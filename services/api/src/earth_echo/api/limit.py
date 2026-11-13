"""Rechaza cuerpos más grandes que el límite configurado."""

from collections.abc import Awaitable, Callable


class BodyLimitMiddleware:
    def __init__(self, app: Callable, max_bytes: int) -> None:
        self.app = app
        self.max_bytes = max_bytes

    async def __call__(
        self,
        scope: dict,
        receive: Callable[[], Awaitable[dict]],
        send: Callable[[dict], Awaitable[None]],
    ) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        headers = dict(scope.get("headers") or [])
        raw_length = headers.get(b"content-length")
        if raw_length is not None:
            try:
                length = int(raw_length)
            except ValueError:
                await _send_json(send, 400, "invalid_content_length", "Content-Length no es un entero.")
                return
            if length > self.max_bytes:
                await _send_json(
                    send,
                    413,
                    "payload_too_large",
                    "El cuerpo supera el límite configurado.",
                )
                return
        await self.app(scope, receive, send)


async def _send_json(send, status: int, error: str, detail: str) -> None:
    body = f'{{"error":"{error}","detail":"{detail}"}}'.encode("utf-8")
    await send(
        {
            "type": "http.response.start",
            "status": status,
            "headers": [
                (b"content-type", b"application/json; charset=utf-8"),
                (b"content-length", str(len(body)).encode("ascii")),
            ],
        }
    )
    await send({"type": "http.response.body", "body": body})

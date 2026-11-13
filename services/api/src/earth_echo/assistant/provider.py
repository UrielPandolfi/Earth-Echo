"""Proveedor de texto. La URL sale del entorno, nunca del mensaje."""

import os
from dataclasses import dataclass

import httpx

from earth_echo.settings import Settings


@dataclass(frozen=True)
class ScriptedProvider:
    """Proveedor de prueba. No es una ejecución de Qwen."""

    script: str
    provider_id: str = "mock"
    model_name: str = "scripted-mock"

    def complete(self, question: str, evidence_json: str) -> str:
        del question, evidence_json
        return self.script


@dataclass(frozen=True)
class OpenAICompatibleProvider:
    base_url: str
    model_name: str
    timeout_seconds: float
    max_tokens: int
    provider_id: str = "openai-compatible"

    def complete(self, question: str, evidence_json: str) -> str:
        key = os.environ.get("EARTH_ECHO_LLM_API_KEY", "").strip()
        headers = {"Authorization": f"Bearer {key}"} if key else {}
        response = httpx.post(
            f"{self.base_url.rstrip('/')}/chat/completions",
            headers=headers,
            json={
                "model": self.model_name,
                "max_tokens": self.max_tokens,
                "temperature": 0,
                "messages": [
                    {
                        "role": "system",
                        "content": (
                            "Reescribí en español solo los datos del JSON. "
                            "No agregues números, fechas, probabilidades ni causas. "
                            "Si el JSON dice que no está validado, no lo valides."
                        ),
                    },
                    {"role": "user", "content": evidence_json},
                ],
            },
            timeout=self.timeout_seconds,
        )
        response.raise_for_status()
        body = response.json()
        return str(body["choices"][0]["message"]["content"])


def configured_provider(settings: Settings) -> OpenAICompatibleProvider | None:
    if not settings.llm_base_url or not settings.llm_model:
        return None
    return OpenAICompatibleProvider(
        base_url=settings.llm_base_url,
        model_name=settings.llm_model,
        timeout_seconds=settings.llm_timeout_seconds,
        max_tokens=settings.llm_max_tokens,
    )

"""Punto de entrada de la API."""

import uvicorn

from earth_echo.api.app import create_app
from earth_echo.settings import get_settings

app = create_app()


def main() -> None:
    settings = get_settings()
    uvicorn.run(app, host=settings.host, port=settings.port)


if __name__ == "__main__":
    main()

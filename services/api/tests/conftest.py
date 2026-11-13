import pytest

from earth_echo.settings import get_settings


@pytest.fixture(autouse=True)
def clear_cached_settings(monkeypatch):
    monkeypatch.setenv('EARTH_ECHO_REFRESH_ENABLED', '0')
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()

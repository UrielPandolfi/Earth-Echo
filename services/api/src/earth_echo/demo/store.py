"""Lee la señal sintética de F11. No la devuelve en modo real."""

import json

from earth_echo.contracts.records import SignalRecord
from earth_echo.paths import repo_root


def load_demo_signal() -> SignalRecord:
    path = repo_root() / "data" / "demo" / "f11_signal.json"
    signal = SignalRecord.model_validate(json.loads(path.read_text(encoding="utf-8")))
    if signal.data_mode != "demo" or signal.phenomenon_id != "F11":
        raise ValueError("El fixture de demostración debe ser F11 con data_mode demo.")
    if signal.probability.state != "absent":
        raise ValueError("El fixture de demostración no puede declarar una probabilidad.")
    return signal

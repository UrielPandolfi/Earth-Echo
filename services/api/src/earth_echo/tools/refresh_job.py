"""One concrete registered source job. Parent owns locking, deadlines and state."""
import json
import sys
from datetime import datetime
from earth_echo.settings import get_settings
from earth_echo.ops.refresh import jobs


def main():
    try:
        get_settings()
        name, stamp = sys.argv[1:]
        moment = datetime.fromisoformat(stamp)
        if moment.utcoffset() is None:
            raise ValueError('Job attempt requires UTC offset')
        result = jobs()[name][1](moment)
        print(json.dumps({'status': result}))
    except Exception as error:
        print(json.dumps({'error': f'{type(error).__name__}: {error}'}))
        raise SystemExit(1)


if __name__ == '__main__':
    main()

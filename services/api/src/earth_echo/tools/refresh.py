import argparse
import asyncio
import json
from earth_echo.settings import get_settings
from earth_echo.ops.refresh import run_due, watch

def main():
    get_settings()
    parser = argparse.ArgumentParser()
    parser.add_argument('--watch', action='store_true')
    parser.add_argument('--force', action='store_true')
    parser.add_argument('--only', nargs='+')
    args = parser.parse_args()
    if args.watch:
        asyncio.run(watch(asyncio.Event()))
    else:
        print(json.dumps(run_due(force=args.force, only=set(args.only) if args.only else None), indent=2))

if __name__ == '__main__':
    main()

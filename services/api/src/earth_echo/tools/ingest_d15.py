"""Ingesta el subconjunto archivado de CoralTemp, o lo vuelve a pedir con --live."""

import argparse
from pathlib import Path

from earth_echo.connectors.crw_sst import fetch_subset
from earth_echo.ingest.d15_sst import default_store, ingest_file, sample_file


def main() -> None:
    parser = argparse.ArgumentParser(description="Ingestión idempotente de SST CoralTemp v3.1")
    parser.add_argument("--live", action="store_true", help="Vuelve a pedir el recorte a ERDDAP")
    parser.add_argument("--source", type=Path, default=None, help="NetCDF local en lugar del archivo archivado")
    args = parser.parse_args()
    source = args.source or sample_file()
    if args.live:
        source.parent.mkdir(parents=True, exist_ok=True)
        fetch_subset(source)
    result = ingest_file(source, default_store())
    print(f"{result['status']} revision={result['revision']} observations={result['observations']}")


if __name__ == "__main__":
    main()

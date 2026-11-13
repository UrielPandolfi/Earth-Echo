"""Descarga y agrega la historia mensual del recorte de CoralTemp."""

import argparse

from earth_echo.ingest.d15_history import download_history, write_monthly_series


def main() -> None:
    parser = argparse.ArgumentParser(description="Historia mensual de SST CoralTemp v3.1")
    parser.add_argument("--download", action="store_true", help="Pide cada año a ERDDAP")
    args = parser.parse_args()
    if args.download:
        download_history()
    path = write_monthly_series()
    print(path)


if __name__ == "__main__":
    main()

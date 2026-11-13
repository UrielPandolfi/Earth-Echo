"""Actualiza sismos y Kp si la cadencia lo pide."""

import argparse

from earth_echo.ingest.feeds import run_due, seed_archived_feeds


def main() -> None:
    parser = argparse.ArgumentParser(description="Feeds públicos D21 y D28")
    parser.add_argument("--live", action="store_true", help="Consulta USGS y SWPC si la tarea está vencida")
    parser.add_argument("--seed", action="store_true", help="Carga las muestras archivadas")
    args = parser.parse_args()
    if args.seed:
        seed_archived_feeds()
        print("muestras archivadas")
    if args.live:
        for item in run_due(force=True):
            print(f"{item['job']} {item['status']} {item['error_class']}")


if __name__ == "__main__":
    main()

"""Índice local del subconjunto real. No es PostGIS."""

import json
import sqlite3
from pathlib import Path

from earth_echo.contracts.records import AssetRecord, ObservationRecord


class SstStore:
    def __init__(self, root: Path) -> None:
        self.root = root
        self.assets = root / "assets"
        self.database = root / "index.sqlite"

    def connect(self) -> sqlite3.Connection:
        self.root.mkdir(parents=True, exist_ok=True)
        self.assets.mkdir(parents=True, exist_ok=True)
        connection = sqlite3.connect(self.database)
        connection.row_factory = sqlite3.Row
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS assets (
                id TEXT PRIMARY KEY,
                logical_key TEXT NOT NULL,
                revision INTEGER NOT NULL,
                checksum TEXT NOT NULL,
                byte_size INTEGER NOT NULL,
                relative_path TEXT NOT NULL,
                payload_json TEXT NOT NULL,
                superseded INTEGER NOT NULL DEFAULT 0,
                UNIQUE(logical_key, revision)
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS observations (
                id TEXT PRIMARY KEY,
                logical_key TEXT NOT NULL UNIQUE,
                asset_id TEXT NOT NULL,
                observed_start TEXT NOT NULL,
                payload_json TEXT NOT NULL
            )
            """
        )
        return connection

    def latest_asset(self, logical_key: str) -> sqlite3.Row | None:
        with self.connect() as connection:
            return connection.execute(
                """
                SELECT * FROM assets
                WHERE logical_key = ? AND superseded = 0
                ORDER BY revision DESC
                LIMIT 1
                """,
                (logical_key,),
            ).fetchone()

    def add_revision(
        self,
        *,
        asset: AssetRecord,
        logical_key: str,
        revision: int,
        relative_path: str,
        observations: list[tuple[str, str, ObservationRecord]],
    ) -> None:
        payload = asset.model_dump_json()
        with self.connect() as connection:
            connection.execute(
                "UPDATE assets SET superseded = 1 WHERE logical_key = ? AND superseded = 0",
                (logical_key,),
            )
            connection.execute(
                """
                INSERT INTO assets (
                    id, logical_key, revision, checksum, byte_size, relative_path, payload_json, superseded
                ) VALUES (?, ?, ?, ?, ?, ?, ?, 0)
                """,
                (
                    asset.id,
                    logical_key,
                    revision,
                    asset.checksum_sha256,
                    asset.byte_size,
                    relative_path,
                    payload,
                ),
            )
            for logical_observation, observed_start, record in observations:
                connection.execute(
                    """
                    INSERT INTO observations (id, logical_key, asset_id, observed_start, payload_json)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (
                        record.id,
                        logical_observation,
                        asset.id,
                        observed_start,
                        record.model_dump_json(),
                    ),
                )

    def current_observations(self) -> list[ObservationRecord]:
        with self.connect() as connection:
            rows = connection.execute(
                """
                SELECT observations.payload_json
                FROM observations
                JOIN assets ON assets.id = observations.asset_id
                WHERE assets.superseded = 0
                ORDER BY observations.observed_start
                """
            ).fetchall()
        return [ObservationRecord.model_validate(json.loads(row["payload_json"])) for row in rows]

    def observation(self, observation_id: str) -> ObservationRecord | None:
        with self.connect() as connection:
            row = connection.execute(
                """
                SELECT observations.payload_json
                FROM observations
                JOIN assets ON assets.id = observations.asset_id
                WHERE observations.id = ? AND assets.superseded = 0
                """,
                (observation_id,),
            ).fetchone()
        if row is None:
            return None
        return ObservationRecord.model_validate(json.loads(row["payload_json"]))

    def asset(self, asset_id: str) -> AssetRecord | None:
        with self.connect() as connection:
            row = connection.execute("SELECT payload_json FROM assets WHERE id = ?", (asset_id,)).fetchone()
        if row is None:
            return None
        return AssetRecord.model_validate(json.loads(row["payload_json"]))

    def asset_path(self, asset_id: str) -> Path | None:
        with self.connect() as connection:
            row = connection.execute(
                "SELECT relative_path FROM assets WHERE id = ? AND superseded = 0",
                (asset_id,),
            ).fetchone()
        if row is None:
            return None
        return self.root / str(row["relative_path"])

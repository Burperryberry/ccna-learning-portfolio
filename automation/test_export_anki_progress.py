#!/usr/bin/env python3

from __future__ import annotations

import datetime as dt
import importlib.util
import sqlite3
import tempfile
import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).with_name("export_anki_progress.py")
SPEC = importlib.util.spec_from_file_location("export_anki_progress", MODULE_PATH)
assert SPEC and SPEC.loader
EXPORTER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(EXPORTER)


class ExportAnkiProgressTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)
        self.collection = Path(self.temp_dir.name) / "collection.anki2"
        self.now = dt.datetime(2026, 7, 18, 20, 0, tzinfo=dt.timezone.utc)
        connection = sqlite3.connect(self.collection)
        connection.executescript(
            """
            CREATE TABLE col (crt INTEGER NOT NULL);
            CREATE TABLE decks (id INTEGER PRIMARY KEY, name TEXT NOT NULL);
            CREATE TABLE cards (
                id INTEGER PRIMARY KEY, nid INTEGER NOT NULL, did INTEGER NOT NULL,
                ord INTEGER NOT NULL, mod INTEGER NOT NULL, usn INTEGER NOT NULL,
                type INTEGER NOT NULL, queue INTEGER NOT NULL, due INTEGER NOT NULL,
                ivl INTEGER NOT NULL, factor INTEGER NOT NULL, reps INTEGER NOT NULL,
                lapses INTEGER NOT NULL, left INTEGER NOT NULL, odue INTEGER NOT NULL,
                odid INTEGER NOT NULL, flags INTEGER NOT NULL, data TEXT NOT NULL
            );
            CREATE TABLE revlog (
                id INTEGER PRIMARY KEY, cid INTEGER NOT NULL, usn INTEGER NOT NULL,
                ease INTEGER NOT NULL, ivl INTEGER NOT NULL,
                lastIvl INTEGER NOT NULL, factor INTEGER NOT NULL,
                time INTEGER NOT NULL, type INTEGER NOT NULL
            );
            CREATE TABLE notes (id INTEGER PRIMARY KEY, flds TEXT NOT NULL);
            """
        )
        created = int((self.now - dt.timedelta(days=200)).timestamp())
        connection.execute("INSERT INTO col VALUES (?)", (created,))
        connection.executemany(
            "INSERT INTO decks VALUES (?, ?)",
            [(1, "Default"), (10, "CCNA"), (11, "CCNA\x1fRouting")],
        )
        card_rows = [
            (1, 1, 10, 0, 0, 0, 0, 0, 1, 0, 2500, 0, 0, 0, 0, 0, 0, ""),
            (2, 2, 11, 0, 0, 0, 2, 2, 199, 30, 2500, 10, 1, 0, 0, 0, 0, ""),
            (
                3,
                3,
                11,
                0,
                0,
                0,
                1,
                1,
                int(self.now.timestamp()) - 10,
                0,
                2500,
                1,
                0,
                0,
                0,
                0,
                0,
                "",
            ),
            (4, 4, 11, 0, 0, 0, 2, -1, 100, 40, 2500, 10, 0, 0, 0, 0, 0, ""),
            (5, 5, 1, 0, 0, 0, 2, 2, 1, 50, 2500, 10, 0, 0, 0, 0, 0, ""),
        ]
        connection.executemany(
            "INSERT INTO cards VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", card_rows
        )
        now_ms = int(self.now.timestamp() * 1000)
        connection.executemany(
            "INSERT INTO revlog VALUES (?,?,?,?,?,?,?,?,?)",
            [
                (now_ms - 3_600_000, 2, 0, 3, 30, 22, 2500, 45_000, 1),
                (now_ms - 90_000_000, 2, 0, 1, 22, 10, 2500, 30_000, 1),
                (now_ms - 3_599_999, 5, 0, 3, 50, 40, 2500, 20_000, 1),
            ],
        )
        connection.execute(
            "INSERT INTO notes VALUES (?, ?)", (1, "PRIVATE-CARD-CONTENT")
        )
        connection.commit()
        connection.close()

    def test_exports_aggregate_non_default_deck_metrics_only(self) -> None:
        with EXPORTER.collection_snapshot(self.collection) as connection:
            decks, counts, reviews = EXPORTER.load_dashboard_data(
                connection, self.now
            )
        self.assertEqual(decks, ["CCNA", "CCNA::Routing"])
        self.assertEqual(
            counts,
            {
                "total": 4,
                "due": 2,
                "new": 1,
                "learning": 1,
                "mature": 1,
                "suspended": 1,
            },
        )
        self.assertEqual(len(reviews), 2)
        dashboard = EXPORTER.render_dashboard(decks, counts, reviews, self.now)
        self.assertIn("aggregate study statistics only", dashboard)
        self.assertIn("CCNA::Routing", dashboard)
        self.assertNotIn("PRIVATE-CARD-CONTENT", dashboard)

    def test_atomic_write_is_idempotent(self) -> None:
        output = Path(self.temp_dir.name) / "progress.md"
        self.assertTrue(EXPORTER.atomic_write_if_changed(output, "dashboard\n"))
        self.assertFalse(EXPORTER.atomic_write_if_changed(output, "dashboard\n"))
        self.assertEqual(output.read_text(encoding="utf-8"), "dashboard\n")


if __name__ == "__main__":
    unittest.main()

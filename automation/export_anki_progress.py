#!/usr/bin/env python3
"""Export aggregate Anki study progress without publishing card contents."""

from __future__ import annotations

import argparse
import datetime as dt
import os
import shutil
import sqlite3
import tempfile
import time
from collections import defaultdict
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator, Sequence


DEFAULT_COLLECTION = (
    Path.home() / "Library" / "Application Support" / "Anki2" / "User 1" / "collection.anki2"
)
DEFAULT_HISTORY_DAYS = 365
OUTPUT_PATHS = (
    Path("progress") / "anki.md",
    Path("flashcard-progress") / "Anki Progress Dashboard.md",
)


def _source_signature(collection: Path) -> tuple[tuple[str, int, int], ...]:
    signature: list[tuple[str, int, int]] = []
    for suffix in ("", "-wal", "-shm"):
        path = Path(f"{collection}{suffix}")
        if path.exists():
            stat = path.stat()
            signature.append((suffix, stat.st_size, stat.st_mtime_ns))
    return tuple(signature)


@contextmanager
def collection_snapshot(
    collection: Path, attempts: int = 5
) -> Iterator[sqlite3.Connection]:
    """Copy a stable SQLite/WAL snapshot so the live Anki database stays untouched."""

    collection = collection.expanduser().resolve()
    if not collection.is_file():
        raise FileNotFoundError(f"Anki collection not found: {collection}")

    last_error: Exception | None = None
    for attempt in range(attempts):
        with tempfile.TemporaryDirectory(prefix="ccna-anki-snapshot-") as temp_dir:
            snapshot = Path(temp_dir) / "collection.anki2"
            before = _source_signature(collection)
            try:
                shutil.copy2(collection, snapshot)
                for suffix in ("-wal", "-shm"):
                    source = Path(f"{collection}{suffix}")
                    if source.exists():
                        shutil.copy2(source, Path(f"{snapshot}{suffix}"))
                after = _source_signature(collection)
                if before != after:
                    raise RuntimeError("Anki changed while its snapshot was being copied")

                connection = sqlite3.connect(snapshot)
                connection.create_collation(
                    "unicase",
                    lambda left, right: (left.casefold() > right.casefold())
                    - (left.casefold() < right.casefold()),
                )
                connection.execute("PRAGMA query_only = ON")
                result = connection.execute("PRAGMA quick_check").fetchone()
                if not result or result[0] != "ok":
                    connection.close()
                    raise RuntimeError("The Anki snapshot did not pass SQLite quick_check")
                try:
                    yield connection
                finally:
                    connection.close()
                return
            except (OSError, sqlite3.Error, RuntimeError) as exc:
                last_error = exc
                if attempt + 1 < attempts:
                    time.sleep(0.2 * (attempt + 1))

    raise RuntimeError(f"Could not create a stable Anki snapshot: {last_error}")


def normalize_deck_name(name: str) -> str:
    return name.replace("\x1f", "::")


def local_date(timestamp_ms: int) -> dt.date:
    return dt.datetime.fromtimestamp(timestamp_ms / 1000).astimezone().date()


def percent(numerator: int, denominator: int) -> str:
    if denominator == 0:
        return "—"
    return f"{(numerator / denominator) * 100:.1f}%"


def duration_minutes(milliseconds: int) -> str:
    minutes = milliseconds / 60000
    if minutes < 1 and milliseconds > 0:
        return "<1 min"
    return f"{minutes:.0f} min"


def stats_for(rows: Sequence[dict[str, int | str]]) -> dict[str, int]:
    again = sum(1 for row in rows if row["ease"] == 1)
    hard = sum(1 for row in rows if row["ease"] == 2)
    good = sum(1 for row in rows if row["ease"] == 3)
    easy = sum(1 for row in rows if row["ease"] == 4)
    total_time = sum(int(row["time_ms"]) for row in rows)
    return {
        "reviews": len(rows),
        "again": again,
        "hard": hard,
        "good": good,
        "easy": easy,
        "successful": len(rows) - again,
        "time_ms": total_time,
    }


def streak_days(rows: Sequence[dict[str, int | str]], today: dt.date) -> int:
    active_days = {local_date(int(row["id"])) for row in rows}
    cursor = today
    if cursor not in active_days and cursor - dt.timedelta(days=1) in active_days:
        cursor -= dt.timedelta(days=1)
    streak = 0
    while cursor in active_days:
        streak += 1
        cursor -= dt.timedelta(days=1)
    return streak


def load_dashboard_data(
    connection: sqlite3.Connection,
    now: dt.datetime,
    history_days: int = DEFAULT_HISTORY_DAYS,
) -> tuple[list[str], dict[str, int], list[dict[str, int | str]]]:
    deck_rows = connection.execute(
        "SELECT id, name FROM decks WHERE name <> 'Default' COLLATE BINARY "
        "ORDER BY name COLLATE BINARY"
    ).fetchall()
    if not deck_rows:
        raise RuntimeError("No non-default Anki decks were found")

    deck_ids = [int(row[0]) for row in deck_rows]
    decks = [normalize_deck_name(str(row[1])) for row in deck_rows]
    placeholders = ",".join("?" for _ in deck_ids)

    collection_created = int(connection.execute("SELECT crt FROM col").fetchone()[0])
    scheduler_day = max(0, int((now.timestamp() - collection_created) // 86400))
    now_seconds = int(now.timestamp())
    count_row = connection.execute(
        f"""
        SELECT
            COUNT(*),
            SUM(CASE WHEN
                (queue IN (1, 3) AND due <= ?)
                OR (queue = 2 AND due <= ?)
                THEN 1 ELSE 0 END),
            SUM(CASE WHEN queue = 0 THEN 1 ELSE 0 END),
            SUM(CASE WHEN queue IN (1, 3) THEN 1 ELSE 0 END),
            SUM(CASE WHEN ivl >= 21 AND queue <> -1 THEN 1 ELSE 0 END),
            SUM(CASE WHEN queue = -1 THEN 1 ELSE 0 END)
        FROM cards
        WHERE did IN ({placeholders})
        """,
        [now_seconds, scheduler_day, *deck_ids],
    ).fetchone()
    if count_row is None:
        raise RuntimeError("Anki card counts could not be read")
    counts = {
        "total": int(count_row[0] or 0),
        "due": int(count_row[1] or 0),
        "new": int(count_row[2] or 0),
        "learning": int(count_row[3] or 0),
        "mature": int(count_row[4] or 0),
        "suspended": int(count_row[5] or 0),
    }

    since = now - dt.timedelta(days=max(30, history_days) + 2)
    rows = connection.execute(
        f"""
        SELECT r.id, r.ease, r.ivl, r.lastIvl, r.time, r.type, d.name
        FROM revlog AS r
        JOIN cards AS c ON c.id = r.cid
        JOIN decks AS d ON d.id = c.did
        WHERE c.did IN ({placeholders}) AND r.id >= ?
        ORDER BY r.id
        """,
        [*deck_ids, int(since.timestamp() * 1000)],
    ).fetchall()
    reviews = [
        {
            "id": int(row[0]),
            "ease": int(row[1]),
            "interval": int(row[2]),
            "last_interval": int(row[3]),
            "time_ms": max(0, int(row[4])),
            "review_type": int(row[5]),
            "deck": normalize_deck_name(str(row[6])),
        }
        for row in rows
    ]
    return decks, counts, reviews


def render_dashboard(
    decks: list[str],
    counts: dict[str, int],
    reviews: list[dict[str, int | str]],
    now: dt.datetime,
) -> str:
    today = now.astimezone().date()
    cutoff_7 = today - dt.timedelta(days=6)
    cutoff_30 = today - dt.timedelta(days=29)
    rows_today = [row for row in reviews if local_date(int(row["id"])) == today]
    rows_7 = [row for row in reviews if local_date(int(row["id"])) >= cutoff_7]
    rows_30 = [row for row in reviews if local_date(int(row["id"])) >= cutoff_30]
    today_stats = stats_for(rows_today)
    week_stats = stats_for(rows_7)
    month_stats = stats_for(rows_30)

    daily: dict[dt.date, list[dict[str, int | str]]] = defaultdict(list)
    for row in rows_30:
        daily[local_date(int(row["id"]))].append(row)
    max_daily = max((len(items) for items in daily.values()), default=1)
    activity_rows: list[str] = []
    for offset in range(13, -1, -1):
        day = today - dt.timedelta(days=offset)
        day_stats = stats_for(daily.get(day, []))
        blocks = round((day_stats["reviews"] / max_daily) * 10) if max_daily else 0
        bar = "█" * blocks + "░" * (10 - blocks)
        activity_rows.append(
            f"| {day.isoformat()} | {day_stats['reviews']} | "
            f"{duration_minutes(day_stats['time_ms']) if day_stats['reviews'] else '—'} | "
            f"{percent(day_stats['successful'], day_stats['reviews'])} | `{bar}` |"
        )

    by_deck: dict[str, list[dict[str, int | str]]] = defaultdict(list)
    for row in rows_30:
        by_deck[str(row["deck"])].append(row)
    ranked: list[tuple[float, str, dict[str, int]]] = []
    for deck, deck_reviews in by_deck.items():
        deck_stats = stats_for(deck_reviews)
        if deck_stats["reviews"] >= 3:
            ranked.append((deck_stats["again"] / deck_stats["reviews"], deck, deck_stats))
    deck_rows: list[str] = []
    for _, deck, deck_stats in sorted(ranked, reverse=True):
        label = deck.replace("|", "\\|")
        deck_rows.append(
            f"| {label} | {deck_stats['reviews']} | {deck_stats['again']} | "
            f"{percent(deck_stats['successful'], deck_stats['reviews'])} |"
        )
    if not deck_rows:
        deck_rows.append("| _Not enough recent reviews yet_ | — | — | — |")

    mature_rows = [row for row in rows_30 if int(row["last_interval"]) >= 21]
    mature_stats = stats_for(mature_rows)
    tracked = ", ".join(f"`{name}`" for name in decks)
    streak = streak_days(reviews, today)

    return f"""---
tags:
  - ccna
  - anki
  - flashcards
  - progress
cssclasses:
  - anki-progress-dashboard
---

# Anki CCNA Progress

> [!info] Nightly snapshot
> **{today.isoformat()}** · Tracking {tracked}

> [!note] Privacy
> This page contains aggregate study statistics only. Card questions, answers, note fields, and raw review history are never exported.

## Current workload

| Due now | New | Learning | Mature | Suspended | Total cards |
|---:|---:|---:|---:|---:|---:|
| **{counts['due']}** | **{counts['new']}** | **{counts['learning']}** | **{counts['mature']}** | **{counts['suspended']}** | **{counts['total']}** |

## Today

| Reviews | Study time | Again | Hard | Good | Easy | Success rate |
|---:|---:|---:|---:|---:|---:|---:|
| **{today_stats['reviews']}** | **{duration_minutes(today_stats['time_ms'])}** | {today_stats['again']} | {today_stats['hard']} | {today_stats['good']} | {today_stats['easy']} | **{percent(today_stats['successful'], today_stats['reviews'])}** |

## Momentum

| Metric | Last 7 days | Last 30 days |
|---|---:|---:|
| Reviews | **{week_stats['reviews']}** | **{month_stats['reviews']}** |
| Study time | **{duration_minutes(week_stats['time_ms'])}** | **{duration_minutes(month_stats['time_ms'])}** |
| Success rate | **{percent(week_stats['successful'], week_stats['reviews'])}** | **{percent(month_stats['successful'], month_stats['reviews'])}** |
| Again presses | {week_stats['again']} | {month_stats['again']} |

> [!success] Current streak
> **{streak} day{'s' if streak != 1 else ''}** with at least one review. A streak remains active through the end of the following day.

> [!note] Mature-card retention
> Over the last 30 days, mature cards had an answer-button success rate of **{percent(mature_stats['successful'], mature_stats['reviews'])}** across **{mature_stats['reviews']}** reviews. Here, mature means the card's prior interval was at least 21 days.

## 14-day activity

| Date | Reviews | Time | Success | Activity |
|---|---:|---:|---:|---|
{chr(10).join(activity_rows)}

## Topics to revisit

Subdecks are ordered by highest **Again** rate over the last 30 days. Rows need at least three reviews.

| Deck / topic | Reviews | Again | Success rate |
|---|---:|---:|---:|
{chr(10).join(deck_rows)}

## How to use this dashboard

- Prioritize the subdecks near the top of **Topics to revisit**.
- A success rate is the percentage of review events answered **Hard**, **Good**, or **Easy** instead of **Again**.
- The GitHub snapshot refreshes nightly at 8:00 PM local time.
"""


def atomic_write_if_changed(path: Path, content: str) -> bool:
    if path.exists() and path.read_text(encoding="utf-8") == content:
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temp_name = tempfile.mkstemp(
        prefix=f".{path.name}.", suffix=".tmp", dir=path.parent
    )
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            handle.write(content)
        os.replace(temp_name, path)
    except Exception:
        try:
            os.unlink(temp_name)
        except OSError:
            pass
        raise
    return True


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--collection", type=Path, default=DEFAULT_COLLECTION)
    parser.add_argument(
        "--repo", type=Path, default=Path(__file__).resolve().parents[1]
    )
    parser.add_argument("--history-days", type=int, default=DEFAULT_HISTORY_DAYS)
    args = parser.parse_args()

    now = dt.datetime.now().astimezone()
    try:
        with collection_snapshot(args.collection) as connection:
            decks, counts, reviews = load_dashboard_data(
                connection, now, max(30, args.history_days)
            )
        content = render_dashboard(decks, counts, reviews, now)
        changed = []
        for relative_path in OUTPUT_PATHS:
            destination = args.repo.expanduser().resolve() / relative_path
            if atomic_write_if_changed(destination, content):
                changed.append(str(relative_path))
        if changed:
            print(f"Updated {', '.join(changed)}")
        else:
            print("No Anki dashboard changes found.")
        return 0
    except (OSError, RuntimeError, sqlite3.Error, ValueError) as exc:
        print(f"Anki export failed: {exc}", file=os.sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

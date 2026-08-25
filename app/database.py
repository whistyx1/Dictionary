from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

from .models import Word

class DuplicateWordError(ValueError):
    pass


class WordRepository:
    def __init__(self, db_path: Path):
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._create_schema()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.db_path, timeout=5)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        return connection

    @contextmanager
    def _session(self) -> Iterator[sqlite3.Connection]:
        connection = self._connect()
        try:
            with connection:
                yield connection
        finally:
            connection.close()

    def _create_schema(self) -> None:
        with self._session() as db:
            db.execute("""
                CREATE TABLE IF NOT EXISTS words (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    word TEXT NOT NULL COLLATE NOCASE UNIQUE,
                    translation TEXT NOT NULL,
                    level TEXT NOT NULL CHECK(level IN ('easy', 'medium', 'hard')),
                    learned INTEGER NOT NULL DEFAULT 0 CHECK(learned IN (0, 1)),
                    category TEXT NOT NULL DEFAULT 'other',
                    image_url TEXT NOT NULL DEFAULT '',
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
            """)

    def add(self, word: Word) -> int:
        try:
            with self._session() as db:
                cursor = db.execute(
                    """INSERT INTO words
                       (word, translation, level, learned, category, image_url)
                       VALUES (?, ?, ?, ?, ?, ?)""",
                    (word.word, word.translation, word.level, int(word.learned),
                     word.category, word.image_url),
                )
                return int(cursor.lastrowid)
        except sqlite3.IntegrityError as error:
            if "UNIQUE" in str(error).upper():
                raise DuplicateWordError(word.word) from error
            raise

    def all(self) -> list[Word]:
        with self._session() as db:
            rows = db.execute("SELECT * FROM words ORDER BY id").fetchall()
        return [self._from_row(row) for row in rows]

    def delete(self, word_id: int) -> None:
        with self._session() as db:
            db.execute("DELETE FROM words WHERE id = ?", (word_id,))

    def mark_learned(self, word_id: int) -> None:
        with self._session() as db:
            db.execute("UPDATE words SET learned = 1 WHERE id = ?", (word_id,))

    def update_image(self, word_id: int, image_url: str) -> None:
        with self._session() as db:
            db.execute("UPDATE words SET image_url = ? WHERE id = ?", (image_url, word_id))

    def stats(self) -> tuple[int, int]:
        with self._session() as db:
            row = db.execute(
                "SELECT COUNT(*) AS total, COALESCE(SUM(learned), 0) AS learned FROM words"
            ).fetchone()
        return int(row["total"]), int(row["learned"])

    @staticmethod
    def _from_row(row: sqlite3.Row) -> Word:
        return Word(row["word"], row["translation"], row["level"],
                    bool(row["learned"]), row["category"], row["image_url"], row["id"])

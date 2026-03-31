import sqlite3
import pytest
from db import init_db


def test_init_db_creates_tables(tmp_path):
    db_path = str(tmp_path / "test.db")
    conn = init_db(db_path)
    cursor = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name"
    )
    tables = {row[0] for row in cursor.fetchall()}
    assert tables == {"books", "characters", "roles", "sentences", "tokens"}
    conn.close()

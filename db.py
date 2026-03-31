import sqlite3
import json
import os

DB_PATH = "dataset.db"
JSON_PATH = "dataset.json"


def init_db(db_path: str = DB_PATH) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS books (
            id          INTEGER PRIMARY KEY,
            title       TEXT NOT NULL,
            author      TEXT NOT NULL,
            year        INTEGER,
            n_sentences INTEGER NOT NULL,
            n_tokens    INTEGER NOT NULL
        );
        CREATE TABLE IF NOT EXISTS characters (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            book_id     INTEGER NOT NULL REFERENCES books(id),
            name        TEXT NOT NULL,
            occurrences INTEGER NOT NULL
        );
        CREATE TABLE IF NOT EXISTS roles (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            character_id INTEGER NOT NULL REFERENCES characters(id),
            role         TEXT NOT NULL,
            count        INTEGER NOT NULL
        );
        CREATE TABLE IF NOT EXISTS sentences (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            book_id     INTEGER NOT NULL REFERENCES books(id),
            sentence_id INTEGER NOT NULL
        );
        CREATE TABLE IF NOT EXISTS tokens (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            sentence_id INTEGER NOT NULL REFERENCES sentences(id),
            form        TEXT,
            lemma       TEXT,
            upos        TEXT,
            xpos        TEXT,
            feats       TEXT,
            head        INTEGER,
            deprel      TEXT,
            start_char  INTEGER,
            end_char    INTEGER,
            character   TEXT
        );
        CREATE INDEX IF NOT EXISTS idx_tokens_character   ON tokens(character);
        CREATE INDEX IF NOT EXISTS idx_tokens_sentence_id ON tokens(sentence_id);
        CREATE INDEX IF NOT EXISTS idx_sentences_book_id  ON sentences(book_id);
        CREATE INDEX IF NOT EXISTS idx_characters_book_id ON characters(book_id);
    """)
    conn.commit()
    return conn

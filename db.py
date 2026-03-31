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


def import_json(conn: sqlite3.Connection, json_path: str = JSON_PATH) -> None:
    with open(json_path, encoding="utf-8") as f:
        data = json.load(f)

    for book in data["libri"]:
        conn.execute(
            "INSERT OR REPLACE INTO books (id, title, author, year, n_sentences, n_tokens) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (book["id_libro"], book["titolo_libro"], book["autore"],
             book["anno"], book["n_frasi"], book["n_token"])
        )
        book_id = book["id_libro"]

        for char in book.get("personaggi", []):
            cur = conn.execute(
                "INSERT INTO characters (book_id, name, occurrences) VALUES (?, ?, ?)",
                (book_id, char["nome"], char["occorrenze"])
            )
            char_id = cur.lastrowid
            for role, count in char.get("ruoli", {}).items():
                conn.execute(
                    "INSERT INTO roles (character_id, role, count) VALUES (?, ?, ?)",
                    (char_id, role, count)
                )

        for sentence in book.get("frasi", []):
            cur = conn.execute(
                "INSERT INTO sentences (book_id, sentence_id) VALUES (?, ?)",
                (book_id, sentence["id_frase"])
            )
            sent_row_id = cur.lastrowid
            for tok in sentence.get("token", []):
                conn.execute(
                    "INSERT INTO tokens "
                    "(sentence_id, form, lemma, upos, xpos, feats, head, deprel, "
                    "start_char, end_char, character) "
                    "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    (sent_row_id, tok["form"], tok["lemma"], tok["upos"],
                     tok["xpos"], tok.get("feats", ""), tok["head"],
                     tok["deprel"], tok.get("start_char"), tok.get("end_char"),
                     tok.get("personaggio"))
                )

    conn.commit()

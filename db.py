import sqlite3
import json
import os

DB_PATH = "dataset.db"
JSON_PATH = "dataset.json"


def init_db(db_path: str = DB_PATH) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path, check_same_thread=False)
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


def get_all_books(conn: sqlite3.Connection) -> list[sqlite3.Row]:
    return conn.execute("""
        SELECT b.id, b.title, b.author, b.year, b.n_sentences, b.n_tokens,
               COUNT(c.id) AS n_characters
        FROM books b
        LEFT JOIN characters c ON c.book_id = b.id
        GROUP BY b.id
        ORDER BY b.title
    """).fetchall()


def get_book(conn: sqlite3.Connection, book_id: int) -> sqlite3.Row | None:
    return conn.execute(
        "SELECT * FROM books WHERE id = ?", (book_id,)
    ).fetchone()


def get_characters(conn: sqlite3.Connection, book_id: int) -> list[sqlite3.Row]:
    return conn.execute("""
        SELECT c.id, c.name, c.occurrences,
               (SELECT r.role FROM roles r
                WHERE r.character_id = c.id
                ORDER BY r.count DESC
                LIMIT 1) AS top_role
        FROM characters c
        WHERE c.book_id = ?
        ORDER BY c.occurrences DESC
    """, (book_id,)).fetchall()


def get_sentences_for_character(
    conn: sqlite3.Connection,
    book_id: int,
    name: str,
    role: str | None,
    page: int,
    per_page: int,
) -> dict:
    """Ritorna frasi in cui appare il personaggio `name` nel libro `book_id`.
    Ogni frase include la lista completa dei token."""
    base = """
        FROM sentences s
        JOIN tokens t ON t.sentence_id = s.id
        WHERE s.book_id = ?
          AND t.character = ?
    """
    params: list = [book_id, name]
    if role:
        base += " AND t.deprel = ?"
        params.append(role)

    total = conn.execute("SELECT COUNT(DISTINCT s.id) " + base, params).fetchone()[0]

    offset = (page - 1) * per_page
    sent_rows = conn.execute(
        "SELECT DISTINCT s.id, s.sentence_id " + base +
        " ORDER BY s.sentence_id LIMIT ? OFFSET ?",
        params + [per_page, offset]
    ).fetchall()

    sentences = []
    for row in sent_rows:
        tokens = conn.execute(
            "SELECT form, deprel, character FROM tokens WHERE sentence_id = ? ORDER BY rowid",
            (row["id"],)
        ).fetchall()
        sentences.append({
            "sentence_id": row["sentence_id"],
            "tokens": [dict(t) for t in tokens],
        })

    return {"total": total, "sentences": sentences}


def search_character(
    conn: sqlite3.Connection,
    query: str,
    book_id: int | None,
    role: str | None,
    page: int,
    per_page: int,
) -> dict:
    """Cerca frasi in cui appare un personaggio il cui nome contiene `query`."""
    where = "WHERE t.character LIKE ?"
    params: list = [f"%{query}%"]

    if book_id:
        where += " AND s.book_id = ?"
        params.append(book_id)
    if role:
        where += " AND t.deprel = ?"
        params.append(role)

    count_sql = f"""
        SELECT COUNT(DISTINCT s.id)
        FROM sentences s
        JOIN tokens t ON t.sentence_id = s.id
        {where}
    """
    total = conn.execute(count_sql, params).fetchone()[0]

    offset = (page - 1) * per_page
    rows_sql = f"""
        SELECT s.id, s.sentence_id, b.title AS book_title,
               MIN(t.character) AS character_name,
               MIN(t.deprel)    AS role
        FROM sentences s
        JOIN tokens t ON t.sentence_id = s.id
        JOIN books  b ON b.id = s.book_id
        {where}
        GROUP BY s.id
        ORDER BY s.id
        LIMIT ? OFFSET ?
    """
    sent_rows = conn.execute(rows_sql, params + [per_page, offset]).fetchall()

    sentences = []
    for row in sent_rows:
        tokens = conn.execute(
            "SELECT form, deprel, character FROM tokens WHERE sentence_id = ? ORDER BY rowid",
            (row["id"],)
        ).fetchall()
        sentences.append({
            "sentence_id": row["sentence_id"],
            "book_title":  row["book_title"],
            "character_name": row["character_name"],
            "role":        row["role"],
            "tokens":      [dict(t) for t in tokens],
        })

    return {"total": total, "sentences": sentences}


def get_stats_for_book(conn: sqlite3.Connection, book_id: int) -> list[sqlite3.Row]:
    return conn.execute("""
        SELECT name, occurrences
        FROM characters
        WHERE book_id = ?
        ORDER BY occurrences DESC
    """, (book_id,)).fetchall()


def get_all_roles_for_book(conn: sqlite3.Connection, book_id: int) -> list[sqlite3.Row]:
    return conn.execute("""
        SELECT r.role, SUM(r.count) AS total
        FROM roles r
        JOIN characters c ON c.id = r.character_id
        WHERE c.book_id = ?
        GROUP BY r.role
        ORDER BY total DESC
    """, (book_id,)).fetchall()


def get_roles_for_character(conn: sqlite3.Connection, book_id: int, name: str) -> list[sqlite3.Row]:
    return conn.execute("""
        SELECT r.role, r.count
        FROM roles r
        JOIN characters c ON c.id = r.character_id
        WHERE c.book_id = ? AND c.name = ?
        ORDER BY r.count DESC
    """, (book_id, name)).fetchall()

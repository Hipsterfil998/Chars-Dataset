import sqlite3
import pytest
import json
from db import init_db
from db import (
    get_all_books, get_book, get_characters,
    get_sentences_for_character, search_character, get_stats_for_book,
    get_all_roles_for_book
)


SAMPLE_JSON = {
    "libri": [
        {
            "id_libro": 1,
            "titolo_libro": "Test Book",
            "autore": "Test Author",
            "anno": 2000,
            "n_frasi": 2,
            "n_token": 6,
            "personaggi": [
                {
                    "nome": "Alice",
                    "occorrenze": 2,
                    "ruoli": {"nsubj": 2}
                }
            ],
            "frasi": [
                {
                    "id_frase": 1,
                    "token": [
                        {"id_token": 1, "form": "Alice", "lemma": "alice",
                         "upos": "PROPN", "xpos": "NNP", "feats": "",
                         "head": 2, "deprel": "nsubj",
                         "start_char": 0, "end_char": 5, "personaggio": "Alice"},
                        {"id_token": 2, "form": "runs", "lemma": "run",
                         "upos": "VERB", "xpos": "VBZ", "feats": "",
                         "head": 0, "deprel": "root",
                         "start_char": 6, "end_char": 10, "personaggio": None}
                    ]
                },
                {
                    "id_frase": 2,
                    "token": [
                        {"id_token": 1, "form": "She", "lemma": "she",
                         "upos": "PRON", "xpos": "PRP", "feats": "",
                         "head": 2, "deprel": "nsubj",
                         "start_char": 0, "end_char": 3, "personaggio": None},
                        {"id_token": 2, "form": "laughs", "lemma": "laugh",
                         "upos": "VERB", "xpos": "VBZ", "feats": "",
                         "head": 0, "deprel": "root",
                         "start_char": 4, "end_char": 10, "personaggio": None}
                    ]
                }
            ]
        }
    ]
}


def test_init_db_creates_tables(tmp_path):
    db_path = str(tmp_path / "test.db")
    conn = init_db(db_path)
    cursor = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name"
    )
    tables = {row[0] for row in cursor.fetchall()}
    assert tables == {"books", "characters", "roles", "sentences", "tokens"}
    conn.close()


def test_import_json(tmp_path):
    db_path = str(tmp_path / "test.db")
    json_path = str(tmp_path / "data.json")
    with open(json_path, "w") as f:
        json.dump(SAMPLE_JSON, f)

    conn = init_db(db_path)
    from db import import_json
    import_json(conn, json_path)

    assert conn.execute("SELECT COUNT(*) FROM books").fetchone()[0] == 1
    assert conn.execute("SELECT COUNT(*) FROM characters").fetchone()[0] == 1
    assert conn.execute("SELECT COUNT(*) FROM roles").fetchone()[0] == 1
    assert conn.execute("SELECT COUNT(*) FROM sentences").fetchone()[0] == 2
    assert conn.execute("SELECT COUNT(*) FROM tokens").fetchone()[0] == 4
    # Token con personaggio
    row = conn.execute(
        "SELECT character FROM tokens WHERE character IS NOT NULL"
    ).fetchone()
    assert row["character"] == "Alice"
    conn.close()


def test_get_all_books(conn):
    books = get_all_books(conn)
    assert len(books) == 1
    assert books[0]["title"] == "Test Book"
    assert books[0]["n_characters"] == 2


def test_get_book(conn):
    book = get_book(conn, 1)
    assert book["title"] == "Test Book"
    assert book["author"] == "Test Author"


def test_get_book_missing(conn):
    assert get_book(conn, 999) is None


def test_get_characters(conn):
    chars = get_characters(conn, book_id=1)
    assert len(chars) == 2
    assert chars[0]["name"] == "Alice"
    assert chars[0]["occurrences"] == 2
    assert chars[0]["top_role"] == "nsubj"


def test_get_sentences_for_character_no_filter(conn):
    results = get_sentences_for_character(conn, book_id=1, name="Alice", role=None, page=1, per_page=20)
    assert results["total"] == 1
    assert len(results["sentences"]) == 1
    sent = results["sentences"][0]
    assert sent["sentence_id"] == 1
    assert any(t["form"] == "Alice" for t in sent["tokens"])


def test_get_sentences_for_character_role_filter(conn):
    results = get_sentences_for_character(conn, book_id=1, name="Alice", role="nsubj", page=1, per_page=20)
    assert results["total"] == 1

    results_no = get_sentences_for_character(conn, book_id=1, name="Alice", role="obj", page=1, per_page=20)
    assert results_no["total"] == 0


def test_search_character(conn):
    results = search_character(conn, query="ali", book_id=None, role=None, page=1, per_page=20)
    assert results["total"] == 1
    assert results["sentences"][0]["character_name"] == "Alice"


def test_search_character_book_filter(conn):
    results = search_character(conn, query="ali", book_id=1, role=None, page=1, per_page=20)
    assert results["total"] == 1
    results_wrong_book = search_character(conn, query="ali", book_id=99, role=None, page=1, per_page=20)
    assert results_wrong_book["total"] == 0


def test_get_stats_for_book(conn):
    stats = get_stats_for_book(conn, book_id=1)
    assert len(stats) == 2
    assert stats[0]["name"] == "Alice"
    assert stats[0]["occurrences"] == 2


def test_get_all_roles_for_book(conn):
    roles = get_all_roles_for_book(conn, book_id=1)
    role_names = [r["role"] for r in roles]
    assert "nsubj" in role_names
    assert "obj" in role_names


def test_get_roles_for_character(conn):
    from db import get_roles_for_character
    roles = get_roles_for_character(conn, book_id=1, name="Alice")
    assert len(roles) == 1
    assert roles[0]["role"] == "nsubj"
    assert roles[0]["count"] == 2

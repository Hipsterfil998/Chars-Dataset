import sqlite3
import pytest
import json
from db import init_db


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

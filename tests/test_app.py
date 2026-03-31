import json
import pytest
from app import create_app
from db import init_db, import_json


@pytest.fixture
def client(tmp_path):
    db_path = str(tmp_path / "test.db")
    json_path = str(tmp_path / "data.json")
    sample = {
        "libri": [{
            "id_libro": 1,
            "titolo_libro": "Test Book",
            "autore": "Test Author",
            "anno": 2000,
            "n_frasi": 2,
            "n_token": 4,
            "personaggi": [
                {"nome": "Alice", "occorrenze": 2, "ruoli": {"nsubj": 2}},
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
                }
            ]
        }]
    }
    with open(json_path, "w") as f:
        json.dump(sample, f)
    conn = init_db(db_path)
    import_json(conn, json_path)
    app = create_app(conn)
    app.config["TESTING"] = True
    with app.test_client() as c:
        yield c


def test_root_redirects(client):
    r = client.get("/")
    assert r.status_code == 302
    assert "/books" in r.headers["Location"]


def test_books_page(client):
    r = client.get("/books")
    assert r.status_code == 200
    assert b"Test Book" in r.data


def test_book_detail(client):
    r = client.get("/books/1")
    assert r.status_code == 200
    assert b"Alice" in r.data


def test_book_missing(client):
    r = client.get("/books/999")
    assert r.status_code == 404


def test_character_sentences(client):
    r = client.get("/books/1/characters/Alice")
    assert r.status_code == 200
    assert b"Alice" in r.data


def test_search_empty_query(client):
    r = client.get("/search")
    assert r.status_code == 200


def test_search_with_query(client):
    r = client.get("/search?q=Alice")
    assert r.status_code == 200
    assert b"Alice" in r.data


def test_stats_page(client):
    r = client.get("/stats")
    assert r.status_code == 200
    assert b"Test Book" in r.data

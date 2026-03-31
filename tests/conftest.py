import json
import pytest
import sqlite3
from db import init_db, import_json

SAMPLE_JSON = {
    "libri": [
        {
            "id_libro": 1,
            "titolo_libro": "Test Book",
            "autore": "Test Author",
            "anno": 2000,
            "n_frasi": 2,
            "n_token": 4,
            "personaggi": [
                {"nome": "Alice", "occorrenze": 2, "ruoli": {"nsubj": 2}},
                {"nome": "Bob",   "occorrenze": 1, "ruoli": {"obj": 1}}
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
                        {"id_token": 1, "form": "Bob", "lemma": "bob",
                         "upos": "PROPN", "xpos": "NNP", "feats": "",
                         "head": 2, "deprel": "obj",
                         "start_char": 0, "end_char": 3, "personaggio": "Bob"},
                        {"id_token": 2, "form": "speaks", "lemma": "speak",
                         "upos": "VERB", "xpos": "VBZ", "feats": "",
                         "head": 0, "deprel": "root",
                         "start_char": 4, "end_char": 10, "personaggio": None}
                    ]
                }
            ]
        }
    ]
}


@pytest.fixture
def conn(tmp_path):
    db_path = str(tmp_path / "test.db")
    json_path = str(tmp_path / "data.json")
    with open(json_path, "w") as f:
        json.dump(SAMPLE_JSON, f)
    c = init_db(db_path)
    import_json(c, json_path)
    yield c
    c.close()

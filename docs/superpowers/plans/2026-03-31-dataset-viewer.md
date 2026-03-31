# Dataset Viewer Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Web app Flask locale con sidebar, ricerca per personaggio/ruolo e grafici statistici sul dataset letterario.

**Architecture:** Flask server-side rendering con Jinja2; SQLite generato da `dataset.json` al primo avvio tramite `db.py`; vanilla JS + Chart.js via CDN solo per i grafici nella pagina statistiche.

**Tech Stack:** Python 3.10+, Flask, SQLite3 (stdlib), pytest, Chart.js (CDN)

---

## Mappa file

| File | Ruolo |
|---|---|
| `requirements.txt` | Dipendenze: `flask`, `pytest` |
| `db.py` | Crea schema SQLite, importa JSON, espone query helpers |
| `app.py` | Flask app, tutte le route |
| `templates/base.html` | Layout HTML con sidebar fissa |
| `templates/books.html` | Lista tutti i libri |
| `templates/book.html` | Dettaglio libro + tabella personaggi |
| `templates/character.html` | Frasi paginate di un personaggio |
| `templates/search.html` | Form ricerca + risultati paginati |
| `templates/stats.html` | Grafici Chart.js |
| `static/app.js` | Inizializzazione grafici Chart.js |
| `tests/conftest.py` | Fixture pytest: db in-memory + Flask test client |
| `tests/test_db.py` | Unit test query helpers |
| `tests/test_app.py` | Integration test route Flask |

---

## Task 1: requirements.txt e struttura cartelle

**Files:**
- Create: `requirements.txt`
- Create: `tests/__init__.py`
- Create: `static/.gitkeep`

- [ ] **Step 1: Crea requirements.txt**

```
flask
pytest
```

- [ ] **Step 2: Crea tests/__init__.py vuoto e static/.gitkeep**

```bash
mkdir -p tests static templates
touch tests/__init__.py static/.gitkeep
```

- [ ] **Step 3: Verifica installazione**

```bash
pip install -r requirements.txt
python -c "import flask; print(flask.__version__)"
```
Expected: versione Flask stampata senza errori.

- [ ] **Step 4: Commit**

```bash
git add requirements.txt tests/__init__.py static/.gitkeep
git commit -m "chore: add requirements and project structure"
```

---

## Task 2: db.py — schema e init

**Files:**
- Create: `db.py`
- Create: `tests/conftest.py`
- Create: `tests/test_db.py`

Il JSON usa chiavi italiane: `id_libro`, `titolo_libro`, `autore`, `anno`, `n_frasi`, `n_token`, `personaggi`, `frasi`. Ogni frase ha `id_frase` e `token`. Ogni token ha `id_token`, `form`, `lemma`, `upos`, `xpos`, `feats`, `head`, `deprel`, `start_char`, `end_char`, `personaggio` (null o nome stringa).

- [ ] **Step 1: Scrivi il test che verifica la creazione dello schema**

`tests/test_db.py`:
```python
import sqlite3
import pytest
from db import init_db

def test_init_db_creates_tables(tmp_path):
    db_path = str(tmp_path / "test.db")
    conn = init_db(db_path)
    cursor = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
    )
    tables = {row[0] for row in cursor.fetchall()}
    assert tables == {"books", "characters", "roles", "sentences", "tokens"}
    conn.close()
```

- [ ] **Step 2: Esegui il test per verificare che fallisce**

```bash
pytest tests/test_db.py::test_init_db_creates_tables -v
```
Expected: FAIL con `ModuleNotFoundError: No module named 'db'`

- [ ] **Step 3: Implementa init_db in db.py**

```python
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
```

- [ ] **Step 4: Esegui il test per verificare che passa**

```bash
pytest tests/test_db.py::test_init_db_creates_tables -v
```
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add db.py tests/test_db.py
git commit -m "feat: add db schema init"
```

---

## Task 3: db.py — import JSON

**Files:**
- Modify: `db.py`
- Modify: `tests/test_db.py`

- [ ] **Step 1: Aggiungi test per l'import del JSON**

Aggiungi in `tests/test_db.py`:
```python
import json

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
```

- [ ] **Step 2: Esegui il test per verificare che fallisce**

```bash
pytest tests/test_db.py::test_import_json -v
```
Expected: FAIL con `ImportError: cannot import name 'import_json'`

- [ ] **Step 3: Implementa import_json in db.py**

Aggiungi in `db.py` dopo `init_db`:
```python
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
```

- [ ] **Step 4: Esegui il test per verificare che passa**

```bash
pytest tests/test_db.py -v
```
Expected: 2 PASS

- [ ] **Step 5: Commit**

```bash
git add db.py tests/test_db.py
git commit -m "feat: import dataset.json into SQLite"
```

---

## Task 4: db.py — query helpers

**Files:**
- Modify: `db.py`
- Modify: `tests/test_db.py`

- [ ] **Step 1: Aggiungi fixture condivisa in tests/conftest.py**

```python
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
```

- [ ] **Step 2: Aggiungi test per i query helpers**

Aggiungi in `tests/test_db.py`:
```python
from db import (
    get_all_books, get_book, get_characters,
    get_sentences_for_character, search_character, get_stats_for_book,
    get_all_roles_for_book
)


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
    # tokens list
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
```

- [ ] **Step 3: Esegui i test per verificare che falliscono**

```bash
pytest tests/test_db.py -v
```
Expected: FAIL con `ImportError` su tutti i query helpers non ancora definiti.

- [ ] **Step 4: Implementa i query helpers in db.py**

Aggiungi in `db.py` dopo `import_json`:
```python
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
    rows = conn.execute("""
        SELECT c.id, c.name, c.occurrences,
               r.role AS top_role
        FROM characters c
        LEFT JOIN roles r ON r.character_id = c.id
        WHERE c.book_id = ?
        GROUP BY c.id
        HAVING r.count = MAX(r.count)
        ORDER BY c.occurrences DESC
    """, (book_id,)).fetchall()
    return rows


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
    base = """
        FROM sentences s
        JOIN tokens t ON t.sentence_id = s.id
        JOIN books b ON b.id = s.book_id
        WHERE t.character LIKE ?
    """
    params: list = [f"%{query}%"]

    if book_id:
        base += " AND s.book_id = ?"
        params.append(book_id)
    if role:
        base += " AND t.deprel = ?"
        params.append(role)

    total = conn.execute("SELECT COUNT(DISTINCT s.id) " + base, params).fetchone()[0]

    offset = (page - 1) * per_page
    sent_rows = conn.execute(
        "SELECT DISTINCT s.id, s.sentence_id, b.title AS book_title, t.character AS character_name, t.deprel AS role " + base +
        " ORDER BY s.id LIMIT ? OFFSET ?",
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
            "book_title": row["book_title"],
            "character_name": row["character_name"],
            "role": row["role"],
            "tokens": [dict(t) for t in tokens],
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
```

- [ ] **Step 5: Esegui i test per verificare che passano**

```bash
pytest tests/test_db.py -v
```
Expected: tutti PASS

- [ ] **Step 6: Commit**

```bash
git add db.py tests/conftest.py tests/test_db.py
git commit -m "feat: add db query helpers"
```

---

## Task 5: app.py — Flask app e route

**Files:**
- Create: `app.py`
- Create: `tests/test_app.py`

- [ ] **Step 1: Scrivi i test delle route**

`tests/test_app.py`:
```python
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
```

- [ ] **Step 2: Esegui i test per verificare che falliscono**

```bash
pytest tests/test_app.py -v
```
Expected: FAIL con `ModuleNotFoundError: No module named 'app'`

- [ ] **Step 3: Implementa app.py**

```python
import sqlite3
import os
from flask import Flask, redirect, url_for, render_template, request, abort
import db as database


def create_app(conn: sqlite3.Connection) -> Flask:
    app = Flask(__name__)
    app.config["DB_CONN"] = conn

    @app.route("/")
    def index():
        return redirect(url_for("books"))

    @app.route("/books")
    def books():
        conn = app.config["DB_CONN"]
        all_books = database.get_all_books(conn)
        return render_template("books.html", books=all_books)

    @app.route("/books/<int:book_id>")
    def book_detail(book_id: int):
        conn = app.config["DB_CONN"]
        book = database.get_book(conn, book_id)
        if book is None:
            abort(404)
        characters = database.get_characters(conn, book_id)
        return render_template("book.html", book=book, characters=characters)

    @app.route("/books/<int:book_id>/characters/<path:name>")
    def character_sentences(book_id: int, name: str):
        conn = app.config["DB_CONN"]
        book = database.get_book(conn, book_id)
        if book is None:
            abort(404)
        role = request.args.get("role") or None
        page = max(1, int(request.args.get("page", 1)))
        per_page = 20
        results = database.get_sentences_for_character(
            conn, book_id, name, role, page, per_page
        )
        all_roles = database.get_roles_for_character(conn, book_id, name)
        total_pages = max(1, (results["total"] + per_page - 1) // per_page)
        return render_template(
            "character.html",
            book=book,
            name=name,
            sentences=results["sentences"],
            total=results["total"],
            page=page,
            total_pages=total_pages,
            role=role,
            all_roles=all_roles,
        )

    @app.route("/search")
    def search():
        conn = app.config["DB_CONN"]
        q = request.args.get("q", "").strip()
        book_id_str = request.args.get("book_id", "")
        role = request.args.get("role") or None
        page = max(1, int(request.args.get("page", 1)))
        per_page = 20
        book_id = int(book_id_str) if book_id_str.isdigit() else None

        results = {"total": 0, "sentences": []}
        if q:
            results = database.search_character(conn, q, book_id, role, page, per_page)

        all_books = database.get_all_books(conn)
        total_pages = max(1, (results["total"] + per_page - 1) // per_page)
        return render_template(
            "search.html",
            q=q,
            book_id=book_id,
            role=role,
            sentences=results["sentences"],
            total=results["total"],
            page=page,
            total_pages=total_pages,
            all_books=all_books,
        )

    @app.route("/stats")
    def stats():
        conn = app.config["DB_CONN"]
        all_books = database.get_all_books(conn)
        book_id_str = request.args.get("book_id", "")
        book_id = int(book_id_str) if book_id_str.isdigit() else (all_books[0]["id"] if all_books else None)
        book = database.get_book(conn, book_id) if book_id else None
        char_stats = database.get_stats_for_book(conn, book_id) if book_id else []
        return render_template(
            "stats.html",
            all_books=all_books,
            book=book,
            book_id=book_id,
            char_stats=char_stats,
        )

    return app


if __name__ == "__main__":
    import sys
    json_path = "dataset.json"
    db_path = "dataset.db"

    if not os.path.exists(db_path):
        print(f"Inizializzazione database da {json_path}...")
        conn = database.init_db(db_path)
        database.import_json(conn, json_path)
        print("Database creato.")
    else:
        conn = database.init_db(db_path)

    app = create_app(conn)
    app.run(debug=True, port=5000)
```

- [ ] **Step 4: Crea template stub minimi** (necessari perché i test renderizzano template)

```bash
mkdir -p templates
```

`templates/base.html` (stub):
```html
<!DOCTYPE html><html><body>{% block content %}{% endblock %}</body></html>
```

`templates/books.html` (stub):
```html
{% extends "base.html" %}{% block content %}{% for b in books %}{{ b.title }}{% endfor %}{% endblock %}
```

`templates/book.html` (stub):
```html
{% extends "base.html" %}{% block content %}{% for c in characters %}{{ c.name }}{% endfor %}{% endblock %}
```

`templates/character.html` (stub):
```html
{% extends "base.html" %}{% block content %}{{ name }}{% for s in sentences %}{% for t in s.tokens %}{{ t.form }} {% endfor %}{% endfor %}{% endblock %}
```

`templates/search.html` (stub):
```html
{% extends "base.html" %}{% block content %}{% for s in sentences %}{{ s.character_name }}{% endfor %}{% endblock %}
```

`templates/stats.html` (stub):
```html
{% extends "base.html" %}{% block content %}{% if book %}{{ book.title }}{% endif %}{% endblock %}
```

- [ ] **Step 5: Esegui i test per verificare che passano**

```bash
pytest tests/test_app.py -v
```
Expected: tutti PASS

- [ ] **Step 6: Commit**

```bash
git add app.py tests/test_app.py templates/
git commit -m "feat: add Flask routes and stub templates"
```

---

## Task 6: Template base.html e books.html

**Files:**
- Create: `templates/base.html`
- Create: `templates/books.html`

- [ ] **Step 1: Crea templates/base.html**

```html
<!DOCTYPE html>
<html lang="it">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{% block title %}Dataset Viewer{% endblock %}</title>
  <style>
    *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
    body { display: flex; min-height: 100vh; font-family: system-ui, sans-serif;
           background: #0f172a; color: #e2e8f0; }
    a { color: #38bdf8; text-decoration: none; }
    a:hover { text-decoration: underline; }

    /* Sidebar */
    #sidebar { width: 220px; min-width: 220px; background: #1e293b;
               padding: 16px 0; display: flex; flex-direction: column;
               position: sticky; top: 0; height: 100vh; overflow-y: auto; }
    #sidebar .logo { padding: 0 16px 16px; font-weight: 700; font-size: 1rem;
                     color: #f1f5f9; border-bottom: 1px solid #334155; }
    #sidebar .section-label { padding: 16px 16px 6px;
                               font-size: 0.65rem; text-transform: uppercase;
                               letter-spacing: .08em; color: #64748b; }
    #sidebar ul { list-style: none; }
    #sidebar ul li a { display: block; padding: 6px 16px; font-size: 0.875rem;
                       color: #94a3b8; }
    #sidebar ul li a:hover, #sidebar ul li a.active
      { background: #0f172a; color: #f1f5f9; text-decoration: none; }
    #sidebar .nav-links { padding: 16px 0; border-top: 1px solid #334155; margin-top: auto; }
    #sidebar .nav-links a { display: block; padding: 8px 16px;
                            font-size: 0.875rem; color: #94a3b8; }
    #sidebar .nav-links a:hover { color: #f1f5f9; text-decoration: none; }

    /* Main */
    #main { flex: 1; padding: 32px; max-width: 900px; }
    h1 { font-size: 1.5rem; color: #f1f5f9; margin-bottom: 4px; }
    h2 { font-size: 1.1rem; color: #f1f5f9; margin-bottom: 12px; }
    .subtitle { color: #64748b; font-size: 0.875rem; margin-bottom: 24px; }

    /* Table */
    table { width: 100%; border-collapse: collapse; font-size: 0.875rem; }
    th { text-align: left; padding: 8px 12px; color: #64748b;
         border-bottom: 1px solid #334155; font-weight: 500; }
    td { padding: 8px 12px; border-bottom: 1px solid #1e293b; }
    tr:hover td { background: #1e293b; }

    /* Badge / chip */
    .badge { display: inline-block; padding: 2px 8px; border-radius: 9999px;
             font-size: 0.75rem; background: #1e3a5f; color: #38bdf8; }
    .badge.role { background: #2e1065; color: #c084fc; }

    /* Sentence */
    .sentence-card { background: #1e293b; border-radius: 6px; padding: 12px 16px;
                     margin-bottom: 8px; font-size: 0.9rem; line-height: 1.8; }
    .sentence-card .meta { font-size: 0.75rem; color: #64748b; margin-bottom: 6px; }
    .char-token { background: #1e3a5f; color: #38bdf8; border-radius: 3px;
                  padding: 0 3px; }

    /* Form */
    .form-row { display: flex; gap: 10px; flex-wrap: wrap; margin-bottom: 20px; }
    input[type=text], select {
      background: #1e293b; border: 1px solid #334155; color: #e2e8f0;
      padding: 8px 12px; border-radius: 5px; font-size: 0.875rem; }
    input[type=text] { flex: 2; min-width: 160px; }
    select { flex: 1; min-width: 120px; }
    button[type=submit] {
      background: #0ea5e9; color: #fff; border: none; padding: 8px 20px;
      border-radius: 5px; cursor: pointer; font-size: 0.875rem; }
    button[type=submit]:hover { background: #0284c7; }

    /* Pagination */
    .pagination { display: flex; gap: 6px; margin-top: 20px; align-items: center; }
    .pagination a, .pagination span {
      padding: 5px 10px; border-radius: 4px; font-size: 0.8rem;
      background: #1e293b; color: #94a3b8; }
    .pagination a:hover { background: #334155; text-decoration: none; }
    .pagination .current { background: #0ea5e9; color: #fff; }

    /* Stats */
    .chart-container { background: #1e293b; border-radius: 8px; padding: 20px;
                       margin-bottom: 24px; }
  </style>
</head>
<body>
<nav id="sidebar">
  <div class="logo">📚 Dataset Viewer</div>
  <div class="section-label">Libri</div>
  <ul>
    {% for b in sidebar_books %}
    <li><a href="{{ url_for('book_detail', book_id=b.id) }}"
           class="{{ 'active' if request.path == url_for('book_detail', book_id=b.id) else '' }}">
      {{ b.title[:28] }}{% if b.title|length > 28 %}…{% endif %}
    </a></li>
    {% endfor %}
  </ul>
  <div class="nav-links">
    <a href="{{ url_for('search') }}" class="{{ 'active' if request.path == '/search' else '' }}">🔍 Ricerca</a>
    <a href="{{ url_for('stats') }}"  class="{{ 'active' if request.path == '/stats'  else '' }}">📊 Statistiche</a>
  </div>
</nav>
<main id="main">
  {% block content %}{% endblock %}
</main>
{% block scripts %}{% endblock %}
</body>
</html>
```

- [ ] **Step 2: Aggiorna app.py per iniettare sidebar_books in ogni response**

Aggiungi in `create_app`, dopo la definizione delle route e prima di `return app`:
```python
    @app.context_processor
    def inject_sidebar():
        return {"sidebar_books": database.get_all_books(app.config["DB_CONN"])}
```

- [ ] **Step 3: Crea templates/books.html**

```html
{% extends "base.html" %}
{% block title %}Libri — Dataset Viewer{% endblock %}
{% block content %}
<h1>Tutti i libri</h1>
<p class="subtitle">{{ books|length }} libri nel dataset</p>
<table>
  <thead>
    <tr>
      <th>Titolo</th>
      <th>Autore</th>
      <th>Anno</th>
      <th>Frasi</th>
      <th>Token</th>
      <th>Personaggi</th>
    </tr>
  </thead>
  <tbody>
    {% for b in books %}
    <tr>
      <td><a href="{{ url_for('book_detail', book_id=b.id) }}">{{ b.title }}</a></td>
      <td>{{ b.author }}</td>
      <td>{{ b.year or '—' }}</td>
      <td>{{ b.n_sentences }}</td>
      <td>{{ b.n_tokens }}</td>
      <td>{{ b.n_characters }}</td>
    </tr>
    {% endfor %}
  </tbody>
</table>
{% endblock %}
```

- [ ] **Step 4: Verifica manualmente**

```bash
python app.py
```
Apri http://localhost:5000 — deve mostrare la lista libri con sidebar.

- [ ] **Step 5: Commit**

```bash
git add templates/base.html templates/books.html app.py
git commit -m "feat: add base layout and books list page"
```

---

## Task 7: Template book.html e character.html

**Files:**
- Create: `templates/book.html`
- Create: `templates/character.html`

- [ ] **Step 1: Crea templates/book.html**

```html
{% extends "base.html" %}
{% block title %}{{ book.title }} — Dataset Viewer{% endblock %}
{% block content %}
<h1>{{ book.title }}</h1>
<p class="subtitle">{{ book.author }}{% if book.year %} · {{ book.year }}{% endif %} · {{ book.n_sentences }} frasi · {{ book.n_tokens }} token</p>

<h2>Personaggi</h2>
<table>
  <thead>
    <tr>
      <th>Nome</th>
      <th>Occorrenze</th>
      <th>Ruolo principale</th>
      <th></th>
    </tr>
  </thead>
  <tbody>
    {% for c in characters %}
    <tr>
      <td>{{ c.name }}</td>
      <td>{{ c.occurrences }}</td>
      <td><span class="badge role">{{ c.top_role or '—' }}</span></td>
      <td>
        <a href="{{ url_for('character_sentences', book_id=book.id, name=c.name) }}">→ frasi</a>
      </td>
    </tr>
    {% endfor %}
  </tbody>
</table>
{% endblock %}
```

- [ ] **Step 2: Crea templates/character.html**

```html
{% extends "base.html" %}
{% block title %}{{ name }} — {{ book.title }}{% endblock %}
{% block content %}
<h1>{{ name }}</h1>
<p class="subtitle">
  <a href="{{ url_for('book_detail', book_id=book.id) }}">{{ book.title }}</a>
  · {{ total }} frase{{ 'i' if total != 1 else '' }}
</p>

<form method="get" class="form-row">
  <select name="role" onchange="this.form.submit()">
    <option value="">Tutti i ruoli</option>
    {% for r in all_roles %}
    <option value="{{ r.role }}" {% if role == r.role %}selected{% endif %}>
      {{ r.role }} ({{ r.count }})
    </option>
    {% endfor %}
  </select>
  {% if role %}<a href="{{ url_for('character_sentences', book_id=book.id, name=name) }}">✕ rimuovi filtro</a>{% endif %}
</form>

{% for s in sentences %}
<div class="sentence-card">
  <div class="meta">Frase #{{ s.sentence_id }}</div>
  {% for tok in s.tokens %}
    {%- if tok.character == name -%}
      <span class="char-token" title="{{ tok.deprel }}">{{ tok.form }}</span>
    {%- else -%}
      {{ tok.form }}
    {%- endif -%}
    {{ ' ' }}
  {% endfor %}
</div>
{% else %}
<p class="subtitle">Nessuna frase trovata.</p>
{% endfor %}

{% if total_pages > 1 %}
<div class="pagination">
  {% if page > 1 %}
  <a href="?page={{ page - 1 }}{% if role %}&role={{ role }}{% endif %}">‹ Prec</a>
  {% endif %}
  {% for p in range(1, total_pages + 1) %}
  {% if p == page %}
    <span class="current">{{ p }}</span>
  {% elif p == 1 or p == total_pages or (p >= page - 2 and p <= page + 2) %}
    <a href="?page={{ p }}{% if role %}&role={{ role }}{% endif %}">{{ p }}</a>
  {% elif p == page - 3 or p == page + 3 %}
    <span>…</span>
  {% endif %}
  {% endfor %}
  {% if page < total_pages %}
  <a href="?page={{ page + 1 }}{% if role %}&role={{ role }}{% endif %}">Succ ›</a>
  {% endif %}
</div>
{% endif %}
{% endblock %}
```

- [ ] **Step 3: Verifica manualmente**

```bash
python app.py
```
Clicca un libro → vedi tabella personaggi. Clicca "→ frasi" → vedi frasi con token evidenziato.

- [ ] **Step 4: Commit**

```bash
git add templates/book.html templates/character.html
git commit -m "feat: add book detail and character sentences pages"
```

---

## Task 8: Template search.html

**Files:**
- Create: `templates/search.html`

- [ ] **Step 1: Crea templates/search.html**

```html
{% extends "base.html" %}
{% block title %}Ricerca — Dataset Viewer{% endblock %}
{% block content %}
<h1>Ricerca</h1>
<p class="subtitle">Cerca frasi per nome personaggio (anche parziale)</p>

<form method="get" class="form-row">
  <input type="text" name="q" value="{{ q }}" placeholder="Nome personaggio…" autofocus>
  <select name="book_id">
    <option value="">Tutti i libri</option>
    {% for b in all_books %}
    <option value="{{ b.id }}" {% if book_id == b.id %}selected{% endif %}>{{ b.title }}</option>
    {% endfor %}
  </select>
  <button type="submit">Cerca</button>
</form>

{% if q %}
  <p class="subtitle">{{ total }} risultat{{ 'o' if total == 1 else 'i' }} per "<strong>{{ q }}</strong>"</p>

  {% for s in sentences %}
  <div class="sentence-card">
    <div class="meta">
      {{ s.book_title }} · frase #{{ s.sentence_id }}
      · ruolo: <span class="badge role">{{ s.role }}</span>
      · personaggio: <strong>{{ s.character_name }}</strong>
    </div>
    {% for tok in s.tokens %}
      {%- if tok.character == s.character_name -%}
        <span class="char-token" title="{{ tok.deprel }}">{{ tok.form }}</span>
      {%- else -%}
        {{ tok.form }}
      {%- endif -%}
      {{ ' ' }}
    {% endfor %}
  </div>
  {% else %}
  <p class="subtitle">Nessun risultato.</p>
  {% endfor %}

  {% if total_pages > 1 %}
  <div class="pagination">
    {% if page > 1 %}
    <a href="?q={{ q }}&book_id={{ book_id or '' }}&page={{ page - 1 }}">‹ Prec</a>
    {% endif %}
    {% for p in range(1, total_pages + 1) %}
    {% if p == page %}
      <span class="current">{{ p }}</span>
    {% elif p == 1 or p == total_pages or (p >= page - 2 and p <= page + 2) %}
      <a href="?q={{ q }}&book_id={{ book_id or '' }}&page={{ p }}">{{ p }}</a>
    {% elif p == page - 3 or p == page + 3 %}
      <span>…</span>
    {% endif %}
    {% endfor %}
    {% if page < total_pages %}
    <a href="?q={{ q }}&book_id={{ book_id or '' }}&page={{ page + 1 }}">Succ ›</a>
    {% endif %}
  </div>
  {% endif %}
{% endif %}
{% endblock %}
```

- [ ] **Step 2: Verifica manualmente**

```bash
python app.py
```
Vai su http://localhost:5000/search, cerca un nome parziale come "Brown" → risultati con token evidenziato.

- [ ] **Step 3: Commit**

```bash
git add templates/search.html
git commit -m "feat: add search page"
```

---

## Task 9: Template stats.html e static/app.js

**Files:**
- Create: `templates/stats.html`
- Create: `static/app.js`

La pagina statistiche deve:
- Mostrare un selettore libro (GET param `book_id`)
- Grafico a barre orizzontali: top-N personaggi per occorrenze
- Grafico a barre verticali: distribuzione ruoli del personaggio selezionato (click su barra)

I dati dei grafici vengono passati dal server come JSON inline nel template; Chart.js li legge da `static/app.js`.

- [ ] **Step 1: Aggiorna la route /stats in app.py per passare i dati ruoli**

Modifica la route `stats` in `app.py`:
```python
    @app.route("/stats")
    def stats():
        conn = app.config["DB_CONN"]
        all_books = database.get_all_books(conn)
        book_id_str = request.args.get("book_id", "")
        book_id = int(book_id_str) if book_id_str.isdigit() else (all_books[0]["id"] if all_books else None)
        book = database.get_book(conn, book_id) if book_id else None
        char_stats = database.get_stats_for_book(conn, book_id) if book_id else []
        # Ruoli per ogni personaggio (dict nome → lista {role, count})
        roles_by_char = {}
        for c in char_stats:
            roles = database.get_roles_for_character(conn, book_id, c["name"])
            roles_by_char[c["name"]] = [{"role": r["role"], "count": r["count"]} for r in roles]
        return render_template(
            "stats.html",
            all_books=all_books,
            book=book,
            book_id=book_id,
            char_stats=char_stats,
            roles_by_char=roles_by_char,
        )
```

- [ ] **Step 2: Crea templates/stats.html**

```html
{% extends "base.html" %}
{% block title %}Statistiche — Dataset Viewer{% endblock %}
{% block content %}
<h1>Statistiche</h1>

<form method="get" class="form-row" style="margin-bottom:24px">
  <select name="book_id" onchange="this.form.submit()">
    {% for b in all_books %}
    <option value="{{ b.id }}" {% if book_id == b.id %}selected{% endif %}>{{ b.title }}</option>
    {% endfor %}
  </select>
</form>

{% if book %}
<p class="subtitle">{{ book.title }} · {{ book.author }}</p>

<div class="chart-container">
  <h2>Occorrenze per personaggio</h2>
  <canvas id="chartOccurrences" height="80"></canvas>
</div>

<div class="chart-container">
  <h2>Distribuzione ruoli — <span id="charNameLabel">{{ char_stats[0].name if char_stats else '' }}</span></h2>
  <p class="subtitle">Clicca una barra del grafico sopra per vedere i ruoli del personaggio</p>
  <canvas id="chartRoles" height="80"></canvas>
</div>
{% endif %}
{% endblock %}

{% block scripts %}
{% if book and char_stats %}
<script src="https://cdn.jsdelivr.net/npm/chart.js@4/dist/chart.umd.min.js"></script>
<script>
  const charStats = {{ char_stats | tojson }};
  const rolesByChar = {{ roles_by_char | tojson }};
</script>
<script src="{{ url_for('static', filename='app.js') }}"></script>
{% endif %}
{% endblock %}
```

- [ ] **Step 3: Crea static/app.js**

```javascript
const COLORS = [
  "#38bdf8","#818cf8","#34d399","#fb923c","#f472b6",
  "#a78bfa","#4ade80","#fbbf24","#e879f9","#60a5fa"
];

const occLabels = charStats.map(c => c.name);
const occData   = charStats.map(c => c.occurrences);

const ctxOcc = document.getElementById("chartOccurrences").getContext("2d");
const occChart = new Chart(ctxOcc, {
  type: "bar",
  data: {
    labels: occLabels,
    datasets: [{
      label: "Occorrenze",
      data: occData,
      backgroundColor: COLORS,
      borderRadius: 4,
    }]
  },
  options: {
    indexAxis: "y",
    responsive: true,
    plugins: { legend: { display: false } },
    scales: {
      x: { ticks: { color: "#94a3b8" }, grid: { color: "#1e293b" } },
      y: { ticks: { color: "#e2e8f0" }, grid: { color: "#1e293b" } }
    },
    onClick: (_evt, elements) => {
      if (!elements.length) return;
      const idx = elements[0].index;
      const name = occLabels[idx];
      showRoles(name);
    }
  }
});

const ctxRoles = document.getElementById("chartRoles").getContext("2d");
let rolesChart = null;

function showRoles(name) {
  document.getElementById("charNameLabel").textContent = name;
  const roles = rolesByChar[name] || [];
  const labels = roles.map(r => r.role);
  const data   = roles.map(r => r.count);

  if (rolesChart) {
    rolesChart.data.labels = labels;
    rolesChart.data.datasets[0].data = data;
    rolesChart.update();
  } else {
    rolesChart = new Chart(ctxRoles, {
      type: "bar",
      data: {
        labels,
        datasets: [{
          label: "Conteggio",
          data,
          backgroundColor: "#818cf8",
          borderRadius: 4,
        }]
      },
      options: {
        responsive: true,
        plugins: { legend: { display: false } },
        scales: {
          x: { ticks: { color: "#e2e8f0" }, grid: { color: "#1e293b" } },
          y: { ticks: { color: "#94a3b8" }, grid: { color: "#1e293b" } }
        }
      }
    });
  }
}

// Mostra il primo personaggio di default
if (occLabels.length) showRoles(occLabels[0]);
```

- [ ] **Step 4: Verifica manualmente**

```bash
python app.py
```
Vai su http://localhost:5000/stats — vedi grafico occorrenze. Clicca una barra → grafico ruoli si aggiorna.

- [ ] **Step 5: Commit**

```bash
git add templates/stats.html static/app.js app.py
git commit -m "feat: add statistics page with Chart.js"
```

---

## Task 10: Esegui tutti i test e verifica finale

**Files:** nessuno — solo verifica

- [ ] **Step 1: Esegui tutta la suite di test**

```bash
pytest tests/ -v
```
Expected: tutti PASS

- [ ] **Step 2: Avvia l'app con il dataset reale e verifica le tre sezioni**

```bash
python app.py
```
Controlla:
- http://localhost:5000 → lista libri
- Click su un libro → tabella personaggi con ruolo principale
- Click "→ frasi" su un personaggio → frasi paginate con token evidenziato e filtro ruolo
- http://localhost:5000/search → ricerca parziale funzionante
- http://localhost:5000/stats → grafici, click su barra aggiorna ruoli

- [ ] **Step 3: Commit finale**

```bash
git add .
git commit -m "feat: complete dataset viewer app"
```

<div align="center">

# Chars-Dataset

</div>

A linguistic dataset of English-language novels in CoNLL-U format, converted to JSON and CSV with character annotations.

---

## Project structure

```
charsdataset/
├── app.py                      # Flask web viewer (entrypoint)
├── db.py                       # SQLite layer: schema, JSON import, queries
├── templates/                  # Jinja2 templates
│   ├── base.html               # Layout with sidebar
│   ├── books.html              # Book list
│   ├── book.html               # Book detail + characters table
│   ├── character.html          # Sentences for a character (paginated)
│   ├── search.html             # Search by character name
│   └── stats.html              # Statistics with Chart.js charts
├── static/
│   └── app.js                  # Chart.js initialisation (stats page)
├── tests/
│   ├── conftest.py             # Shared pytest fixtures
│   ├── test_db.py              # Unit tests for db.py
│   └── test_app.py             # Integration tests for Flask routes
├── main.py                     # Dataset build entrypoint
├── build_dataset/              # Build package
│   ├── __init__.py
│   ├── config.py               # Paths, author lookup, title overrides
│   ├── models.py               # Dataclasses: Token, Sentence, Character, Book
│   ├── parser.py               # ConlluParser
│   ├── extractor.py            # CharacterExtractor
│   └── dataset.py              # Dataset (build + export)
├── dataset.json                # Output: hierarchical structure (~438 MB)
├── dataset.csv                 # Output: one row per sentence (~8 MB)
└── drive-download-*.zip        # Source: compressed CoNLL-U files
```

---

## Web viewer

A local Flask app to browse the dataset without opening raw files.

### Setup

```bash
pip install -r requirements.txt
python app.py
```

Then open **http://localhost:5000**.

On first run `dataset.db` is created automatically from `dataset.json`. To rebuild after adding new books, delete `dataset.db` and relaunch.

### Features

| Section | Description |
|---------|-------------|
| **Books** | List of all books with author, year, sentence/token counts and number of characters |
| **Book detail** | Characters table with total occurrences and dominant syntactic role; link to sentences |
| **Character sentences** | Paginated sentences where the character appears, token highlighted; filterable by syntactic role |
| **Search** | Full-text search by character name (partial match); filterable by book |
| **Statistics** | Interactive bar charts: occurrences per character + role distribution (click a bar to switch character) |

---

## Building the dataset

```bash
python3 main.py
```

Produces `dataset.json` and `dataset.csv` in the current directory.

---

## Data format

### dataset.json

Hierarchical structure: **books → sentences → tokens**.

```json
{
  "libri": [
    {
      "id_libro":   1,
      "titolo_libro": "The Third Life of Grange Copeland",
      "autore":     "Alice Walker",
      "anno":       1970,
      "n_frasi":    4951,
      "n_token":    96304,
      "personaggi": [
        {
          "nome":        "Brownfield",
          "occorrenze":  469,
          "ruoli":       { "nsubj": 291, "obl": 46 }
        }
      ],
      "frasi": [
        {
          "id_frase": 1,
          "token": [
            {
              "id_token":   1,
              "form":       "The",
              "lemma":      "the",
              "upos":       "DET",
              "xpos":       "DT",
              "feats":      "Definite=Def|PronType=Art",
              "head":       3,
              "deprel":     "det",
              "start_char": 0,
              "end_char":   3,
              "personaggio": null
            }
          ]
        }
      ]
    }
  ]
}
```

#### Token fields

| Field | Type | Description |
|-------|------|-------------|
| `id_token` | int | Token index within the sentence (starting from 1) |
| `form` | str | Original token form |
| `lemma` | str | Lemma |
| `upos` | str | Universal POS tag (UD tagset) |
| `xpos` | str | Penn Treebank POS tag |
| `feats` | str | Morphological features (`"Key=Val\|Key=Val"`) |
| `head` | int | Head token index (syntactic dependency) |
| `deprel` | str | Dependency relation |
| `start_char` | int\|null | Start character offset in the original text |
| `end_char` | int\|null | End character offset in the original text |
| `personaggio` | str\|null | Canonical character name, if the token belongs to a recognised span |

### dataset.csv

One row per sentence, flattened from the JSON.

| Column | Description |
|--------|-------------|
| `book_id` | Numeric book identifier |
| `title` | Novel title |
| `author` | Author name |
| `year` | Publication year |
| `sentence_id` | Sentence identifier within the book |
| `text` | Reconstructed sentence text (tokens joined by space) |
| `n_tokens` | Number of tokens in the sentence |
| `characters` | Characters mentioned in the sentence, separated by `;` |

---

## Character extraction

Characters are identified automatically as **spans of consecutive `PROPN` tokens** with at least 3 occurrences in the text. The top 30 most frequent characters are selected per book.

For each character the following are recorded:
- **nome** — canonical form (the most frequent form in the text)
- **occorrenze** — total number of mentions
- **ruoli** — distribution of syntactic roles (`nsubj`, `obj`, `nmod`, …)

Every token belonging to a recognised character span receives the `personaggio` field with the canonical name.

---

## Adding new books

1. Add the `.conllu` file to the zip — it is discovered automatically.
2. If the author is new, add an entry in `build_dataset/config.py`:
   ```python
   AUTHOR_NAMES["SURNAME"] = "First Last"
   ```
3. If the auto-generated title is wrong, add an entry in `OVERRIDES`:
   ```python
   OVERRIDES["SURNAME_TITLERAW"] = {"title": "Correct Title", "year": 1950}
   ```
4. Re-run `python3 main.py` to rebuild `dataset.json`.
5. Delete `dataset.db` and relaunch `python app.py` to rebuild the viewer database.

---

## Source format: CoNLL-U

Source files follow the [CoNLL-U](https://universaldependencies.org/format.html) format with 10 tab-separated columns:

```
ID  FORM  LEMMA  UPOS  XPOS  FEATS  HEAD  DEPREL  DEPS  MISC
```

The `MISC` field contains `start_char` and `end_char` for mapping back to character offsets in the original text.

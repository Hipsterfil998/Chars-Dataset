# CharDataset

A linguistic dataset of English-language novels in CoNLL-U format, converted to JSON and CSV with character annotations.

**Statistics:** 11 books · 60,028 sentences · 1,195,013 tokens

---

## Project structure

```
charsdataset/
├── main.py                     # Entrypoint
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

## Usage

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
      "id_libro":     1,
      "titolo_libro": "Mrs Dalloway",
      "autore":       "Virginia Woolf",
      "anno":         1925,
      "n_frasi":      3533,
      "n_token":      78450,
      "personaggi": [
        {
          "nome":       "Clarissa",
          "occorrenze": 156,
          "ruoli":      { "nsubj": 45, "obj": 12 }
        }
      ],
      "frasi": [
        {
          "id_frase": 1,
          "token": [
            {
              "id_token":    1,
              "form":        "Mrs.",
              "lemma":       "Mrs.",
              "upos":        "PROPN",
              "xpos":        "NNP",
              "feats":       "Number=Sing",
              "head":        13,
              "deprel":      "nsubj",
              "start_char":  0,
              "end_char":    4,
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
| `id_libro` | Numeric book identifier |
| `titolo_libro` | Novel title |
| `autore` | Author name |
| `anno` | Publication year |
| `id_frase` | Sentence identifier within the book |
| `testo` | Reconstructed sentence text (tokens joined by space) |
| `n_token` | Number of tokens in the sentence |
| `personaggi` | Characters mentioned in the sentence, separated by `;` |

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
   OVERRIDES["SURNAME_TITLERAW"] = {"titolo_libro": "Correct Title", "anno": 1950}
   ```
4. Re-run `python3 main.py`.

---

## Source format: CoNLL-U

Source files follow the [CoNLL-U](https://universaldependencies.org/format.html) format with 10 tab-separated columns:

```
ID  FORM  LEMMA  UPOS  XPOS  FEATS  HEAD  DEPREL  DEPS  MISC
```

The `MISC` field contains `start_char` and `end_char` for mapping back to character offsets in the original text.

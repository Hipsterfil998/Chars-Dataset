<div align="center">

# Chars-Dataset

</div>

A linguistic dataset of English-language novels in CoNLL-U format, converted to JSON and CSV with character annotations.

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
  "books": [
    {
      "book_id":     1,
      "title":       "Mrs Dalloway",
      "author":      "Virginia Woolf",
      "year":        1925,
      "n_sentences": 3533,
      "n_tokens":    78450,
      "characters": [
        {
          "name":        "Clarissa",
          "occurrences": 156,
          "roles":       { "nsubj": 45, "obj": 12 }
        }
      ],
      "sentences": [
        {
          "sentence_id": 1,
          "token": [
            {
              "token_id":   1,
              "form":       "Mrs.",
              "lemma":      "Mrs.",
              "upos":       "PROPN",
              "xpos":       "NNP",
              "feats":      "Number=Sing",
              "head":       13,
              "deprel":     "nsubj",
              "start_char": 0,
              "end_char":   4,
              "character":  null
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
| `token_id` | int | Token index within the sentence (starting from 1) |
| `form` | str | Original token form |
| `lemma` | str | Lemma |
| `upos` | str | Universal POS tag (UD tagset) |
| `xpos` | str | Penn Treebank POS tag |
| `feats` | str | Morphological features (`"Key=Val\|Key=Val"`) |
| `head` | int | Head token index (syntactic dependency) |
| `deprel` | str | Dependency relation |
| `start_char` | int\|null | Start character offset in the original text |
| `end_char` | int\|null | End character offset in the original text |
| `character` | str\|null | Canonical character name, if the token belongs to a recognised span |

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
- **name** — canonical form (the most frequent form in the text)
- **occurrences** — total number of mentions
- **roles** — distribution of syntactic roles (`nsubj`, `obj`, `nmod`, …)

Every token belonging to a recognised character span receives the `character` field with the canonical name.

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
4. Re-run `python3 main.py`.

---

## Source format: CoNLL-U

Source files follow the [CoNLL-U](https://universaldependencies.org/format.html) format with 10 tab-separated columns:

```
ID  FORM  LEMMA  UPOS  XPOS  FEATS  HEAD  DEPREL  DEPS  MISC
```

The `MISC` field contains `start_char` and `end_char` for mapping back to character offsets in the original text.

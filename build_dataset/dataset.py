import csv
import json
import zipfile
from pathlib import Path

from .config import CSV_FIELDS, METADATA_PATH
from .extractor import CharacterExtractor
from .models import Book
from .parser import ConlluParser


class Dataset:
    """Builds the dataset from a zip archive and exports it to JSON and CSV."""

    def __init__(self, zip_path: Path):
        self.zip_path   = zip_path
        self.books:     list[Book] = []
        self._parser    = ConlluParser()
        self._extractor = CharacterExtractor()
        self._metadata  = self._load_metadata()

    def build(self) -> None:
        with zipfile.ZipFile(self.zip_path) as zf:
            files = sorted(n for n in zf.namelist() if n.endswith(".conllu"))
            print(f"CoNLL-U files found: {len(files)}\n")
            for book_id, fname in enumerate(files, start=1):
                self.books.append(self._build_book(zf, fname, book_id))

    def save_json(self, path: Path) -> None:
        print(f"Saving {path.name} ...", end=" ", flush=True)
        with open(path, "w", encoding="utf-8") as fp:
            json.dump({"books": [b.to_dict() for b in self.books]}, fp,
                      ensure_ascii=False, indent=2)
        print(f"OK  ({path.stat().st_size / 1_048_576:.1f} MB)")

    def save_csv(self, path: Path) -> None:
        print(f"Saving {path.name}  ...", end=" ", flush=True)
        with open(path, "w", encoding="utf-8", newline="") as fp:
            writer = csv.DictWriter(fp, fieldnames=CSV_FIELDS)
            writer.writeheader()
            for book in self.books:
                for row in self._book_to_csv_rows(book):
                    writer.writerow(row)
        print(f"OK  ({path.stat().st_size / 1_048_576:.1f} MB)")

    # ── private ───────────────────────────────────────────────────────────────

    @staticmethod
    def _load_metadata() -> dict[str, dict]:
        """
        Reads metadata.json and builds a key→{title, author, year} dict.
        For keys not present in overrides, an automatic fallback is used
        (author from authors, title derived from the filename in title case).
        Called at runtime so it always reflects the current metadata.json.
        """
        with open(METADATA_PATH, encoding="utf-8") as fp:
            raw = json.load(fp)
        authors   = raw.get("authors", {})
        overrides = raw.get("overrides", {})

        # Build entries for all keys present in overrides
        # (keys not in overrides are generated on-the-fly in _build_book)
        metadata: dict[str, dict] = {}
        for key, corrections in overrides.items():
            surname, _, title_raw = key.partition("_")
            entry = {
                "author": authors.get(surname, surname.title()),
                "title":  title_raw.title(),
                "year":   None,
            }
            entry.update(corrections)
            metadata[key] = entry
        return metadata

    def _resolve_meta(self, key: str) -> dict:
        """Returns metadata for a key, generating a fallback if not present."""
        if key in self._metadata:
            return self._metadata[key]
        with open(METADATA_PATH, encoding="utf-8") as fp:
            authors = json.load(fp).get("authors", {})
        surname, _, title_raw = key.partition("_")
        return {
            "author": authors.get(surname, surname.title()),
            "title":  title_raw.title(),
            "year":   None,
        }

    def _build_book(self, zf: zipfile.ZipFile, fname: str, book_id: int) -> Book:
        key  = fname.replace(".conllu", "")
        meta = self._resolve_meta(key)

        print(f"  {meta['title']:<40}", end=" ", flush=True)
        with zf.open(fname) as f:
            text = f.read().decode("utf-8")

        sentences  = self._parser.parse(text)
        characters = self._extractor.extract(sentences)
        self._extractor.annotate(sentences, characters)

        book = Book(book_id, meta["title"], meta["author"], meta["year"],
                    characters, sentences)
        print(f"{book.n_sentences:>6,} sentences  {book.n_tokens:>8,} tokens  {len(characters):>3} characters")
        return book

    @staticmethod
    def _book_to_csv_rows(book: Book):
        ctx = {"book_id": book.book_id, "title": book.title,
               "author": book.author, "year": book.year}
        for sent in book.sentences:
            yield {
                **ctx,
                "sentence_id": sent.sentence_id,
                "text":        sent.text,
                "n_tokens":    len(sent.token),
                "characters":  ";".join(sent.characters_present),
            }

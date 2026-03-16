from dataclasses import asdict, dataclass, field


@dataclass
class Token:
    token_id:    int
    form:        str
    lemma:       str
    upos:        str
    xpos:        str
    feats:       str          # "Key=Val|Key=Val" or ""
    head:        int
    deprel:      str
    start_char:  int | None
    end_char:    int | None
    character:   str | None = None


@dataclass
class Sentence:
    sentence_id: int
    token:       list[Token] = field(default_factory=list)

    @property
    def text(self) -> str:
        return " ".join(t.form for t in self.token)

    @property
    def characters_present(self) -> list[str]:
        """Unique characters mentioned in the sentence, in order of appearance."""
        return list(dict.fromkeys(t.character for t in self.token if t.character))


@dataclass
class Character:
    name:        str
    occurrences: int
    roles:       dict[str, int]


@dataclass
class Book:
    book_id:    int
    title:      str
    author:     str
    year:       int | None
    characters: list[Character] = field(default_factory=list)
    sentences:  list[Sentence]  = field(default_factory=list)

    @property
    def n_sentences(self) -> int:
        return len(self.sentences)

    @property
    def n_tokens(self) -> int:
        return sum(len(s.token) for s in self.sentences)

    def to_dict(self) -> dict:
        return {
            "book_id":    self.book_id,
            "title":      self.title,
            "author":     self.author,
            "year":       self.year,
            "n_sentences": self.n_sentences,
            "n_tokens":   self.n_tokens,
            "characters": [asdict(c) for c in self.characters],
            "sentences": [
                {"sentence_id": s.sentence_id, "token": [asdict(t) for t in s.token]}
                for s in self.sentences
            ],
        }

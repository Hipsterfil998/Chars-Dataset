from dataclasses import asdict, dataclass, field


@dataclass
class Token:
    id_token:    int
    form:        str
    lemma:       str
    upos:        str
    xpos:        str
    feats:       str          # "Key=Val|Key=Val" oppure ""
    head:        int
    deprel:      str
    start_char:  int | None
    end_char:    int | None
    personaggio: str | None = None


@dataclass
class Sentence:
    id_frase: int
    token:    list[Token] = field(default_factory=list)

    @property
    def testo(self) -> str:
        return " ".join(t.form for t in self.token)

    @property
    def personaggi_presenti(self) -> list[str]:
        """Personaggi unici citati nella frase, in ordine di comparsa."""
        return list(dict.fromkeys(t.personaggio for t in self.token if t.personaggio))


@dataclass
class Personaggio:
    nome:       str
    occorrenze: int
    ruoli:      dict[str, int]


@dataclass
class Book:
    id_libro:     int
    titolo_libro: str
    autore:       str
    anno:         int | None
    personaggi:   list[Personaggio] = field(default_factory=list)
    frasi:        list[Sentence]    = field(default_factory=list)

    @property
    def n_frasi(self) -> int:
        return len(self.frasi)

    @property
    def n_token(self) -> int:
        return sum(len(s.token) for s in self.frasi)

    def to_dict(self) -> dict:
        return {
            "id_libro":     self.id_libro,
            "titolo_libro": self.titolo_libro,
            "autore":       self.autore,
            "anno":         self.anno,
            "n_frasi":      self.n_frasi,
            "n_token":      self.n_token,
            "personaggi":   [asdict(p) for p in self.personaggi],
            "frasi": [
                {"id_frase": s.id_frase, "token": [asdict(t) for t in s.token]}
                for s in self.frasi
            ],
        }

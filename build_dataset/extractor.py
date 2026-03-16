from collections import Counter, defaultdict

from .models import Personaggio, Sentence, Token


class CharacterExtractor:
    """Identifies characters from consecutive PROPN spans and annotates tokens."""

    def __init__(self, top_n: int = 30, min_freq: int = 3):
        self.top_n    = top_n
        self.min_freq = min_freq

    def extract(self, sentences: list[Sentence]) -> list[Personaggio]:
        info: dict[str, dict] = defaultdict(
            lambda: {"count": 0, "roles": Counter(), "forms": Counter()}
        )
        for sent in sentences:
            for span, role in self._propn_spans(sent):
                norm = span.lower()
                info[norm]["count"]       += 1
                info[norm]["roles"][role] += 1
                info[norm]["forms"][span] += 1

        top = sorted(
            ((k, v) for k, v in info.items() if v["count"] >= self.min_freq),
            key=lambda x: x[1]["count"], reverse=True
        )[:self.top_n]

        return [
            Personaggio(
                nome=v["forms"].most_common(1)[0][0],
                occorrenze=v["count"],
                ruoli=dict(v["roles"].most_common()),
            )
            for _, v in top
        ]

    def annotate(self, sentences: list[Sentence], personaggi: list[Personaggio]) -> None:
        """Sets Token.personaggio in-place for every token belonging to a known character."""
        name_map = {p.nome.lower(): p.nome for p in personaggi}
        for sent in sentences:
            i = 0
            while i < len(sent.token):
                span_tokens, j = self._collect_propn_span(sent.token, i)
                if span_tokens:
                    norm = " ".join(t.form for t in span_tokens).lower()
                    if norm in name_map:
                        for tok in span_tokens:
                            tok.personaggio = name_map[norm]
                    i = j
                else:
                    i += 1

    @staticmethod
    def _collect_propn_span(tokens: list[Token], start: int) -> tuple[list[Token], int]:
        if tokens[start].upos != "PROPN":
            return [], start
        j = start + 1
        while j < len(tokens) and tokens[j].upos == "PROPN":
            j += 1
        return tokens[start:j], j

    @staticmethod
    def _propn_spans(sent: Sentence):
        tokens = sent.token
        i = 0
        while i < len(tokens):
            if tokens[i].upos == "PROPN":
                j = i + 1
                while j < len(tokens) and tokens[j].upos == "PROPN":
                    j += 1
                yield " ".join(t.form for t in tokens[i:j]), tokens[i].deprel
                i = j
            else:
                i += 1

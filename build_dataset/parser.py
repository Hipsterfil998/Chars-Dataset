from .models import Sentence, Token


class ConlluParser:
    """Converte testo CoNLL-U in lista di Sentence."""

    def parse(self, text: str) -> list[Sentence]:
        sentences: list[Sentence] = []
        current_tokens: list[Token] = []
        frase_id = 1

        for line in text.splitlines():
            line = line.strip()
            if not line:
                if current_tokens:
                    sentences.append(Sentence(frase_id, current_tokens))
                    current_tokens = []
                    frase_id += 1
            elif line.startswith("#"):
                continue
            else:
                tok = self._parse_line(line)
                if tok:
                    current_tokens.append(tok)

        if current_tokens:
            sentences.append(Sentence(frase_id, current_tokens))
        return sentences

    def _parse_line(self, line: str) -> Token | None:
        fields = line.split("\t")
        if len(fields) != 10 or "-" in fields[0] or "." in fields[0]:
            return None
        start, end = self._parse_misc(fields[9])
        return Token(
            id_token=int(fields[0]),
            form=fields[1],
            lemma=fields[2],
            upos=fields[3],
            xpos=fields[4],
            feats=fields[5] if fields[5] != "_" else "",
            head=int(fields[6]),
            deprel=fields[7],
            start_char=start,
            end_char=end,
        )

    @staticmethod
    def _parse_misc(misc: str) -> tuple[int | None, int | None]:
        start = end = None
        for part in misc.split("|"):
            if part.startswith("start_char="):
                start = int(part[11:])
            elif part.startswith("end_char="):
                end = int(part[9:])
        return start, end

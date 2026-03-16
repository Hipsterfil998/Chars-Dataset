# CharDataset

Dataset linguistico di romanzi in lingua inglese in formato CoNLL-U, convertito in JSON e CSV con annotazioni di personaggi.

## Contenuto del dataset

| # | Titolo | Autore | Anno |
|---|--------|--------|------|
| 1 | The Third Life of Grange Copeland | Alice Walker | 1970 |
| 2 | Between the Acts | Virginia Woolf | 1941 |
| 3 | Jacob's Room | Virginia Woolf | 1922 |
| 4 | Mrs Dalloway | Virginia Woolf | 1925 |
| 5 | Night and Day | Virginia Woolf | 1919 |
| 6 | Orlando: A Biography | Virginia Woolf | 1928 |
| 7 | The Lady in the Looking Glass | Virginia Woolf | 1929 |
| 8 | The Voyage Out | Virginia Woolf | 1915 |
| 9 | The Waves | Virginia Woolf | 1931 |
| 10 | The Years | Virginia Woolf | 1937 |
| 11 | To the Lighthouse | Virginia Woolf | 1927 |

**Statistiche:** 11 libri · 60.028 frasi · 1.195.013 token

---

## Struttura del progetto

```
charsdataset/
├── main.py                     # Entrypoint
├── build_dataset/              # Package di costruzione
│   ├── __init__.py
│   ├── config.py               # Percorsi, lookup autori, correzioni titoli
│   ├── models.py               # Dataclass: Token, Sentence, Personaggio, Book
│   ├── parser.py               # ConlluParser
│   ├── extractor.py            # CharacterExtractor
│   └── dataset.py              # Dataset (build + export)
├── dataset.json                # Output: struttura gerarchica (~438 MB)
├── dataset.csv                 # Output: una riga per frase (~8 MB)
└── drive-download-*.zip        # Sorgente: file CoNLL-U compressi
```

---

## Utilizzo

```bash
python3 main.py
```

Produce `dataset.json` e `dataset.csv` nella directory corrente.

---

## Formato dei dati

### dataset.json

Struttura gerarchica: **libri → frasi → token**.

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

#### Campi token

| Campo | Tipo | Descrizione |
|-------|------|-------------|
| `id_token` | int | Indice del token nella frase (da 1) |
| `form` | str | Forma originale del token |
| `lemma` | str | Lemma |
| `upos` | str | POS universale (UD tagset) |
| `xpos` | str | POS Penn Treebank |
| `feats` | str | Tratti morfologici (`"Key=Val\|Key=Val"`) |
| `head` | int | Indice del token testa (dipendenza sintattica) |
| `deprel` | str | Relazione di dipendenza |
| `start_char` | int\|null | Offset carattere iniziale nel testo originale |
| `end_char` | int\|null | Offset carattere finale nel testo originale |
| `personaggio` | str\|null | Nome canonico del personaggio, se il token appartiene a uno span riconosciuto |

### dataset.csv

Una riga per frase, appiattimento del JSON.

| Colonna | Descrizione |
|---------|-------------|
| `id_libro` | Identificatore numerico del libro |
| `titolo_libro` | Titolo del romanzo |
| `autore` | Nome dell'autore |
| `anno` | Anno di pubblicazione |
| `id_frase` | Identificatore della frase all'interno del libro |
| `testo` | Testo ricostruito della frase (token separati da spazio) |
| `n_token` | Numero di token nella frase |
| `personaggi` | Personaggi citati nella frase, separati da `;` |

---

## Estrazione dei personaggi

I personaggi vengono identificati automaticamente come **span di token `PROPN` consecutivi** con almeno 3 occorrenze nel testo. Per ogni libro vengono selezionati i 30 più frequenti.

Per ogni personaggio vengono registrati:
- **nome** — forma canonica (la più frequente nel testo)
- **occorrenze** — numero totale di menzioni
- **ruoli** — distribuzione dei ruoli sintattici (`nsubj`, `obj`, `nmod`, …)

Ogni token che fa parte di uno span riconosciuto come personaggio riceve il campo `personaggio` con il nome canonico.

---

## Aggiungere nuovi libri

1. Aggiungere il file `.conllu` allo zip — viene scoperto automaticamente.
2. Se l'autore è nuovo, aggiungere una riga in `build_dataset/config.py`:
   ```python
   AUTHOR_NAMES["SURNAME"] = "First Last"
   ```
3. Se il titolo auto-generato è errato, aggiungere una voce in `OVERRIDES`:
   ```python
   OVERRIDES["SURNAME_TITLERAW"] = {"titolo_libro": "Titolo Corretto", "anno": 1950}
   ```
4. Rieseguire `python3 main.py`.

---

## Formato sorgente: CoNLL-U

I file sorgente seguono il formato [CoNLL-U](https://universaldependencies.org/format.html) con 10 colonne tab-separate:

```
ID  FORM  LEMMA  UPOS  XPOS  FEATS  HEAD  DEPREL  DEPS  MISC
```

Il campo `MISC` contiene `start_char` e `end_char` per il mapping ai caratteri del testo originale.

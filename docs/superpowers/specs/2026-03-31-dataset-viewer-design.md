# Dataset Viewer — Design Spec

**Data:** 2026-03-31  
**Stato:** approvato

## Obiettivo

Creare un'interfaccia web locale per consultare il dataset letterario (`dataset.json`) senza aprire file raw o strumenti esterni. L'app deve supportare ricerca mirata per personaggio/ruolo e analisi statistica, e reggere la crescita del dataset nel tempo.

## Tecnologia scelta

**Flask + SQLite + vanilla JS + Chart.js**

- Flask serve le pagine (Jinja2) e le route API
- SQLite come database locale generato automaticamente da `dataset.json` al primo avvio
- Vanilla JS solo per i grafici (Chart.js via CDN) e submit del form ricerca
- Nessun framework frontend — rendering server-side, semplice e robusto
- Dipendenza unica: `flask`

## Struttura file

```
charsdataset/
├── app.py                          # Flask app, route definitions
├── db.py                           # init SQLite da dataset.json, query helpers
├── templates/
│   ├── base.html                   # layout con sidebar fissa
│   ├── books.html                  # lista libri (homepage)
│   ├── book.html                   # dettaglio libro + tabella personaggi
│   ├── character.html              # frasi di un personaggio (paginate)
│   ├── search.html                 # form ricerca + risultati paginati
│   └── stats.html                  # grafici statistici
├── static/
│   └── app.js                      # Chart.js init + eventuale JS minimo
├── dataset.json                    # sorgente dati (esistente)
├── dataset.db                      # generato automaticamente, in .gitignore
└── requirements.txt                # flask
```

## Layout

Sidebar fissa a sinistra con:
- Lista libri (cliccabili)
- Link a Ricerca
- Link a Statistiche

Area principale a destra che cambia in base alla route attiva.

## Schema database

```sql
books      (id INTEGER PK, title TEXT, author TEXT, year INTEGER,
            n_sentences INTEGER, n_tokens INTEGER)

characters (id INTEGER PK, book_id INTEGER FK,
            name TEXT, occurrences INTEGER)

roles      (id INTEGER PK, character_id INTEGER FK,
            role TEXT, count INTEGER)

sentences  (id INTEGER PK, book_id INTEGER FK, sentence_id INTEGER)

tokens     (id INTEGER PK, sentence_id INTEGER FK,
            form TEXT, lemma TEXT, upos TEXT, xpos TEXT,
            feats TEXT, head INTEGER, deprel TEXT,
            start_char INTEGER, end_char INTEGER,
            character TEXT)
```

**Indici:** `tokens.character`, `tokens.sentence_id`, `sentences.book_id`

## Route

| Route | Descrizione |
|---|---|
| `/` | Redirect a `/books` |
| `/books` | Lista tutti i libri: titolo, autore, anno, n. frasi, n. personaggi |
| `/books/<id>` | Dettaglio libro: tabella personaggi con occorrenze e ruolo sintattico principale |
| `/books/<id>/characters/<name>` | Frasi del personaggio nel libro, paginate (20/pagina), filtrabili per ruolo |
| `/search` | Form: query testo + filtro libro + filtro ruolo → risultati paginati con token evidenziato |
| `/stats` | Grafici: occorrenze personaggi (barre), distribuzione ruoli (barre orizzontali); selettore libro |

## Sezioni nel dettaglio

### Libri → Personaggi → Frasi
- Click su libro in sidebar → `GET /books/<id>`: tabella con nome, occorrenze totali, ruolo principale (ruolo con count più alto), link "→ frasi"
- Click "→ frasi" → `GET /books/<id>/characters/<name>`: lista frasi paginate con il token del personaggio evidenziato in blu; dropdown filtro ruolo sintattico

### Ricerca
- Input testo (nome personaggio, parziale ok), select libro, select ruolo
- Submit form GET → risultati paginati (20/pagina)
- Ogni risultato: libro, n. frase, ruolo sintattico, testo frase con token evidenziato

### Statistiche
- Selettore libro (default: primo libro)
- Grafico a barre orizzontali: top-N personaggi per occorrenze
- Grafico a barre: distribuzione ruoli sintattici del personaggio selezionato
- Tutto renderizzato con Chart.js

## Inizializzazione database

All'avvio di `app.py`:
1. Se `dataset.db` non esiste → `db.py` lo crea e importa `dataset.json`
2. Flask parte su `http://localhost:5000`

Per aggiornare il dataset dopo aver aggiunto libri: eliminare `dataset.db` e rilanciare.

## Setup per chi clona la repo

```bash
pip install -r requirements.txt
python app.py
# apri http://localhost:5000
```

`dataset.db` è in `.gitignore`. `dataset.json` è la sorgente di verità versionata.

## Fuori scope

- Autenticazione
- Editing del dataset dall'interfaccia
- Deploy remoto
- Export dei risultati

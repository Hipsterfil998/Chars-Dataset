import argparse
from pathlib import Path

from build_dataset import Dataset
from build_dataset.config import ZIP_PATH

parser = argparse.ArgumentParser(description="Costruisce dataset.json e dataset.csv da un archivio CoNLL-U.")
parser.add_argument("zip",        nargs="?",         type=Path, default=ZIP_PATH,        help=f"Percorso dello zip CoNLL-U (default: {ZIP_PATH})")
parser.add_argument("--json-out", metavar="FILE",    type=Path, default=Path("dataset.json"), help="Output JSON (default: dataset.json)")
parser.add_argument("--csv-out",  metavar="FILE",    type=Path, default=Path("dataset.csv"),  help="Output CSV  (default: dataset.csv)")
args = parser.parse_args()

if not args.zip.exists():
    parser.error(f"File non trovato: {args.zip}")

ds = Dataset(args.zip)
ds.build()
print()
ds.save_json(args.json_out)
ds.save_csv(args.csv_out)

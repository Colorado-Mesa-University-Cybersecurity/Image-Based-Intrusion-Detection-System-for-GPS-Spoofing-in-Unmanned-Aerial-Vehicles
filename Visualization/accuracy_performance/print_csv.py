# print_csv.py
import csv
from pathlib import Path


def read_csv_dicts(path: str):
    """Return (header, rows) where rows is a list[dict]."""
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(p.resolve())

    with p.open("r", encoding="utf-8", errors="ignore", newline="") as f:
        sample = f.read(20000)
        f.seek(0)
        try:
            dialect = csv.Sniffer().sniff(sample, delimiters=[",",";","\t","|"])
            sep = dialect.delimiter
        except Exception:
            sep = ","
        reader = csv.reader(f, delimiter=sep)
        rows = [r for r in reader]

    if not rows:
        return [], []

    header = [h.strip().lstrip("\ufeff") for h in rows[0]]

    # Re-read as DictReader using the same delimiter
    with p.open("r", encoding="utf-8", errors="ignore", newline="") as f:
        dict_reader = csv.DictReader(f, delimiter=sep)
        dict_rows = [{k.strip().lstrip("\ufeff"): (v or "").strip() for k, v in row.items()}
                     for row in dict_reader]

    return header, dict_rows


if __name__ == "__main__":
    repo_root = Path(__file__).resolve().parent.parent.parent
    results_dir = Path(__file__).resolve().parent.parent / "Results"
    candidates = [
        results_dir / "UAVATTACK_Results_filtered.csv",
        results_dir / "2D_Results_filtered.csv",
        repo_root / "UAVATTACK_Results.csv",
        repo_root / "2D_Results.csv",
    ]
    for fp in [c for c in candidates if c.exists()]:
        header, rows = read_csv_dicts(fp)
        print(f"\n=== {fp} ===")
        print("Header:", header)
        print("Rows:", len(rows))
        for r in rows[:5]:
            print(r)

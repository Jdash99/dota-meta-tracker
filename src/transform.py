"""Convierte el JSON crudo mas reciente en filas limpias y las agrega al historico"""

import json
from pathlib import Path

import polars as pl

RAW_DIR = Path("data/raw")
CLEAN_PATH = Path("data/clean/hero_winrates.csv")

BRACKETS = {
    "1": "Herald",
    "2": "Guardian",
    "3": "Crusader",
    "4": "Archon",
    "5": "Legend",
    "6": "Ancient",
    "7": "Divine",
    "8": "Immortal",
    "pro": "Pro",
}

def to_rows(heroes: list, snapshot_date: str) -> pl.DataFrame:
    rows = []
    for hero in heroes:
        for key, bracket in BRACKETS.items():
            rows.append(
                {
                    "snapshot_date": snapshot_date,
                    "hero_id": hero["id"],
                    "hero": hero["localized_name"],
                    "bracket": bracket,
                    "picks": hero.get(f"{key}_pick") or 0,
                    "wins": hero.get(f"{key}_win") or 0,
                }
            )
    # Si no hay picks, el win rate queda nulo en vez de dividir por cero.
    return pl.DataFrame(rows).with_columns(
        win_rate=pl.when(pl.col("picks") > 0).then((pl.col("wins") / pl.col("picks")).round(4))
    )

def main() -> None:
    latest = max(RAW_DIR.glob("*.json"))
    snapshot_date = latest.stem
    today = to_rows(json.loads(latest.read_text(encoding="utf-8")), snapshot_date)

    if CLEAN_PATH.exists():
        history = pl.read_csv(CLEAN_PATH, schema=today.schema)
        # Idempotente: si el dia ya existe, se reemplaza en vez de duplicarse.
        history = history.filter(pl.col("snapshot_date") != snapshot_date)
        today = pl.concat([history, today])

    CLEAN_PATH.parent.mkdir(parents=True, exist_ok=True)
    today.write_csv(CLEAN_PATH)
    print(f"{CLEAN_PATH}: {today.height} filas en total")

if __name__ == "__main__":
    main()

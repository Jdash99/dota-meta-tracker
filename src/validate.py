"""Chequeos de calidad del snapshot mas reciente. Sale con codigo 1 si alguno falla."""

import json
import os
import sys
from pathlib import Path

import polars as pl

RAW_DIR = Path("data/raw")
CLEAN_PATH = Path("data/clean/hero_winrates.csv")
REPORT_PATH = Path("report.md")
MAX_JUMP = 0.15  # maximo cambio de win rate aceptado entre dos dias
MIN_PICKS = 1000  # solo se compara si hay suficientes partidas
MIN_HEROES = 1000  # Dota tiene mas de 120 heroes; menos indica una respuesta incompleta

def run_checks(today: pl.DataFrame, raw_count: int, previous: pl.DataFrame) -> list:
    checks = []

    heroes = today["hero_id"].n_unique()
    checks.append(
        ("Numero de heroes", heroes == raw_count and heroes > MIN_HEROES, f"{heroes} en limpio, {raw_count} en crudo")
    )

    bad_rate = today.filter(~pl.col("win_rate").is_between(0, 1)).height
    checks.append(("Win rate entre 0 y 1", bad_rate == 0, f"{bad_rate} filas fuera de rango"))

    bad_wins = today.filter(pl.col("wins") > pl.col("picks")).height
    checks.append(("Wins <= picks", bad_wins == 0, f"{bad_wins} filas con mas wins que picks"))

    dupes = today.height - today.unique(["snapshot_date", "hero_id", "bracket"]).height
    checks.append(("Sin duplicados", dupes == 0, f"{dupes} filas duplicadas"))

    if previous.is_empty():
        checks.append(("Cambio vs. dia anterior", True, "sin dia anterior para comparar"))
    else:
        jumps = (
            today.join(previous, on=["hero_id", "bracket"], suffix="_prev")
            .filter((pl.col("picks") >= MIN_PICKS) & (pl.col("picks_prev") >= MIN_PICKS))
            .filter((pl.col("win_rate") - pl.col("win_rate_prev")).abs() > MAX_JUMP)
        )
        detail = ", ".join(f"{r['hero']} ({r['bracket']})" for r in jumps.iter_rows(named=True)) or "ninguno"
        checks.append(("Cambio vs. dia anterior", jumps.is_empty(), f"saltos > {MAX_JUMP:.0%}: {detail}"))

    return [(name, bool(ok), detail) for name, ok, detail in checks]

def main() -> None:
    latest = max(RAW_DIR.glob("*.json"))
    raw_count = len(json.loads(latest.read_text(encoding="utf-8")))
    df = pl.read_csv(CLEAN_PATH)
    dates = df["snapshot_date"].unique().sort().to_list()
    today = df.filter(pl.col("snapshot_date") == dates[-1])
    previous = df.filter(pl.col("snapshot_date") == dates[-2]) if len(dates) > 1 else df.clear()

    checks = run_checks(today, raw_count, previous)

    lines = [f"## Validacion del snapshot {dates[-1]}", "", "| Chequeo | Resultado | Detalle |", "| --- | --- | --- |"]
    lines += [f"| {name} | {'OK' if ok else 'FALLA'} | {detail} |" for name, ok, detail in checks]
    report = "\n".join(lines) + "\n"
    REPORT_PATH.write_text(report, encoding="utf-8")
    print(report)

    # En GitHub Actions, el reporte tambien aparece en el resumen de la ejecucion.
    summary = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary:
        with open(summary, "a", encoding="utf-8") as f:
            f.write(report)

    if not all(ok for _, ok, _ in checks):
        sys.exit(1)


if __name__ == "__main__":
    main()

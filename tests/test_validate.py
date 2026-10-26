import json
from pathlib import Path

import polars as pl

from src.transform import to_rows
from src.validate import run_checks

SAMPLE = json.loads(Path("tests/fixtures/herostats_sample.json").read_text(encoding="utf-8"))


def test_clean_data_passes_row_checks():
    df = to_rows(SAMPLE, "2026-10-24")
    checks = {name: ok for name, ok, _ in run_checks(df, 3, df.clear())}
    assert checks["Wins <= picks"] and checks["Sin duplicados"] and checks["Win rate entre 0 y 1"]


def test_more_wins_than_picks_fails():
    df = to_rows(SAMPLE, "2026-10-24").with_columns(wins=pl.col("picks") + 1)
    checks = {name: ok for name, ok, _ in run_checks(df, 3, df.clear())}
    assert checks["Wins <= picks"] is False

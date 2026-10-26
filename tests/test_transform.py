import json
from pathlib import Path

import polars as pl

from src.transform import to_rows

SAMPLE = json.loads(Path("tests/fixtures/herostats_sample.json").read_text(encoding="utf-8"))

def find(df: pl.DataFrame, hero: str, bracket: str) -> dict:
    return df.filter((pl.col("hero") == hero) & (pl.col("bracket") == bracket)).row(0, named=True)

def test_one_row_per_hero_and_bracket():
    df = to_rows(SAMPLE, "2026-10-24")
    assert df.height == 3 * 9

def test_win_rate_is_winds_over_picks():
    df = to_rows(SAMPLE, "2026-10-24")
    assert find(df, "Anti-Mage", "Immortal")["win_rate"] is None

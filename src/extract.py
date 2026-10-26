"""Descarga heroStats de OpenDota y guarda el JSON crudo del dia."""

import json
import sys
import time
from datetime import UTC, datetime
from pathlib import Path

import requests

URL = "https://api.opendota.com/api/heroStats"
RAW_DIR = Path("data/raw")

def fetch(url: str = URL, retries: int = 3) -> list:
    for attempt in range(1, retries + 1):
        try:
            response = requests.get(url, timeout=30)
            if response.status_code == 200:
                return response.json()
            print(f"Intento {attempt}: HTTP {response.status_code}")
        except requests.RequestException as error:
            print(f"Intento {attempt}: {error}")
        if attempt < retries:
            time.sleep(10 * attempt)
    sys.exit("No se pudo descargar heroStats")

def main() -> None:
    heroes = fetch()
    today = datetime.now(UTC).strftime("%Y-%m-%d")
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    path = RAW_DIR / f"{today}.json"
    path.write_text(json.dumps(heroes), encoding="utf-8")
    print(f"Guardado {path} con {len(heroes)} heroes")

if __name__ == "__main__":
    main()

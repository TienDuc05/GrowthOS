#!/usr/bin/env python3
"""Download the two public Olist datasets from Kaggle into data/raw/.

Run: python scripts/download_data.py
Requires a Kaggle account and API token configured for kagglehub.
Manual alternative: download the ZIPs from the Kaggle pages in docs/data_sources.csv
and extract the CSV files into data/raw/olist_ecommerce/ and data/raw/olist_marketing/.
"""
from __future__ import annotations
import json
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "data" / "raw"

DATASETS = {
    "olist_ecommerce": "olistbr/brazilian-ecommerce",
    "olist_marketing": "olistbr/marketing-funnel-olist",
}


def download_kaggle(handle: str, folder: Path) -> None:
    import kagglehub
    folder.mkdir(parents=True, exist_ok=True)
    # The official Kaggle API determines the latest dataset version.
    cache_dir = Path(kagglehub.dataset_download(handle))
    files = list(cache_dir.rglob('*.csv'))
    if not files:
        raise RuntimeError(f"No CSV files returned from Kaggle: {handle}. Check account permissions.")
    for src in files:
        dest = folder / src.name
        if not dest.exists() or dest.stat().st_size != src.stat().st_size:
            shutil.copy2(src, dest)
    print(f"  Copied {len(files)} CSV files to {folder.relative_to(ROOT)}")


def main() -> None:
    results = {}
    for folder, handle in DATASETS.items():
        print(f'\n[{folder}]')
        try:
            download_kaggle(handle, BASE / folder)
            results[folder] = 'downloaded'
            print('  OK')
        except Exception as exc:
            results[folder] = f'ERROR: {exc}'
            print(f'  ERROR: {exc}', file=sys.stderr)
    outfile = ROOT / 'data' / 'download_status.json'
    outfile.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding='utf-8')
    print('\n=== DOWNLOAD STATUS ===')
    print(json.dumps(results, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()

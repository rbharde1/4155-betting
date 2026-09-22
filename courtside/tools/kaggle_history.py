#!/usr/bin/env python3
"""Download or inspect Wyatt Walsh's NBA database without loading it into RAM.
Run in PyCharm or Python 3.10+. No third-party dependencies required.
"""
import argparse
import json
import shutil
import sqlite3
import urllib.request
import zipfile
from pathlib import Path

SOURCE = 'https://www.kaggle.com/datasets/wyattowalsh/basketball'
DOWNLOAD = 'https://www.kaggle.com/api/v1/datasets/download/wyattowalsh/basketball'

def download(directory):
    directory.mkdir(parents=True, exist_ok=True)
    archive = directory / 'basketball.zip'
    if archive.exists():
        raise FileExistsError(f'{archive} already exists; use --database to inspect existing data.')
    print('Downloading the full dataset. This may be large; allow sufficient disk space.')
    try:
        with urllib.request.urlopen(DOWNLOAD, timeout=90) as response, archive.open('wb') as out:
            shutil.copyfileobj(response, out, 1024 * 1024)
        with zipfile.ZipFile(archive) as zipped:
            entries = [i for i in zipped.infolist() if Path(i.filename).suffix.lower() in {'.sqlite', '.sqlite3', '.db'}]
            if not entries:
                raise ValueError('No SQLite database found. Inspect the downloaded archive for the new dataset format.')
            for entry in entries:
                destination = directory / Path(entry.filename).name
                with zipped.open(entry) as src, destination.open('xb') as out:
                    shutil.copyfileobj(src, out, 1024 * 1024)
                yield destination
    except Exception:
        print('If Kaggle requires sign-in, download the archive from the dataset page and pass --database after extraction.')
        raise

def inspect(path):
    with sqlite3.connect(path.resolve().as_uri() + '?mode=ro', uri=True) as connection:
        tables = [r[0] for r in connection.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")]
        result = {}
        for table in tables:
            escaped = '"' + table.replace('"', '""') + '"'
            columns = [r[1] for r in connection.execute(f'PRAGMA table_info({escaped})')]
            count = connection.execute(f'SELECT count(*) FROM {escaped}').fetchone()[0]
            result[table] = {'rows': count, 'columns': columns}
    return {'source': SOURCE, 'author': 'Wyatt Walsh', 'license': 'CC BY-SA 4.0', 'database': str(path), 'tables': result}

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--download', type=Path, help='Download all source data into this directory')
    group.add_argument('--database', type=Path, help='Inspect an existing SQLite file, read-only')
    parser.add_argument('--report', type=Path, help='Save a JSON inventory')
    args = parser.parse_args()
    databases = list(download(args.download)) if args.download else [args.database]
    reports = [inspect(p) for p in databases]
    output = json.dumps(reports, indent=2)
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(output + '\n')
    print(output)

if __name__ == '__main__':
    main()

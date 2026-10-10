#!/usr/bin/env python3
"""Create synthetic learning DBs in a new directory; never replace evidence."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import sqlite3

ROOT = Path(__file__).resolve().parent.parent
SCHEMA = 'CREATE TABLE evidence(id INTEGER PRIMARY KEY, value INTEGER NOT NULL)'


def load_seed(path):
    raw = path.read_bytes()
    if len(raw) > 16384:
        raise ValueError('seed is too large')
    seed = json.loads(raw)
    if not isinstance(seed, dict) or seed.get('schemaVersion') != 1 or seed.get('kind') != 'synthetic-sqlite-learning-seed':
        raise ValueError('unsupported seed schema')
    cases = seed.get('cases')
    if not isinstance(cases, list) or not 1 <= len(cases) <= 32:
        raise ValueError('seed needs 1..32 cases')
    seen = set()
    for row in cases:
        if not isinstance(row, dict) or set(row) != {'id', 'value'}:
            raise ValueError('each case needs only id and value')
        case_id = row['id']
        if not isinstance(case_id, str) or not re.fullmatch(r'[a-z][a-z0-9-]{0,40}', case_id) or case_id in seen:
            raise ValueError('invalid or duplicate case id')
        seen.add(case_id)
        if type(row['value']) is not int or not -1000000 <= row['value'] <= 1000000:
            raise ValueError('value must be a bounded integer')
    return cases, hashlib.sha256(raw).hexdigest()


def rebuild(seed_path, output):
    cases, seed_hash = load_seed(seed_path)
    output.mkdir()  # Existing paths are always refused, even when empty.
    records = []
    for row in cases:
        file = output / (row['id'] + '.sqlite')
        db = sqlite3.connect(str(file))
        try:
            db.execute(SCHEMA)
            db.execute('INSERT INTO evidence(id,value) VALUES (?,?)', (1, row['value']))
            db.commit()
            if db.execute('PRAGMA quick_check').fetchone() != ('ok',):
                raise ValueError('SQLite integrity check failed')
            if db.execute('SELECT id,value FROM evidence ORDER BY id').fetchall() != [(1, row['value'])]:
                raise ValueError('SQLite seed result mismatch')
        finally:
            db.close()
        data = file.read_bytes()
        records.append(dict(case=row['id'], file=file.name, bytes=len(data), sha256=hashlib.sha256(data).hexdigest(), expectedRows=[[1, row['value']]]))
    report = dict(schemaVersion=1, kind='seed-regeneration-not-historical-evidence', seedSHA256=seed_hash, sqliteVersion=sqlite3.sqlite_version, schema=SCHEMA, outputs=records, nativeWALExperimentRun=False, originalEvidenceModified=False, scope='Synthetic table contents only; byte identity with historical DBs is not promised.')
    (output / 'seed-result.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--seed', type=Path, default=ROOT / 'seeds/wal-snapshot-values.json')
    parser.add_argument('--output-dir', type=Path, required=True, help='A new path outside this delivery tree; its parent must exist')
    args = parser.parse_args()
    output = args.output_dir.resolve()
    if output == ROOT or ROOT in output.parents:
        parser.error('output must be outside the delivery tree')
    try:
        report = rebuild(args.seed, output)
    except (OSError, ValueError, sqlite3.Error) as exc:
        parser.exit(2, 'seed regeneration refused or failed: ' + str(exc) + '\n')
    print(json.dumps(dict(status='regenerated', kind=report['kind'], databases=len(report['outputs']), sqliteVersion=report['sqliteVersion'])))


if __name__ == '__main__':
    main()

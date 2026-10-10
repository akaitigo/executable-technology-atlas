"""Finite SQLite outbox experiment. No WAL reader, Kafka or external service."""
import argparse
import json
import os
import sqlite3
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

CASES = {
    'coupled': {'mode': 'coupled', 'deltas': [7, -2]},
    'separate-source-only': {'mode': 'source-only', 'deltas': [7]},
    'separate-event-only': {'mode': 'event-only', 'deltas': [7]},
    'rollback': {'mode': 'rollback', 'deltas': [7]},
    'invalid-schema': {'mode': 'invalid-schema', 'deltas': [7]},
    'replay-naive': {'mode': 'coupled', 'deltas': [7], 'crash': True, 'idempotent': False},
    'replay-idempotent': {'mode': 'coupled', 'deltas': [7], 'crash': True, 'idempotent': True},
    'empty': {'mode': 'coupled', 'deltas': []},
    'zero-delta': {'mode': 'coupled', 'deltas': [0]},
    'consumer-invalid-schema': {'mode': 'bad-payload', 'deltas': [7]},
}

def now():
    return datetime.now(timezone.utc).isoformat()

def log(folder, kind, **values):
    with (folder / 'timeline.jsonl').open('a') as f:
        f.write(json.dumps({'at': now(), 'pid': os.getpid(), 'kind': kind, **values}, ensure_ascii=False) + '\n')

def connect(folder, filename):
    db = sqlite3.connect(folder / filename, isolation_level=None)
    db.set_trace_callback(lambda sql: log(folder, 'sql', database=filename, sql=sql))
    return db

def visible(folder):
    with sqlite3.connect((folder / 'source.sqlite').as_uri() + '?mode=ro', uri=True) as db:
        return {'source': db.execute('SELECT * FROM source ORDER BY version').fetchall(),
                'outbox': db.execute('SELECT seq,event_id,version,delta,schema_version FROM outbox ORDER BY seq').fetchall()}

def produce(folder, data):
    db = connect(folder, 'source.sqlite')
    db.executescript('''PRAGMA journal_mode=DELETE;
    CREATE TABLE source(version INTEGER PRIMARY KEY, balance INTEGER NOT NULL);
    CREATE TABLE outbox(seq INTEGER PRIMARY KEY AUTOINCREMENT,event_id TEXT UNIQUE NOT NULL,
      version INTEGER NOT NULL,delta INTEGER NOT NULL,schema_version INTEGER NOT NULL CHECK(schema_version=1),payload TEXT NOT NULL);''')
    balance = 0
    for version, delta in enumerate(data['deltas'], 1):
        mode = data['mode']
        event = {'schema_version': 2 if mode == 'bad-payload' else 1, 'version': version, 'delta': delta, 'event_id': f'event-{version}'}
        balance += delta
        db.execute('BEGIN IMMEDIATE')
        if mode != 'event-only':
            db.execute('INSERT INTO source VALUES(?,?)', (version, balance))
        if mode == 'source-only':
            db.execute('COMMIT')
            log(folder, 'injected-stop', boundary='source commit before event write')
            break
        db.execute('INSERT INTO outbox(event_id,version,delta,schema_version,payload) VALUES(?,?,?,?,?)',
                   (event['event_id'], version, delta, 1, json.dumps(event)))
        log(folder, 'before-commit-other-connection', visible=visible(folder))
        if mode == 'rollback':
            db.execute('ROLLBACK')
        elif mode == 'invalid-schema':
            try:
                db.execute('INSERT INTO outbox(event_id,version,delta,schema_version,payload) VALUES(?,?,?,?,?)', ('invalid', 2, 7, 2, '{}'))
            except sqlite3.IntegrityError as error:
                log(folder, 'constraint-error', error=str(error))
                db.execute('ROLLBACK')
        else:
            db.execute('COMMIT')
        log(folder, 'after-transaction', visible=visible(folder))
        if mode == 'event-only':
            log(folder, 'injected-stop', boundary='event commit before source write')
            break
    db.close()
    db = connect(folder, 'consumer.sqlite')
    db.executescript('''PRAGMA journal_mode=DELETE;
      CREATE TABLE checkpoint(id INTEGER PRIMARY KEY CHECK(id=1), offset INTEGER NOT NULL);
      INSERT INTO checkpoint VALUES(1,0);
      CREATE TABLE effects(sequence INTEGER PRIMARY KEY,event_id TEXT NOT NULL,delta INTEGER NOT NULL);
      CREATE TABLE inbox(event_id TEXT PRIMARY KEY,payload TEXT NOT NULL);
      CREATE TABLE materialized(id INTEGER PRIMARY KEY CHECK(id=1),balance INTEGER NOT NULL);
      INSERT INTO materialized VALUES(1,0);''')
    db.close()

def consume(folder, data, crash):
    # Each child reopens saved state; offset is last applied seq (Kafka next-offset differs).
    source = sqlite3.connect((folder / 'source.sqlite').as_uri() + '?mode=ro', uri=True)
    db = connect(folder, 'consumer.sqlite')
    offset = db.execute('SELECT offset FROM checkpoint WHERE id=1').fetchone()[0]
    highwater = source.execute('SELECT coalesce(max(seq),0) FROM outbox').fetchone()[0]
    log(folder, 'consumer-start', offset=offset, highwater=highwater)
    for seq, payload in source.execute('SELECT seq,payload FROM outbox WHERE seq>? AND seq<=? ORDER BY seq', (offset, highwater)):
        event = json.loads(payload)
        log(folder, 'delivery', seq=seq, event=event)
        if event.get('schema_version') != 1 or type(event.get('delta')) is not int:
            log(folder, 'schema-blocked', seq=seq, offset=offset)
            break
        db.execute('BEGIN IMMEDIATE')
        prior = db.execute('SELECT payload FROM inbox WHERE event_id=?', (event['event_id'],)).fetchone()
        if data.get('idempotent', True) and prior:
            if prior[0] != payload:
                db.execute('ROLLBACK')
                raise ValueError('same id conflicting payload')
            log(folder, 'duplicate-no-effect', seq=seq)
        else:
            db.execute('INSERT INTO effects(event_id,delta) VALUES(?,?)', (event['event_id'], event['delta']))
            db.execute('UPDATE materialized SET balance=balance+? WHERE id=1', (event['delta'],))
            if data.get('idempotent', True):
                db.execute('INSERT INTO inbox VALUES(?,?)', (event['event_id'], payload))
        db.execute('COMMIT')
        log(folder, 'effect-committed', seq=seq, offset=offset, balance=db.execute('SELECT balance FROM materialized').fetchone()[0])
        if crash:
            log(folder, 'crash-before-checkpoint', seq=seq, offset=offset)
            os._exit(70)
        db.execute('BEGIN IMMEDIATE')
        db.execute('UPDATE checkpoint SET offset=? WHERE id=1', (seq,))
        db.execute('COMMIT')
        offset = seq
        log(folder, 'checkpoint-saved', offset=offset)
    log(folder, 'finite-consumer-end', offset=offset, highwater=highwater)
    source.close()
    db.close()

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('folder', type=Path)
    parser.add_argument('--consume', action='store_true')
    parser.add_argument('--crash', action='store_true')
    args = parser.parse_args()
    folder = args.folder.resolve()
    data = json.loads((folder / 'input.json').read_text())
    if args.consume:
        consume(folder, data, args.crash)
        return
    produce(folder, data)
    for crash in ([True, False] if data.get('crash') else [False]):
        command = [sys.executable, str(Path(__file__).resolve()), str(folder), '--consume'] + (['--crash'] if crash else [])
        result = subprocess.run(command, capture_output=True, text=True, timeout=10)
        log(folder, 'child-exit', code=result.returncode, stdout=result.stdout, stderr=result.stderr.replace(str(folder), '<case>'))
        with sqlite3.connect(folder / 'consumer.sqlite') as saved:
            log(folder, 'child-state', offset=saved.execute('SELECT offset FROM checkpoint').fetchone()[0], balance=saved.execute('SELECT balance FROM materialized').fetchone()[0], effects=saved.execute('SELECT count(*) FROM effects').fetchone()[0])
        if result.returncode != (70 if crash else 0):
            raise RuntimeError('unexpected consumer exit')

if __name__ == '__main__':
    main()

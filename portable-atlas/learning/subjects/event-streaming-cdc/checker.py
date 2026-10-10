"""Read-only independent hand oracle; does not import experiment or runner."""
import copy
import hashlib
import json
import re
import sqlite3
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parent
# source rows, source final balance, outbox rows, saved last seq, effects, sink balance, inbox
EXPECTED = {
 'coupled': (2,5,2,2,2,5,2), 'separate-source-only': (1,7,0,0,0,0,0),
 'separate-event-only': (0,0,1,1,1,7,1), 'rollback': (0,0,0,0,0,0,0),
 'invalid-schema': (0,0,0,0,0,0,0), 'replay-naive': (1,7,1,1,2,14,0),
 'replay-idempotent': (1,7,1,1,1,7,1), 'empty': (0,0,0,0,0,0,0),
 'zero-delta': (1,0,1,1,1,0,1), 'consumer-invalid-schema': (1,7,1,0,0,0,0)}

def sha(raw):
    return hashlib.sha256(raw).hexdigest()

def query(path, statements):
    db = sqlite3.connect(path.resolve().as_uri() + '?mode=ro&immutable=1', uri=True)
    db.execute('PRAGMA query_only=ON')
    assert db.execute('PRAGMA integrity_check').fetchone()[0] == 'ok'
    result = {name: db.execute(sql).fetchall() for name, sql in statements.items()}
    db.close()
    return result

def state(folder):
    a = query(folder/'source.sqlite', {'source':'SELECT * FROM source ORDER BY version',
       'outbox':'SELECT seq,event_id,version,delta,schema_version,payload FROM outbox ORDER BY seq'})
    b = query(folder/'consumer.sqlite', {'checkpoint':'SELECT offset FROM checkpoint',
       'effects':'SELECT * FROM effects ORDER BY sequence', 'materialized':'SELECT balance FROM materialized',
       'inbox':'SELECT * FROM inbox ORDER BY event_id'})
    return {**a, **b}

def summary(s):
    return (len(s['source']),s['source'][-1][1] if s['source'] else 0,len(s['outbox']),
      s['checkpoint'][0][0],len(s['effects']),s['materialized'][0][0],len(s['inbox']))

def hand_rows(name):
    # Independent small examples: each tuple enumerates an expected persisted row.
    source = [(1,7),(2,5)] if name=='coupled' else [] if name in ('empty','rollback','invalid-schema','separate-event-only') else [(1,0)] if name=='zero-delta' else [(1,7)]
    events = [(1,'event-1',1,7,1),(2,'event-2',2,-2,1)] if name=='coupled' else [] if name in ('empty','rollback','invalid-schema','separate-source-only') else [(1,'event-1',1,0,1)] if name=='zero-delta' else [(1,'event-1',1,7,1)]
    effects = [(1,'event-1',7),(2,'event-2',-2)] if name=='coupled' else [(1,'event-1',7),(2,'event-1',7)] if name=='replay-naive' else [] if name in ('empty','rollback','invalid-schema','separate-source-only','consumer-invalid-schema') else [(1,'event-1',0)] if name=='zero-delta' else [(1,'event-1',7)]
    return source, events, effects

def row_problems(name, s):
    expected_source,expected_events,expected_effects=hand_rows(name)
    problems=[]
    if s['source']!=expected_source: problems.append('source rows differ')
    if [row[:5] for row in s['outbox']]!=expected_events: problems.append('outbox rows differ')
    if s['effects']!=expected_effects: problems.append('effect rows differ')
    for seq,event_id,version,delta,schema,payload in s['outbox']:
        want={'schema_version':2 if name=='consumer-invalid-schema' else 1,'event_id':event_id,'version':version,'delta':delta}
        if json.loads(payload)!=want: problems.append('event envelope differs')
    want_inbox=[] if name=='replay-naive' else [(row[1],row[5]) for row in s['outbox']] if expected_effects else []
    if s['inbox']!=want_inbox: problems.append('inbox payload differs')
    return problems

def report(folder):
    rows=[]
    assert {p.name for p in folder.iterdir() if p.is_dir()} == set(EXPECTED), 'scenario denominator'
    for name, expected in EXPECTED.items():
        s=state(folder/name)
        timeline=[json.loads(line) for line in (folder/name/'timeline.jsonl').read_text().splitlines()]
        problems=row_problems(name,s)
        if summary(s)!=expected: problems.append('hand expectation differs')
        committed=[x for x in timeline if x['kind']=='after-transaction']
        if name in ('coupled','replay-naive','replay-idempotent','zero-delta','consumer-invalid-schema'):
            # The observer cannot see the source/outbox write currently in the uncommitted transaction.
            for i,x in enumerate(x for x in timeline if x['kind']=='before-commit-other-connection'):
                if len(x['visible']['source'])!=i or len(x['visible']['outbox'])!=i:
                    problems.append('uncommitted visibility')
        if name.startswith('replay-'):
            crashes=[x for x in timeline if x['kind']=='crash-before-checkpoint']
            starts=[x for x in timeline if x['kind']=='consumer-start']
            snapshots=[x for x in timeline if x['kind']=='child-state']
            if len(crashes)!=1 or len(starts)!=2 or starts[0]['pid']==starts[1]['pid'] or starts[1]['offset']!=0:
                problems.append('replay boundary evidence')
            if not snapshots or snapshots[0]['offset']!=0 or snapshots[0]['balance']!=7 or snapshots[0]['effects']!=1:
                problems.append('saved crash state')
            if [x['code'] for x in timeline if x['kind']=='child-exit'] != [70,0]: problems.append('child exit evidence')
        if name=='invalid-schema' and not any(x['kind']=='constraint-error' for x in timeline): problems.append('missing actual constraint error')
        if name=='consumer-invalid-schema' and not any(x['kind']=='schema-blocked' for x in timeline): problems.append('missing consumer block')
        if sum(x[2] for x in s['effects'])!=s['materialized'][0][0]: problems.append('effect sum')
        rows.append({'id':name,'expected':expected,'actual':summary(s),'matches_expected':not problems,'problems':problems,'sql_state':s})
    return {'oracle':'independent literal expectations + immutable read-only SQL + raw boundary evidence','rows':rows}

def check():
    payload=json.loads((ROOT/'observation-data.js').read_text().removeprefix('window.CDC_OBSERVATION = ').removesuffix(';\n'))
    folder=ROOT/payload['directory']
    index=json.loads((folder/'artifact-index.json').read_text())
    assert set(index)=={p.relative_to(folder).as_posix() for p in folder.rglob('*') if p.is_file() and p.name!='artifact-index.json'}, 'artifact denominator'
    for file, digest in index.items():
        assert sha((folder/file).read_bytes())==digest, f'artifact digest: {file}'
    metadata=json.loads((folder/'run.json').read_text())
    for file,digest in metadata['source_digests'].items():
        assert sha((ROOT/file).read_bytes())==digest, f'stale source: {file}'
    assert metadata['environment']['journal_mode']=='DELETE' and metadata['started_at']<=metadata['completed_at']
    for name in EXPECTED:
        raw_input=json.loads((folder/name/'input.json').read_text())
        raw_timeline=[json.loads(x) for x in (folder/name/'timeline.jsonl').read_text().splitlines()]
        assert payload['inputs'][name]==raw_input, 'UI input binding'
        assert payload['timelines'][name]==raw_timeline, 'UI timeline binding'
    actual=report(folder)
    assert all(x['matches_expected'] for x in actual['rows']), actual
    assert json.loads(json.dumps(actual))==payload['oracle'], 'UI oracle binding'
    assert payload['run']==metadata, 'UI run binding'
    sources=json.loads((ROOT/'sources.json').read_text())
    assert len(sources)>=4 and all(x['locator'] and x['binding'] for x in sources)
    for file in ('README.md','index.html','skills/atlas-event-streaming-cdc/SKILL.md'):
        text=(ROOT/file).read_text()
        for href in re.findall(r'(?:href="|\]\()([^"\)]+)', text):
            if ':' not in href and not href.startswith('#'):
                assert (ROOT/Path(file).parent/href.split('#')[0]).exists(), (file,href)
    for term in ('前提','主要概念','実務判断','限界','次の実験','原典'):
        assert term in (ROOT/'README.md').read_text() and term in (ROOT/'index.html').read_text(), term
    # Negative control: an independent literal expectation must reject a mutated sink state.
    for row in actual['rows']:
        altered=dict(row['sql_state'])
        altered['materialized']=[(999,)]
        assert summary(altered)!=tuple(row['expected'])
        if row['sql_state']['effects']:
            forged=copy.deepcopy(row['sql_state'])
            forged['effects'][0]=(forged['effects'][0][0],'wrong-event-id',forged['effects'][0][2])
            assert row_problems(row['id'],forged), 'row identity negative control'
    print(json.dumps({'cases':len(actual['rows']),'matches':True,'read_only':True,'source_binding':True,'negative_control':True}))

if __name__=='__main__':
    if len(sys.argv)==3 and sys.argv[1]=='--oracle-json':
        print(json.dumps(report(Path(sys.argv[2])),ensure_ascii=False))
    elif len(sys.argv)==1: check()
    else: raise SystemExit('usage: checker.py [--oracle-json RUN_DIRECTORY]')

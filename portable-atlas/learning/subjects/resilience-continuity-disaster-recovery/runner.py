"""Actual owned SQLite/file cycle. CLI uses an automatically cleaned temporary directory."""
import argparse,datetime,hashlib,json,platform,shutil,sqlite3,tempfile,time
from pathlib import Path
ROOT=Path(__file__).resolve().parent
def digest(obj):return hashlib.sha256(json.dumps(obj,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()).hexdigest()
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def fixture():return json.loads((ROOT/'fixture.json').read_text())
def reopen(p):
    c=sqlite3.connect(p.as_uri()+'?mode=ro&immutable=1',uri=True)
    try:return [list(r) for r in c.execute('SELECT id,value,tick FROM writes ORDER BY id')],c.execute('PRAGMA integrity_check').fetchall()[0][0]
    finally:c.close()
def cycle(case,folder):
    f=fixture()
    if case not in f['cases']:raise ValueError('unsupported-case')
    cfg=f['cases'][case];folder=Path(folder).resolve();folder.mkdir(parents=True,exist_ok=True)
    live=folder/'live.sqlite';snapshot=folder/'snapshot.sqlite';candidate=folder/'candidate.sqlite';damaged=folder/'damaged.sqlite'
    # Fixed owned filenames only; caller provides a fresh temporary directory.
    assert not live.exists() and not snapshot.exists()
    trace=[];start=time.perf_counter_ns()
    def event(name,**detail):
        trace.append({'phase':name,'elapsedNs':time.perf_counter_ns()-start,'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),**detail})
    c=sqlite3.connect(live);c.execute('CREATE TABLE writes(id INTEGER PRIMARY KEY,value TEXT NOT NULL,tick INTEGER NOT NULL)');c.commit()
    for row in f['rows'][:cfg['snapshotCount']]:c.execute('INSERT INTO writes VALUES(?,?,?)',row);c.commit();event('commit',id=row[0],tick=row[2])
    target=sqlite3.connect(snapshot);c.backup(target);target.close();event('backup')
    expectedHash=sha(snapshot);snapshotRows,integrity=reopen(snapshot)
    for row in f['rows'][cfg['snapshotCount']:cfg['latestCount']]:c.execute('INSERT INTO writes VALUES(?,?,?)',row);c.commit();event('commit-after-backup',id=row[0],tick=row[2])
    c.close();latestRows,_=reopen(live);event('latest-read',rows=latestRows)
    c=sqlite3.connect(live);c.execute('DELETE FROM writes');c.execute('INSERT INTO writes VALUES(99,?,?)',('damaged',40));c.commit();c.close()
    shutil.copyfile(live,damaged);damagedHash=sha(live);event('mutate',rows=reopen(live)[0])
    if cfg['fault']!='missing':
        shutil.copyfile(snapshot,candidate)
        if cfg['fault']=='corrupt':
            raw=bytearray(candidate.read_bytes());raw[0]^=1;candidate.write_bytes(raw)
    event('candidate',fault=cfg['fault'])
    attemptStart=time.perf_counter_ns()-start;event('restore-start')
    candidateHash=sha(candidate) if candidate.exists() else None
    reason='missing-backup' if candidateHash is None else 'digest-mismatch' if candidateHash!=expectedHash else None
    if reason is None:
        candidateRows,candidateIntegrity=reopen(candidate)
        if candidateIntegrity!='ok':reason='integrity-failed'
        else:shutil.copyfile(candidate,live);event('replace-live')
    rows,restoredIntegrity=reopen(live);event('reopen',rows=rows,integrity=restoredIntegrity)
    attemptEnd=time.perf_counter_ns()-start;event('restore-end')
    restored=reason is None
    missing=[r[0] for r in latestRows if r not in rows] if restored else None
    latestTick=latestRows[-1][2] if latestRows else 0;snapshotTick=snapshotRows[-1][2] if snapshotRows else 0
    artifacts={p.name:sha(p) for p in folder.iterdir() if p.is_file()}
    return {'schema':1,'case':case,'input':cfg,'inputDigest':digest({'config':cfg,'rows':f['rows']}),'executedAtUTC':trace[0]['utc'],'environment':{'python':platform.python_version(),'sqlite':sqlite3.sqlite_version,'system':platform.system(),'machine':platform.machine()},'snapshotRows':snapshotRows,'snapshotIntegrity':integrity,'latestRows':latestRows,'reopenedRows':rows,'reopenedIntegrity':restoredIntegrity,'expectedSnapshotHash':expectedHash,'candidateHash':candidateHash,'liveBeforeHash':damagedHash,'liveAfterHash':sha(live),'status':'restored' if restored else 'refused','reason':reason,'missingWriteIds':missing,'dataLossWrites':len(missing) if restored else None,'rpoGapSyntheticTicks':latestTick-snapshotTick if restored else None,'latestSyntheticTick':latestTick,'snapshotSyntheticTick':snapshotTick,'restoreAttemptStartNs':attemptStart,'restoreAttemptEndNs':attemptEnd,'restoreObservedNs':attemptEnd-attemptStart if restored else None,'attemptObservedNs':attemptEnd-attemptStart,'trace':trace,'artifacts':artifacts,'scope':'owned local file copy, closed connections; elapsed observed only; synthetic ticks are not clock seconds; no production DR guarantee'}
def run(case):
    with tempfile.TemporaryDirectory(prefix='atlas-dr-') as folder:return cycle(case,folder)
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--case',choices=list(fixture()['cases']),default='fresh');a=p.parse_args();print(json.dumps(run(a.case),ensure_ascii=False,indent=2))

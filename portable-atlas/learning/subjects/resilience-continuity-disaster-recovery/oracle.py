"""Independent fixed hand datasets, no runner import or shared expectations."""
import datetime,hashlib,json,sqlite3
HAND=[[1,'alpha',10],[2,'beta',20],[3,'gamma',30]]
EXPECTED={'fresh':(HAND,HAND,[],0),'stale':(HAND[:2],HAND,[3],10),'corrupt':(HAND,HAND,None,None),'missing-backup':(HAND,HAND,None,None),'empty':([],[],[],0),'stale-empty':([],HAND,[1,2,3],30)}
def audit(r,folder=None):
    snapshot,latest,missing,gap=EXPECTED[r['case']]
    assert r['snapshotRows']==snapshot and r['latestRows']==latest
    assert r['snapshotIntegrity']=='ok' and r['reopenedIntegrity']=='ok'
    refused=r['case'] in ('corrupt','missing-backup')
    assert r['status']==('refused' if refused else 'restored')
    assert r['reason']==('digest-mismatch' if r['case']=='corrupt' else 'missing-backup' if refused else None)
    expectedReopen=[[99,'damaged',40]] if refused else snapshot
    assert r['reopenedRows']==expectedReopen
    assert r['missingWriteIds']==missing and r['dataLossWrites']==(None if refused else len(missing)) and r['rpoGapSyntheticTicks']==gap
    assert r['latestSyntheticTick']==(latest[-1][2] if latest else 0) and r['snapshotSyntheticTick']==(snapshot[-1][2] if snapshot else 0)
    if refused:
        assert r['liveBeforeHash']==r['liveAfterHash'] and r['candidateHash']!=r['expectedSnapshotHash'] and r['restoreObservedNs'] is None
    else:assert r['liveAfterHash']==r['candidateHash']==r['expectedSnapshotHash']
    assert r['attemptObservedNs']==r['restoreAttemptEndNs']-r['restoreAttemptStartNs']>0
    if not refused:assert r['restoreObservedNs']==r['attemptObservedNs']
    t=r['trace'];assert all(type(x['elapsedNs']) is int for x in t)
    assert [x['elapsedNs'] for x in t]==sorted(x['elapsedNs'] for x in t)
    assert [datetime.datetime.fromisoformat(x['utc']) for x in t]==sorted(datetime.datetime.fromisoformat(x['utc']) for x in t)
    phases=['commit']*len(snapshot)+['backup']+['commit-after-backup']*(len(latest)-len(snapshot))+['latest-read','mutate','candidate','restore-start']+([] if refused else ['replace-live'])+['reopen','restore-end']
    assert [x['phase'] for x in t]==phases
    assert r['restoreAttemptStartNs']<=next(x['elapsedNs'] for x in t if x['phase']=='restore-start')<r['restoreAttemptEndNs']<=t[-1]['elapsedNs']
    assert next(x['rows'] for x in t if x['phase']=='reopen')==expectedReopen
    if folder is not None:
        assert {p.name for p in folder.iterdir() if p.is_file()}==set(r['artifacts'])
        for name,value in r['artifacts'].items():assert hashlib.sha256((folder/name).read_bytes()).hexdigest()==value
        assert r['artifacts']['snapshot.sqlite']==r['expectedSnapshotHash'] and r['artifacts']['live.sqlite']==r['liveAfterHash']
        for name,expected in [('snapshot.sqlite',snapshot),('live.sqlite',expectedReopen),('damaged.sqlite',[[99,'damaged',40]])]:
            c=sqlite3.connect((folder/name).resolve().as_uri()+'?mode=ro&immutable=1',uri=True)
            try:assert [list(x) for x in c.execute('SELECT id,value,tick FROM writes ORDER BY id')]==expected;assert c.execute('PRAGMA integrity_check').fetchone()[0]=='ok'
            finally:c.close()
    return {'validScenario':True,'status':r['status'],'restoredIds':[x[0] for x in expectedReopen],'missingWriteIds':missing,'rpoGapSyntheticTicks':gap,'timeScope':'local observed only'}

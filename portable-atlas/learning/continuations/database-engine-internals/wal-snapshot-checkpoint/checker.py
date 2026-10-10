#!/usr/bin/env python3
import hashlib,json,pathlib,sqlite3,sys
ROOT=pathlib.Path(__file__).resolve().parent
def check(run):
    d=json.loads((run/'result.json').read_text()); a=json.loads((run/'artifacts.json').read_text())
    for n,h in a.items():
        b=(run/n).read_bytes(); assert len(b)==h['bytes'] and hashlib.sha256(b).hexdigest()==h['sha256'],n
    for n,h in d['sourceHashes'].items(): assert hashlib.sha256((ROOT/n).read_bytes()).hexdigest()==h,n
    assert [json.loads(s) for s in (run/'stdout.ndjson').read_text().splitlines()]==d['cases'],'stdout'
    specs=[('passive','PASSIVE',10,20,1,0),('full','FULL',10,20,1,1),('truncate','TRUNCATE',10,20,1,1),('begin-only','PASSIVE',20,20,1,0),('rollback','PASSIVE',10,10,0,0),('two-commits','PASSIVE',10,30,2,0)]
    assert [c['id'] for c in d['cases']]==[s[0] for s in specs]
    for c,(name,mode,held,fresh,count,busy) in zip(d['cases'],specs):
        t={e['label']:e for e in c['trace']}; assert c['mode']==mode
        labels=['page-size','journal','writer-auto','writer-timeout','writer-sync','reader-auto','reader-timeout','reader-sync','create','seed','baseline','reader-begin']
        if name!='begin-only': labels+=['old']
        for i in range(2 if name=='two-commits' else 1): labels+=['writer-begin-'+str(i),'update-'+str(i),'writer-end-'+str(i)]
        labels+=['held','checkpoint-held','reader-end','fresh','checkpoint-ended','cleanup-truncate','compile','source-id']
        assert [e['label'] for e in c['trace']]==labels,'sequence'
        fixed={'page-size':'PRAGMA page_size=4096','journal':'PRAGMA journal_mode=WAL','create':'CREATE TABLE item(id INTEGER PRIMARY KEY, value INTEGER NOT NULL)','seed':'INSERT INTO item VALUES(1,10)','baseline':'PRAGMA wal_checkpoint(TRUNCATE)','reader-begin':'BEGIN','old':'SELECT value FROM item WHERE id=1','held':'SELECT value FROM item WHERE id=1','reader-end':'COMMIT','fresh':'SELECT value FROM item WHERE id=1','checkpoint-held':'PRAGMA wal_checkpoint('+mode+')','checkpoint-ended':'PRAGMA wal_checkpoint('+mode+')','cleanup-truncate':'PRAGMA wal_checkpoint(TRUNCATE)','compile':'PRAGMA compile_options','source-id':'SELECT sqlite_source_id()'}
        for role in ['writer','reader']:
            fixed[role+'-auto']='PRAGMA wal_autocheckpoint=0'; fixed[role+'-timeout']='PRAGMA busy_timeout=50'; fixed[role+'-sync']='PRAGMA synchronous=FULL'
        for i in range(2 if name=='two-commits' else 1):
            fixed['writer-begin-'+str(i)]='BEGIN IMMEDIATE'; fixed['update-'+str(i)]='UPDATE item SET value='+str(20+10*i)+' WHERE id=1'; fixed['writer-end-'+str(i)]='ROLLBACK' if name=='rollback' else 'COMMIT'
        assert all(e['sql']==fixed[e['label']] for e in c['trace']),'exact SQL'
        assert t['reader-begin']['beforeTransaction'] is False and t['reader-begin']['afterTransaction'] is True
        assert t['reader-end']['beforeTransaction'] is True and t['reader-end']['afterTransaction'] is False
        for e in c['trace']:
            assert e['connection']==('reader' if e['label'] in ['reader-auto','reader-timeout','reader-sync','reader-begin','old','held','reader-end','fresh'] else 'writer'),'connection'
            assert e['utc'] and e['wal']['capturedUtc']
            w=e['wal']; assert w['bytes']==(32+len(w['physicalFrames'])*(24+w['pageSize']) if w['physicalFrames'] else 0),'WAL layout'
            p=run/name/(e['label']+'.wal')
            if w['bytes']: assert p.stat().st_size==w['bytes'] and hashlib.sha256(p.read_bytes()).hexdigest()==w['sha256']
        assert t['journal']['rows']==[['wal']]
        assert t['baseline']['rows']==[[0,0,0]]
        for role in ['writer','reader']:
            assert t[role+'-auto']['rows']==[[0]] and t[role+'-timeout']['rows']==[[50]]
        if name!='begin-only': assert t['old']['rows']==[[10]] and t['old']['afterTransaction']
        assert t['held']['sql']=='SELECT value FROM item WHERE id=1' and t['held']['rows']==[[held]] and t['held']['afterTransaction'],'snapshot literal'
        assert t['fresh']['rows']==[[fresh]] and not t['fresh']['afterTransaction'],'fresh literal'
        for i in range(2 if name=='two-commits' else 1):
            assert t['update-'+str(i)]['sql']=='UPDATE item SET value='+str(20+10*i)+' WHERE id=1'
            assert t['writer-end-'+str(i)]['sql']==('ROLLBACK' if name=='rollback' else 'COMMIT')
        progress=count if name=='begin-only' else 0
        assert t['checkpoint-held']['sql']=='PRAGMA wal_checkpoint('+mode+')'
        assert t['checkpoint-held']['rows']==[[busy,count,progress]],'held checkpoint literal'
        assert len(t['checkpoint-held']['wal']['physicalFrames'])==count
        assert t['checkpoint-ended']['rows']==([[0,0,0]] if mode=='TRUNCATE' else [[0,count,count]]),'ended checkpoint literal'
        assert t['cleanup-truncate']['rows']==[[0,0,0]] and t['cleanup-truncate']['wal']['bytes']==0
        assert c['compileOptions']==t['compile']['rows'] and c['sourceId']==t['source-id']['rows']
        p=run/name/'closed.sqlite'; assert hashlib.sha256(p.read_bytes()).hexdigest()==c['closedDbSha256']
        con=sqlite3.connect(p.as_uri()+'?mode=ro&immutable=1',uri=True); con.execute('PRAGMA query_only=ON')
        assert con.execute('SELECT id,value FROM item').fetchall()==[(1,fresh)]; con.close()
    return d
if __name__=='__main__':
    check(ROOT/(ROOT/'CURRENT').read_text().strip()); print('PASS 6 fixed sequences, literal snapshot/checkpoint oracle, closed DB, hashes')

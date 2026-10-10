#!/usr/bin/env python3
import hashlib,json,pathlib,sqlite3,sys
ROOT=pathlib.Path(__file__).resolve().parent
# 独立の事前literal契約。producer、migration実装、app moduleをimportしない。
MATRIX={'v1':{'v1':(0,[[1,'Ada']],None),'v2':(3,None,'no such column: display_name')},'additive':{'v1':(0,[[1,'Ada']],None),'v2':(0,[[1,'Ada-v2']],None)},'rename':{'v1':(3,None,'no such column: name'),'v2':(0,[[1,'Ada-v2']],None)}}
COLS={'v1':['id','name'],'additive':['id','name','display_name'],'rename':['id','display_name']}
ROWS={'v1':[[1,'Ada']],'additive':[[1,'Ada','Ada-v2']],'rename':[[1,'Ada-v2']]}
MIG={'v1':[],'additive':["ALTER TABLE person ADD COLUMN display_name TEXT NOT NULL DEFAULT ''","UPDATE person SET display_name=name || '-v2'"],'rename':['ALTER TABLE person RENAME COLUMN name TO display_name',"UPDATE person SET display_name=display_name || '-v2'"]}
SEED=['CREATE TABLE person(id INTEGER PRIMARY KEY, name TEXT NOT NULL)',"INSERT INTO person VALUES(1,'Ada')"]
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def snapshot(db,schema,saved):
    c=sqlite3.connect(db.resolve().as_uri()+'?mode=ro&immutable=1',uri=True);c.execute('PRAGMA query_only=ON');info=[list(x) for x in c.execute('PRAGMA table_info(person)')];rows=[list(x) for x in c.execute('SELECT * FROM person ORDER BY id')];sql=c.execute("SELECT sql FROM sqlite_schema WHERE name='person'").fetchone()[0];c.close()
    assert [x[1] for x in info]==COLS[schema] and rows==ROWS[schema],'database literal'
    assert saved=={'schemaSql':sql,'columns':info,'rows':rows,'dbSha256':digest(db)},'snapshot binding'
def sqltrace(trace,expected):
    assert [e['sql'] for e in trace]==expected,'SQL sequence';assert all(e['exitCode']==0 and e['rows']==[] and e['startedUtc']<=e['endedUtc'] for e in trace)
def reader(cmd,v,schema,artifact,db):
    code,rows,error=MATRIX[schema][v];assert cmd['argv']==['python3','-B',artifact,db],'reader artifact routing'
    assert cmd['exitCode']==code,'reader exit';p=json.loads(cmd['stdout']);assert p==cmd['parsed'],'raw binding';assert not cmd['stderr']
    assert p['version']==v and p['sql']==('SELECT id, name FROM person ORDER BY id' if v=='v1' else 'SELECT id, display_name FROM person ORDER BY id')
    if code==0:assert p['rows']==rows and 'error' not in p,'reader rows'
    else:assert p['error']==error and p['errorClass']=='OperationalError' and 'rows' not in p,'actual SQL error'
def check(run):
    a=json.loads((run/'artifacts.json').read_text());d=json.loads((run/'result.json').read_text());assert json.loads((run/'stdout.json').read_text())==d
    for n,h in a.items():assert (run/n).stat().st_size==h['bytes'] and digest(run/n)==h['sha256'],n
    for n,h in d['sourceHashes'].items():assert digest(ROOT/n)==h,n
    assert digest(run/'health.py')==digest(ROOT/'health.py'),'health executable bytes'
    assert digest(run/'inputs.json')==digest(ROOT/'compatibility.json'),'prior input table bytes'
    inputs=json.loads((run/'inputs.json').read_text())
    assert inputs['fixture']==[[1,'Ada']]
    expected={s:{v:dict(exit=code,**({'rows':rows} if code==0 else {'error':error})) for v,(code,rows,error) in apps.items()} for s,apps in MATRIX.items()};assert inputs['matrix']==expected,'independent matrix'
    for v in ['v1','v2']:
        art=d['artifacts'][v];assert digest(run/art['path'])==art['sha256']==digest(ROOT/('app_'+v+'.py')) and (run/art['path']).stat().st_size==art['bytes'],'stored artifact bytes'
    assert [m['schema'] for m in d['matrix']]==['v1','additive','rename']
    for m in d['matrix']:
        s=m['schema'];sqltrace(m['sqlTrace'],SEED+MIG[s]);snapshot(run/('matrix-'+s)/'data.sqlite',s,m['snapshot'])
        for v in ['v1','v2']:reader(m['reads'][v],v,s,d['artifacts'][v]['path'],'matrix-'+s+'/data.sqlite')
    assert [x['schema'] for x in d['releases']]==['additive','rename']
    for rel in d['releases']:
        s=rel['schema'];folder=run/('release-'+s);t=rel['trace'];assert [e['event'] for e in t]==['before','migration','promotion','v2-read','synthetic-health-failure','artifact-rollback','v1-read','after'],'release sequence';sqltrace(rel['seedTrace'],SEED);sqltrace(t[1]['sqlTrace'],MIG[s]);snapshot(folder/'before.sqlite','v1',t[0]['database']);snapshot(folder/'migrated.sqlite',s,t[1]['database']);snapshot(folder/'after.sqlite',s,t[7]['database']);snapshot(folder/'data.sqlite',s,t[7]['database'])
        assert digest(folder/'before.sqlite')!=digest(folder/'after.sqlite'),'migration changed DB'
        assert digest(folder/'migrated.sqlite')==digest(folder/'after.sqlite')==t[5]['databaseSha256'],'pointer rollback must not restore DB'
        v1={'sha256':d['artifacts']['v1']['sha256']};v2={'sha256':d['artifacts']['v2']['sha256']}
        assert t[0]['active']==t[5]['active']==t[7]['active']==v1 and t[2]['active']==v2,'active digest'
        for n,e in [('pointer-before.json',v1),('pointer-promoted.json',v2),('pointer-restored.json',v1),('active.json',v1)]:assert json.loads((folder/n).read_text())==e
        reader(t[3]['command'],'v2',s,d['artifacts']['v2']['path'],'release-'+s+'/data.sqlite');reader(t[6]['command'],'v1',s,d['artifacts']['v1']['path'],'release-'+s+'/data.sqlite')
        h=t[4]['command'];assert h['argv']==['python3','-B','health.py'] and h['exitCode']==42 and h['parsed']==json.loads(h['stdout'])=={'kind':'synthetic-health-failure','reason':'fixed fixture: canary alarm; no service/provider probe','healthy':False} and not h['stderr'],'synthetic health separate'
        assert rel['artifactRestored'] is True and rel['databaseRestored'] is False
        assert rel['v1ReadExit']==MATRIX[s]['v1'][0] and rel['v1ReadSucceeded']==(s=='additive'),'rollback compatibility'
    return d
if __name__=='__main__':check(ROOT/(ROOT/'CURRENT').read_text().strip());print('PASS independent 6-cell app/schema matrix; 2 release flows; real closed DB and raw/digest binding')

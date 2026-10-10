"""Independent Python frame-set enumeration plus literal anchors. No SUM SQL rerun."""
import argparse,hashlib,json,re,sqlite3,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parent
BASE=[[3,'A',2,5],[2,'A',1,20],[1,'A',1,10],[5,'B',2,None],[4,'B',1,7]]
FIXTURES={'peers':BASE,'null-sort':[[3,'A',1,5],[2,'A',None,20],[1,'A',None,10]],'null-amounts':[[1,'A',1,None],[2,'A',1,None],[3,'A',2,None]],'negative-amounts':[[1,'A',1,10],[2,'A',1,-10],[3,'A',2,4]],'no-peers':[[1,'A',1,10],[2,'A',2,20],[3,'A',3,5]],'singleton':[[9,'Z',None,None]],'empty-partition':BASE,'null-partition':[[3,'A',1,9],[2,None,1,7],[1,None,1,5]],'negative-sort':[[3,'A',0,5],[2,'A',-1,20],[1,'A',-1,10]],'range-tie-breaker':BASE,'invalid-start-end':BASE,'invalid-negative':BASE}
FRAMES={'range-default':'PARTITION BY part ORDER BY sort_key','rows-explicit':'PARTITION BY part ORDER BY sort_key,id ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW','range-explicit':'PARTITION BY part ORDER BY sort_key RANGE BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW','range-with-id':'PARTITION BY part ORDER BY sort_key,id RANGE BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW','invalid-start-end':'PARTITION BY part ORDER BY sort_key,id ROWS BETWEEN CURRENT ROW AND 1 PRECEDING','invalid-negative':'PARTITION BY part ORDER BY sort_key,id ROWS BETWEEN -1 PRECEDING AND CURRENT ROW'}
COLUMNS=['id','part','sort_key','amount','total','known_values','frame_ids_raw']
SCHEMA='CREATE TABLE samples(id INTEGER NOT NULL UNIQUE, part TEXT, sort_key INTEGER, amount INTEGER)'
def sha(b):return 'sha256:'+hashlib.sha256(b).hexdigest()
def read(p):return json.loads(p.read_text())
def sortkey(value):return (value is not None,value if value is not None else 0)
def enumerate_frames(rows,mode):
    ordered=sorted(rows,key=lambda r:(sortkey(r[1]),sortkey(r[2]),r[0]));out=[]
    for row in ordered:
        group=[r for r in ordered if r[1]==row[1]]
        if mode in ('rows-explicit','range-with-id'):frame=group[:next(i for i,r in enumerate(group) if r[0]==row[0])+1]
        else:frame=[r for r in group if sortkey(r[2])<=sortkey(row[2])]
        known=[r[3] for r in frame if r[3] is not None];out.append({'id':row[0],'part':row[1],'sort_key':row[2],'amount':row[3],'frame_ids':sorted(r[0] for r in frame),'total':sum(known) if known else None,'known_values':len(known)})
    return out
# Hand anchors guard the independent algorithm itself, not a second SQL invocation.
ANCHORS={('peers','range-default',1):([1,2],30),('peers','rows-explicit',1):([1],10),('peers','range-default',3):([1,2,3],35),('null-sort','range-default',1):([1,2],30),('null-sort','rows-explicit',1):([1],10),('null-amounts','range-default',1):([1,2],None),('negative-amounts','range-default',1):([1,2],0),('negative-amounts','rows-explicit',1):([1],10),('singleton','range-default',9):([9],None),('null-partition','range-default',1):([1,2],12),('range-tie-breaker','range-with-id',1):([1],10)}
def oracle(folder):
    obs=read(folder/'observation.json');assert {r['id'] for r in obs['runs']}==set(FIXTURES) and len(obs['runs'])==12,'case set';reports=[];anchors_seen=set()
    for run in obs['runs']:
        key=run['id'];case=folder/key;request=read(case/'input.json');result=read(case/'result.json');command=read(case/'command.json');trace=read(case/'trace.json');db=case/'fixture.sqlite3';before=db.read_bytes()
        modes=[key] if key.startswith('invalid') else ['range-default','rows-explicit','range-explicit']+(['range-with-id'] if key=='range-tie-breaker' else []);filter_value='missing' if key=='empty-partition' else None
        assert request=={'rows':FIXTURES[key],'filter':filter_value,'modes':modes},'fixed fixture input'
        connection=sqlite3.connect(db.resolve().as_uri()+'?mode=ro&immutable=1',uri=True)
        try:
            connection.execute('PRAGMA query_only=ON');assert connection.execute('PRAGMA query_only').fetchone()[0]==1
            physical=[list(r) for r in connection.execute('SELECT id,part,sort_key,amount FROM samples ORDER BY rowid')];schema=connection.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='samples'").fetchone()[0]
        finally:connection.close()
        assert physical==FIXTURES[key] and schema==SCHEMA,'saved DB rows/schema';assert before==db.read_bytes(),'oracle wrote DB'
        created=read(case/'database-created.json');assert created['schema']==SCHEMA and created['rows_in_insertion_order']==physical and created['db_digest']==sha(before),'DB creation record'
        assert command['exit_code']==run['exit_code']==0 and command['stderr']=='','command success'
        assert json.loads(command['stdin'])=={'modes':modes,'filter':filter_value},'SQL request'
        for stream in ('stdin','stdout','stderr'):assert sha(command[stream].encode())==command[stream+'_digest'],'raw stream digest'
        assert trace==[json.loads(line) for line in command['stdout'].splitlines()],'raw trace'
        assert result['query_only']==1 and result['db_digest_before']==result['db_digest_after']==sha(before),'read-only DB binding'
        assert result['sqlite_version']==obs['environment']['sqlite'],'SQLite identity';assert len(result['observations'])==len(modes),'query count'
        expected_trace=[{'event':'database-opened','sqlite_version':result['sqlite_version'],'query_only':1,'db_digest':sha(before)}]
        for mode,sqlobs in zip(modes,result['observations']):
            where=' WHERE part = ?' if filter_value is not None else '';sql='SELECT id,part,sort_key,amount,SUM(amount) OVER w AS total,COUNT(amount) OVER w AS known_values,GROUP_CONCAT(id) OVER w AS frame_ids_raw FROM samples'+where+' WINDOW w AS ('+FRAMES[mode]+') ORDER BY part,sort_key,id'
            assert sqlobs['mode']==mode and sqlobs['sql']==sql and sqlobs['params']==([filter_value] if where else []),'SQL/order contract'
            expected_trace.append({'event':'query-observed',**sqlobs})
            if mode.startswith('invalid'):
                assert sqlobs['outcome']=='error' and sqlobs['rows']==sqlobs['raw_rows']==sqlobs['columns']==[],'invalid frame accepted'
                assert sqlobs['error']['class']=='OperationalError','invalid frame error class';expected_message='unsupported frame specification' if mode=='invalid-start-end' else 'frame starting offset must be a non-negative integer';assert sqlobs['error']['message']==expected_message,'invalid frame cause'
                reports.append({'id':key,'mode':mode,'outcome':'error','error':sqlobs['error'],'rows':[]});continue
            selected=[r for r in physical if filter_value is None or r[1]==filter_value];expected=enumerate_frames(selected,mode)
            assert sqlobs['outcome']=='rows' and sqlobs['error'] is None and sqlobs['columns']==COLUMNS,'normal result'
            assert len(sqlobs['rows'])==len(sqlobs['raw_rows'])==len(expected),'result count/order'
            for actual,raw_row,hand in zip(sqlobs['rows'],sqlobs['raw_rows'],expected):
                assert dict(zip(COLUMNS,raw_row))=={k:actual[k] for k in COLUMNS},'raw columns/rows'
                ids=[int(i) for i in actual['frame_ids_raw'].split(',')] if actual['frame_ids_raw'] else [];assert len(ids)==len(set(ids)) and sorted(ids)==actual['frame_ids'],'raw frame set'
                assert {k:actual[k] for k in hand}==hand,'independent frame set/sum/order mismatch'
                anchor=(key,mode,hand['id'])
                if anchor in ANCHORS:assert (hand['frame_ids'],hand['total'])==ANCHORS[anchor],'literal anchor';anchors_seen.add(anchor)
            reports.append({'id':key,'mode':mode,'outcome':'rows','error':None,'rows':expected})
        expected_trace.append({'event':'database-closed','db_digest':sha(before),'unchanged':True});assert trace==expected_trace,'actual SQL trace'
    assert len(reports)==33 and anchors_seen==set(ANCHORS),'query/anchor coverage'
    return {'passed':True,'cases':12,'queries':33,'literal_anchors':len(ANCHORS),'independence':'Python frame membership from saved input SELECT only; literal anchors; no SUM/window SQL rerun and no producer import','reports':reports}
def check():
    folder=ROOT/read(ROOT/'current.json')['directory'];obs=read(folder/'observation.json')
    for n,d in obs['source_bindings'].items():assert sha((ROOT/n).read_bytes())==d,'stale source '+n
    index=read(folder/'artifact-index.json');assert set(index)=={p.relative_to(folder).as_posix() for p in folder.rglob('*') if p.is_file() and p.name!='artifact-index.json'},'artifact set'
    for n,e in index.items():
        b=(folder/n).read_bytes();assert e=={'digest':sha(b),'size':len(b)},'artifact digest '+n
    assert oracle(folder)==read(folder/'oracle.json'),'saved oracle differs';print(json.dumps({'passed':True,'cases':12,'queries':33,'literal_anchors':11,'read_only':True}))
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--oracle');args=p.parse_args()
    try:
        if args.oracle:
            assert re.fullmatch(r'(observations/[0-9TZ]+|oracle-negative-[a-zA-Z0-9_-]+)',args.oracle),'oracle path';print(json.dumps(oracle(ROOT/args.oracle),ensure_ascii=False))
        else:check()
    except (AssertionError,KeyError,ValueError,OSError) as exc:print(str(exc),file=sys.stderr);raise SystemExit(1)

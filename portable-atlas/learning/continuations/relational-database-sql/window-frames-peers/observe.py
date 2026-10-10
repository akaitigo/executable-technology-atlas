"""Read-only SQL observations of a previously saved local SQLite fixture."""
import hashlib,json,sqlite3,sys
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parent
COLUMNS=['id','part','sort_key','amount','total','known_values','frame_ids_raw']
def sha(b):return 'sha256:'+hashlib.sha256(b).hexdigest()
def now():return datetime.now(timezone.utc).isoformat()
def emit(event,**fields):print(json.dumps({'event':event,**fields},ensure_ascii=False),flush=True)
def run(db,request):
    before=sha(db.read_bytes());connection=sqlite3.connect(db.resolve().as_uri()+'?mode=ro&immutable=1',uri=True);observations=[]
    try:
        connection.execute('PRAGMA query_only=ON');guard=connection.execute('PRAGMA query_only').fetchone()[0];templates=json.loads((ROOT/'queries.json').read_text());emit('database-opened',sqlite_version=sqlite3.sqlite_version,query_only=guard,db_digest=before)
        for mode in request['modes']:
            frame=templates[mode];where=' WHERE part = ?' if request['filter'] is not None else '';params=[request['filter']] if where else []
            sql='SELECT id,part,sort_key,amount,SUM(amount) OVER w AS total,COUNT(amount) OVER w AS known_values,GROUP_CONCAT(id) OVER w AS frame_ids_raw FROM samples'+where+' WINDOW w AS ('+frame+') ORDER BY part,sort_key,id'
            started=now()
            try:
                cursor=connection.execute(sql,params);columns=[c[0] for c in cursor.description];raw_rows=[list(r) for r in cursor.fetchall()];rows=[]
                for values in raw_rows:
                    row=dict(zip(columns,values));row['frame_ids']=sorted(int(i) for i in row['frame_ids_raw'].split(',')) if row['frame_ids_raw'] else [];rows.append(row)
                observation={'mode':mode,'sql':sql,'params':params,'started_at':started,'completed_at':now(),'outcome':'rows','columns':columns,'raw_rows':raw_rows,'rows':rows,'error':None}
            except sqlite3.OperationalError as exc:
                observation={'mode':mode,'sql':sql,'params':params,'started_at':started,'completed_at':now(),'outcome':'error','columns':[],'raw_rows':[],'rows':[],'error':{'class':type(exc).__name__,'message':str(exc)}}
            observations.append(observation);emit('query-observed',**observation)
    finally:connection.close()
    after=sha(db.read_bytes());emit('database-closed',db_digest=after,unchanged=before==after)
    return {'sqlite_version':sqlite3.sqlite_version,'query_only':guard,'db_digest_before':before,'db_digest_after':after,'observations':observations}
if __name__=='__main__':
    request=json.load(sys.stdin);result=run(Path(sys.argv[1]),request);Path(sys.argv[2]).write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')

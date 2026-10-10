import sqlite3,json,sys,platform
from pathlib import Path
P=Path(__file__).resolve().parent
TABLE='CREATE TABLE samples(id INTEGER PRIMARY KEY, bucket INTEGER, label TEXT COLLATE BINARY, payload TEXT)'
INDEX='CREATE INDEX samples_bucket_label_idx ON samples(bucket, label)'
def validate(x):
 if type(x)!=dict or set(x)!={'bucket','projection','order'}:raise ValueError('FIELDS')
 b=x['bucket']
 if b is not None and (type(b)!=int or b not in list(range(8))+[99]):raise ValueError('BUCKET')
 if type(x['projection'])!=str or x['projection'] not in ['index','payload']:raise ValueError('PROJECTION')
 if type(x['order'])!=str or x['order'] not in ['asc','desc']:raise ValueError('ORDER')
 return x
def classify(plan):
 details=[row[3] for row in plan]
 if any('USING COVERING INDEX samples_bucket_label_idx' in text for text in details):return 'COVERING_REPORTED'
 if any('USING INDEX samples_bucket_label_idx' in text for text in details):return 'INDEX_TABLE_LOOKUP_REPORTED'
 return 'OTHER_OR_UNRECOGNIZED'
def run(x,fail=False):
 validate(x);db=None;statements=[];trace=[];r=dict(status='OBSERVED',input_echo=x,selected_projection=x['projection'],db_opened=False,queries={})
 try:
  db=sqlite3.connect(':memory:');r['db_opened']=True;db.set_trace_callback(statements.append);trace.append(dict(stage='connect',database=':memory:'))
  db.execute(TABLE);source=json.loads((P/'rows.json').read_text());db.executemany('INSERT INTO samples(id,bucket,label,payload) VALUES (?,?,?,?)',[(v['id'],v['bucket'],v['label'],v['payload']) for v in source]);db.execute(INDEX);db.commit();r['environment']=dict(system=platform.system(),python=platform.python_version(),sqlite_module_version=sqlite3.sqlite_version,sqlite_version=db.execute('SELECT sqlite_version()').fetchone()[0],source_id=db.execute('SELECT sqlite_source_id()').fetchone()[0],compile_options=sorted(row[0] for row in db.execute('PRAGMA compile_options')))
  r['schema']=[list(v) for v in db.execute("SELECT type,name,tbl_name,sql FROM sqlite_master WHERE name NOT LIKE 'sqlite_%' ORDER BY type,name")];r['table_info']=[list(v) for v in db.execute('PRAGMA table_info(samples)')];r['index_list']=[list(v) for v in db.execute('PRAGMA index_list(samples)')];r['index_xinfo']=[list(v) for v in db.execute('PRAGMA index_xinfo(samples_bucket_label_idx)')]
  r['loaded_rows']=[dict(zip(['id','bucket','label','payload'],v)) for v in db.execute('SELECT id,bucket,label,payload FROM samples ORDER BY id')];r['row_count']=len(r['loaded_rows']);trace.append(dict(stage='load_fixture',rows=r['row_count']));trace.append(dict(stage='create_index',name='samples_bucket_label_idx',index_xinfo=r['index_xinfo']))
  if fail:raise RuntimeError('INJECTED_PRODUCER_FAILURE')
  for name,cols in [('index',['bucket','label']),('payload',['bucket','label','payload'])]:
   where='bucket IS NULL' if x['bucket'] is None else 'bucket = ?';direction=x['order'].upper();sql='SELECT '+', '.join(cols)+' FROM samples WHERE '+where+' ORDER BY label '+direction+', id '+direction;params=[] if x['bucket'] is None else [x['bucket']]
   plan=[list(v) for v in db.execute('EXPLAIN QUERY PLAN '+sql,params)];cursor=db.execute(sql,params);columns=[v[0] for v in cursor.description];rows=[list(v) for v in cursor.fetchall()];pc=classify(plan);missing=[] if name=='index' else ['payload'];q=dict(sql=sql,params=params,columns=columns,rows=rows,row_count=len(rows),eqp_raw=plan,plan_class=pc,schema_cover_possible=not missing,missing_projection=missing,plan_contract_consistent=pc!='COVERING_REPORTED' or not missing);r['queries'][name]=q;trace.append(dict(stage='query_'+name,sql=sql,params=params,rows=len(rows),plan_class=pc))
  observed=r['queries']['index']['plan_class']=='COVERING_REPORTED' and r['queries']['payload']['plan_class']=='INDEX_TABLE_LOOKUP_REPORTED';r['comparison_status']='COMPARISON_OBSERVED' if observed else 'COMPARISON_NOT_ESTABLISHED'
 except Exception as e:r['status']='EXECUTION_FAILED';r['reason']=type(e).__name__;trace.append(dict(stage='exception',name=type(e).__name__))
 finally:
  if db is not None:
   db.close();error=None
   try:db.execute('SELECT 1')
   except sqlite3.ProgrammingError as e:error=type(e).__name__
   r['cleanup']=dict(closed=True,post_close_error=error);trace.append(dict(stage='close_connection',post_close_error=error))
  else:r['cleanup']=dict(closed=False,post_close_error=None)
 r['trace']=trace;r['sqlite_trace']=statements;return r
if __name__=='__main__':
 try:
  x=validate(json.load(sys.stdin))
  if sys.argv[1:] not in [[],['--fail']]:raise ValueError('ARGUMENT')
 except (ValueError,TypeError) as e:print(json.dumps(dict(status='INPUT_REFUSED',reason=str(e),db_opened=False)));sys.exit(2)
 r=run(x,sys.argv[1:]==['--fail']);print(json.dumps(r));sys.exit(0 if r['status']=='OBSERVED' else 3)

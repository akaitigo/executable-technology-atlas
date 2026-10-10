"""Independent fresh SQLite replay; no producer helpers."""
import sqlite3,json,platform
from pathlib import Path
P=Path(__file__).resolve().parent
TABLE='CREATE TABLE samples(id INTEGER PRIMARY KEY, bucket INTEGER, label TEXT COLLATE BINARY, payload TEXT)'
INDEX='CREATE INDEX samples_bucket_label_idx ON samples(bucket, label)'
def audit(r,x):
 rows=json.loads((P/'rows.json').read_text());db=sqlite3.connect(':memory:');trace=[];db.set_trace_callback(trace.append)
 try:
  db.execute(TABLE);db.executemany('INSERT INTO samples(id,bucket,label,payload) VALUES (?,?,?,?)',[(v['id'],v['bucket'],v['label'],v['payload']) for v in rows]);db.execute(INDEX);db.commit()
  assert r['environment']==dict(system=platform.system(),python=platform.python_version(),sqlite_module_version=sqlite3.sqlite_version,sqlite_version=db.execute('SELECT sqlite_version()').fetchone()[0],source_id=db.execute('SELECT sqlite_source_id()').fetchone()[0],compile_options=sorted(v[0] for v in db.execute('PRAGMA compile_options')))
  assert r['schema']==[list(v) for v in db.execute("SELECT type,name,tbl_name,sql FROM sqlite_master WHERE name NOT LIKE 'sqlite_%' ORDER BY type,name")]
  assert r['table_info']==[list(v) for v in db.execute('PRAGMA table_info(samples)')];assert r['index_list']==[list(v) for v in db.execute('PRAGMA index_list(samples)')];assert r['index_xinfo']==[list(v) for v in db.execute('PRAGMA index_xinfo(samples_bucket_label_idx)')]
  assert r['loaded_rows']==[dict(zip(['id','bucket','label','payload'],v)) for v in db.execute('SELECT id,bucket,label,payload FROM samples ORDER BY id')]
  expected=[dict(stage='connect',database=':memory:'),dict(stage='load_fixture',rows=256),dict(stage='create_index',name='samples_bucket_label_idx',index_xinfo=r['index_xinfo'])]
  if r['status']=='OBSERVED':
   for name in ['index','payload']:
    q=r['queries'][name];assert q['eqp_raw']==[list(v) for v in db.execute('EXPLAIN QUERY PLAN '+q['sql'],q['params'])];cur=db.execute(q['sql'],q['params']);assert q['columns']==[v[0] for v in cur.description] and q['rows']==[list(v) for v in cur.fetchall()];expected.append(dict(stage='query_'+name,sql=q['sql'],params=q['params'],rows=q['row_count'],plan_class=q['plan_class']))
  else:assert r['reason']=='RuntimeError' and r['queries']=={};expected.append(dict(stage='exception',name='RuntimeError'))
  expected.append(dict(stage='close_connection',post_close_error='ProgrammingError'));assert r['trace']==expected;assert r['sqlite_trace']==trace
 finally:db.close()
 try:db.execute('SELECT 1')
 except sqlite3.ProgrammingError:return True
 raise AssertionError('fresh DB not closed')

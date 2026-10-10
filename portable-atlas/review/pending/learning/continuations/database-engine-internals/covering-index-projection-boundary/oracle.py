import json,sys
from pathlib import Path
P=Path(__file__).resolve().parent;ROWS=json.loads((P/'rows.json').read_text());HAND=json.loads((P/'hand-table.json').read_text())
def expected(x,projection):
 rows=[r for r in ROWS if r['bucket']==x['bucket']];rows.sort(key=lambda r:(r['label'] is not None,r['label'] or '',r['id']),reverse=x['order']=='desc');cols=HAND['projection_columns'][projection]
 return [[r[c] for c in cols] for r in rows], [r['id'] for r in rows]
def classify(plan):
 details=[r[3] for r in plan]
 if any('USING COVERING INDEX samples_bucket_label_idx' in d for d in details):return 'COVERING_REPORTED'
 if any('USING INDEX samples_bucket_label_idx' in d for d in details):return 'INDEX_TABLE_LOOKUP_REPORTED'
 return 'OTHER_OR_UNRECOGNIZED'
def check(r,x,literal=None):
 if literal and literal.get('status')=='EXECUTION_FAILED':assert r['status']=='EXECUTION_FAILED' and r['cleanup']=={'closed':True,'post_close_error':'ProgrammingError'};return
 assert r['status']=='OBSERVED' and r['input_echo']==x and r['selected_projection']==x['projection'] and r['db_opened'] is True
 assert r['loaded_rows']==ROWS and r['row_count']==256
 for row in HAND['literal_rows']:assert ROWS[row['id']-1]==row
 for bucket,key in [(0,'bucket0_asc_ids'),(None,'bucket_null_asc_ids'),(99,'empty_ids')]:assert expected(dict(bucket=bucket,order='asc'), 'index')[1]==HAND[key]
 assert r['cleanup']=={'closed':True,'post_close_error':'ProgrammingError'}
 env=r['environment'];assert env['sqlite_version'] and env['sqlite_version']==env['sqlite_module_version'] and env['source_id'] and env['python'] and env['system']=='Darwin';assert env['compile_options']==sorted(set(env['compile_options'])) and env['compile_options']
 assert set(r['queries'])=={'index','payload'}
 for name,q in r['queries'].items():
  rows,_=expected(x,name);cols=HAND['projection_columns'][name];where='bucket IS NULL' if x['bucket'] is None else 'bucket = ?';direction=x['order'].upper();sql='SELECT '+', '.join(cols)+' FROM samples WHERE '+where+' ORDER BY label '+direction+', id '+direction
  assert q['sql']==sql and q['params']==([] if x['bucket'] is None else [x['bucket']]);assert q['columns']==cols and q['rows']==rows and q['row_count']==len(rows)
  assert q['schema_cover_possible']==HAND['schema_cover_possible'][name] and q['missing_projection']==([] if name=='index' else ['payload'])
  assert all(len(row)==4 and all(type(v)==int for v in row[:3]) and type(row[3])==str for row in q['eqp_raw']);assert q['eqp_raw'];assert q['plan_class']==classify(q['eqp_raw'])
  assert q['plan_contract_consistent']==(q['plan_class']!='COVERING_REPORTED' or name=='index')
 observed=r['queries']['index']['plan_class']=='COVERING_REPORTED' and r['queries']['payload']['plan_class']=='INDEX_TABLE_LOOKUP_REPORTED';assert r['comparison_status']==('COMPARISON_OBSERVED' if observed else 'COMPARISON_NOT_ESTABLISHED')
 if literal:assert r['queries']['index']['row_count']==literal['rows'] and sum(row[1] is None for row in r['queries']['index']['rows'])==literal['null_labels'] and [r['queries'][n]['schema_cover_possible'] for n in ['index','payload']]==literal['schema_cover']
if __name__=='__main__':
 try:a=json.load(sys.stdin);check(a['result'],a['input'],a.get('literal'));print(json.dumps({'status':'passed'}))
 except Exception as e:print(json.dumps({'status':'failed','reason':type(e).__name__}));sys.exit(1)

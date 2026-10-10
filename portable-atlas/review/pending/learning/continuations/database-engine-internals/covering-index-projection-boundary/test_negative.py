import json,copy,subprocess,sys
from pathlib import Path
from model import run
from oracle import check
from sqlite_audit import audit
P=Path(__file__).resolve().parent
def collect():
 x={'bucket':0,'projection':'index','order':'asc'};base=run(x);check(base,x);audit(base,x);mutants=[]
 def rejects(name,change):
  r=copy.deepcopy(base);change(r)
  try:check(r,x);audit(r,x)
  except (AssertionError,KeyError,TypeError,IndexError):mutants.append(name);return
  raise AssertionError('accepted mutant '+name)
 rejects('drop_loaded_row',lambda r:r['loaded_rows'].pop())
 rejects('fabricate_payload',lambda r:r['loaded_rows'][0].update(payload='fake'))
 rejects('deduplicate_results',lambda r:r['queries']['index'].update(rows=[list(v) for v in dict.fromkeys(tuple(v) for v in r['queries']['index']['rows'])]))
 rejects('NULL_to_empty',lambda r:r['queries']['index']['rows'][0].__setitem__(1,''))
 rejects('reverse_order',lambda r:r['queries']['index']['rows'].reverse())
 rejects('drop_payload_column',lambda r:r['queries']['payload']['rows'][0].pop())
 rejects('wrong_where',lambda r:r['queries']['index'].update(sql=r['queries']['index']['sql'].replace('bucket = ?','bucket != ?')))
 rejects('wrong_tie_break',lambda r:r['queries']['index'].update(sql=r['queries']['index']['sql'].replace(', id ASC','')))
 rejects('wrong_binding',lambda r:r['queries']['index'].update(params=[1]))
 rejects('wrong_projection_echo',lambda r:r.update(selected_projection='payload'))
 rejects('wrong_row_count',lambda r:r['queries']['payload'].update(row_count=0))
 rejects('claim_payload_schema_cover',lambda r:r['queries']['payload'].update(schema_cover_possible=True,missing_projection=[]))
 rejects('fake_index_xinfo_payload',lambda r:r['index_xinfo'][0].__setitem__(2,'payload'))
 rejects('fake_schema',lambda r:r['schema'][0].__setitem__(3,'CREATE INDEX other ON samples(payload)'))
 rejects('fake_table_info',lambda r:r['table_info'][0].__setitem__(1,'other'))
 rejects('fake_index_list',lambda r:r['index_list'].clear())
 rejects('fake_sqlite_version',lambda r:r['environment'].update(sqlite_version='99.0',sqlite_module_version='99.0'))
 rejects('fake_compile_options',lambda r:r['environment'].update(compile_options=['FAKE']))
 rejects('fake_source_id',lambda r:r['environment'].update(source_id='FAKE'))
 rejects('fake_EQP_tree_id',lambda r:r['queries']['index']['eqp_raw'][0].__setitem__(0,999))
 rejects('fake_plan_class',lambda r:r['queries']['payload'].update(plan_class='COVERING_REPORTED'))
 rejects('hide_comparison_unknown',lambda r:r.update(comparison_status='COMPARISON_NOT_ESTABLISHED' if r['comparison_status']=='COMPARISON_OBSERVED' else 'COMPARISON_OBSERVED'))
 rejects('missing_close',lambda r:r['cleanup'].update(closed=False))
 rejects('fake_post_close',lambda r:r['cleanup'].update(post_close_error=None))
 rejects('drop_sqlite_trace',lambda r:r['sqlite_trace'].pop())
 rejects('reorder_operation_trace',lambda r:r['trace'].reverse())
 # Contract-only hypothetical; it is never presented as a measured runtime plan.
 unknown=copy.deepcopy(base)
 for q in unknown['queries'].values():q.update(eqp_raw=[[0,0,0,'UNRECOGNIZED FUTURE PLAN']],plan_class='OTHER_OR_UNRECOGNIZED',plan_contract_consistent=True)
 unknown['comparison_status']='COMPARISON_NOT_ESTABLISHED';check(unknown,x)
 try:audit(unknown,x)
 except AssertionError:pass
 else:raise AssertionError('fabricated runtime plan accepted')
 refusals=[]
 invalid=[None,[],{},dict(x,bucket=True),dict(x,bucket=1.0),dict(x,bucket='0'),dict(x,bucket=8),dict(x,bucket=-1),dict(x,projection='all'),dict(x,order='random'),dict(x,path='x'),dict(x,sql='SELECT 1')]
 for i,v in enumerate(invalid):
  p=subprocess.run([sys.executable,'-B','model.py'],input=json.dumps(v),text=True,capture_output=True,cwd=P);r=json.loads(p.stdout);assert p.returncode==2 and r['status']=='INPUT_REFUSED' and r['db_opened'] is False;refusals.append('schema-'+str(i))
 p=subprocess.run([sys.executable,'-B','model.py'],input='{',text=True,capture_output=True,cwd=P);r=json.loads(p.stdout);assert p.returncode==2 and r['db_opened'] is False;refusals.append('invalid-json')
 failure=run(x,True);check(failure,x,{'status':'EXECUTION_FAILED'});audit(failure,x)
 return dict(status='passed',mutants=mutants,refusals=refusals,unknown_plan_contract='passed; fabricated raw rejected by real replay',failure_cleanup='passed')
if __name__=='__main__':
 r=collect()
 if sys.argv[1:]==['--record']:(P/'evidence/negative.json').write_text(json.dumps(r,indent=2)+'\n')
 print(json.dumps(r))

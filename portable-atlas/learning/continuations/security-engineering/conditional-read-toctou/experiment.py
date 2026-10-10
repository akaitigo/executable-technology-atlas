import argparse,json,shutil,sqlite3,sys,tempfile
from pathlib import Path
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parent

def query(connection,label,sql,params,trace):
 before=connection.in_transaction;connection.execute('BEGIN')
 try:
  rows=connection.execute(sql,params).fetchall();trace.append({'event':'sql','connection':'reader','phase':label,'sql':sql,'params':list(params),'rows':[list(r) for r in rows],'transaction_before':before,'transaction_during':connection.in_transaction,'exit':0});connection.commit();trace.append({'event':'commit','connection':'reader','phase':label,'transaction_after':connection.in_transaction});return rows
 except sqlite3.Error as e:
  trace.append({'event':'sql','connection':'reader','phase':label,'sql':sql,'params':list(params),'rows':None,'transaction_before':before,'transaction_during':connection.in_transaction,'exit':1,'error':str(e)});connection.rollback();trace.append({'event':'rollback','connection':'reader','phase':label,'transaction_after':connection.in_transaction});raise

def run(spec,fixture,snapshot_root):
 result=None
 with tempfile.TemporaryDirectory(prefix='atlas-toctou-') as tmp:
  database=Path(tmp)/'state.sqlite';reader=sqlite3.connect(database);writer=sqlite3.connect(database);trace=[]
  try:
   reader.execute('CREATE TABLE resources(id TEXT PRIMARY KEY, tenant TEXT NOT NULL, payload TEXT NOT NULL, revision INTEGER NOT NULL)');reader.executemany('INSERT INTO resources VALUES(?,?,?,?)',fixture['initial_rows']);reader.commit();trace.append({'event':'observation-start','state':'initial committed fixture','reader_transaction':reader.in_transaction,'writer_transaction':writer.in_transaction})
   before=reader.execute('SELECT id,tenant,payload,revision FROM resources ORDER BY id').fetchall()
   def change():
    if spec['change'] is None:trace.append({'event':'no-change'});return
    writer.execute('BEGIN IMMEDIATE');writer.execute('UPDATE resources SET tenant=?,payload=?,revision=? WHERE id=?',(*spec['change'],spec['resource']));trace.append({'event':'mutation','connection':'writer','transaction_during':writer.in_transaction,'new_values':spec['change']});writer.commit();trace.append({'event':'commit','connection':'writer','phase':'change','transaction_after':writer.in_transaction})
   reason=None;checked=None;actor_tenant=None
   if type(spec['actor']) is not str:reason='actor-type'
   elif spec['actor'] not in fixture['actors']:reason='unknown-actor'
   elif type(spec['resource']) is not str:reason='resource-type'
   if reason:
    normal={'decision':'refuse','reason':reason,'payload':None,'row_tenant':None,'attempts':0};faulty=dict(normal);trace.append({'event':'input-refused','reason':reason})
   else:
    actor_tenant=fixture['actors'][spec['actor']]
    if spec['schedule']=='before-check':change()
    checked_rows=query(reader,'check','SELECT tenant FROM resources WHERE id=?',(spec['resource'],),trace);checked=bool(checked_rows and checked_rows[0][0]==actor_tenant);trace.append({'event':'check-result','tenant':checked_rows[0][0] if checked_rows else None,'check_allowed':checked,'diagnostic_only_for_normal':True})
    if spec['schedule']=='after-check':change()
    col='missing_payload' if spec['sql_failure'] else 'payload'
    try:
     rows=query(reader,'conditional-read',f'SELECT tenant,{col} FROM resources WHERE id=? AND tenant=?',(spec['resource'],actor_tenant),trace)
     normal={'decision':'allow' if rows else 'deny','reason':'conditional-match' if rows else 'conditional-no-row','payload':rows[0][1] if rows else None,'row_tenant':rows[0][0] if rows else None,'attempts':1}
    except sqlite3.Error as e:normal={'decision':'error','reason':'sqlite-read-error','payload':None,'row_tenant':None,'attempts':1,'error':str(e)}
    if checked:
     try:
      rows=query(reader,'id-only-read',f'SELECT tenant,{col} FROM resources WHERE id=?',(spec['resource'],),trace)
      faulty={'decision':'allow' if rows else 'deny','reason':'old-check-then-id' if rows else 'id-no-row','payload':rows[0][1] if rows else None,'row_tenant':rows[0][0] if rows else None,'attempts':1}
     except sqlite3.Error as e:faulty={'decision':'error','reason':'sqlite-read-error','payload':None,'row_tenant':None,'attempts':1,'error':str(e)}
    else:faulty={'decision':'deny','reason':'precheck-deny','payload':None,'row_tenant':None,'attempts':0};trace.append({'event':'faulty-read-skipped','reason':'precheck-deny'})
   after=reader.execute('SELECT id,tenant,payload,revision FROM resources ORDER BY id').fetchall()
   result={'id':spec['id'],'status':'execution-error' if normal['decision']=='error' else 'expected-refusal' if normal['decision']=='refuse' else 'observed','request':{'actor':spec['actor'],'resource':spec['resource']},'actor_tenant':actor_tenant,'check_allowed':checked,'normal':normal,'faulty':faulty,'before_rows':[list(r) for r in before],'after_rows':[list(r) for r in after],'trace':trace,'sqlite_version':sqlite3.sqlite_version}
  finally:reader.close();writer.close()
  if snapshot_root:
   dest=snapshot_root/spec['id']/'state.sqlite';dest.parent.mkdir(parents=True,exist_ok=False);shutil.copyfile(database,dest)
 result['owned_tmp_cleaned']=not database.parent.exists();return result

def main():
 parser=argparse.ArgumentParser();parser.add_argument('--snapshot-root');args=parser.parse_args();folder=Path(args.snapshot_root) if args.snapshot_root else None
 fixture=json.loads((ROOT/'fixture.json').read_text());specs=json.loads((ROOT/'contracts.json').read_text())['cases'];print(json.dumps({'rows':[run(s,fixture,folder) for s in specs]},ensure_ascii=False))
if __name__=='__main__':main()

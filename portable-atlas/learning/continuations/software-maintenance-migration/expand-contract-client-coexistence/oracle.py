# SPDX-License-Identifier: Apache-2.0
# Independent observer queries live SQLite. No producer import or decimal conversion.
def observe(db):
 return dict(schema=[list(x) for x in db.execute('PRAGMA table_info(money)')],ddl=[list(x) for x in db.execute("SELECT sql FROM sqlite_schema WHERE name='money'")],rows=[list(x) for x in db.execute('SELECT * FROM money ORDER BY id')],integrity=[list(x) for x in db.execute('PRAGMA integrity_check')])
SCHEMA={
 'seed':[[0,'id','INTEGER',0,None,1],[1,'amount_text','TEXT',1,None,0]],
 'expand':[[0,'id','INTEGER',0,None,1],[1,'amount_text','TEXT',1,None,0],[2,'amount_cents','INTEGER',0,None,0]],
 'contract':[[0,'id','INTEGER',0,None,1],[1,'amount_cents','INTEGER',0,None,0]]}
ROWS={
 'seed':[[1,'12.30'],[2,'0.00'],[3,'1.05']],
 'expand':[[1,'12.30',None],[2,'0.00',None],[3,'1.05',None]],
 'backfill':[[1,'12.30',1230],[2,'0.00',0],[3,'1.05',105]],
 'bridge':[[1,'20.00',2000],[2,'0.00',0],[3,'1.05',105]],
 'old-write-fault':[[1,'20.00',1230],[2,'0.00',0],[3,'1.05',105]],
 'contract':[[1,2000],[2,0],[3,105]]}
# phase/state table and explicit guard decision, authored before producer run.
LEDGER={
 'expand-only':('OK',['seed','expand'],None),
 'backfill':('OK',['seed','expand','backfill'],None),
 'bridge':('OK',['seed','expand','backfill','bridge'],None),
 'active-guard':('REFUSED_CLIENT_ACTIVE',['seed','expand','backfill','bridge','guard'],dict(all_rows_consistent=True,retired=False,allowed=False)),
 'contract':('OK',['seed','expand','backfill','bridge','guard','contract'],dict(all_rows_consistent=True,retired=True,allowed=True)),
 'old-write-fault':('REFUSED_INCONSISTENT',['seed','expand','backfill','old-write-fault','guard'],dict(all_rows_consistent=False,retired=True,allowed=False)),
 'invalid-amount':('REFUSED_INVALID_AMOUNT',['seed','expand','backfill','write-refused'],None),
 'execution-failure':('EXECUTION_FAILURE',['seed','expand','backfill','write-rollback'],None)}
def check(name,result):
 status,phases,guard=LEDGER[name];assert result['status']==status and result['guard']==guard
 assert [x['phase'] for x in result['phases']]==phases
 for p in result['phases']:
  phase=p['phase'];state=('old-write-fault' if name=='old-write-fault' else 'bridge') if phase=='guard' else 'backfill' if phase in ('write-refused','write-rollback') else phase
  schema='seed' if state=='seed' else 'contract' if state=='contract' else 'expand'
  assert p['direct']['schema']==SCHEMA[schema] and p['direct']['rows']==ROWS[state] and p['direct']['integrity']==[['ok']]
  ddl={'seed':'CREATE TABLE money(id INTEGER PRIMARY KEY,amount_text TEXT NOT NULL)','expand':'CREATE TABLE money(id INTEGER PRIMARY KEY,amount_text TEXT NOT NULL, amount_cents INTEGER)','contract':'CREATE TABLE money(id INTEGER PRIMARY KEY,amount_cents INTEGER)'}
  assert p['direct']['ddl']==[[ddl[schema]]],p['direct']['ddl']
  old=p['clients']['old'];new=p['clients']['new']
  if schema=='contract':assert old['status']=='SQL_FAILURE' and old['rows']==[] and 'amount_text' in old['error']
  else:assert old['status']=='OK' and old['rows']==[[row[0],row[1]] for row in ROWS[state]]
  if schema=='seed':assert new['status']=='SQL_FAILURE' and new['rows']==[] and 'amount_cents' in new['error']
  else:assert new['status']=='OK' and new['rows']==[[row[0],row[1] if schema=='contract' else row[2]] for row in ROWS[state]]
 assert result['clients']==result['phases'][-1]['clients']
 if name=='execution-failure':assert 'ROLLBACK' in result['trace'] and 'nonexistent' in result['reason']
 if name=='bridge':assert "UPDATE money SET amount_text='20.00',amount_cents=2000 WHERE id=1" in result['trace']
 return True
AMOUNTS=[('0.00',0),('0.01',1),('1.05',105),('12.30',1230),('9999.99',999999)]

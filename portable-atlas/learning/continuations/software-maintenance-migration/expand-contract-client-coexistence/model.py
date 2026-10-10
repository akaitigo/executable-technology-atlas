# SPDX-License-Identifier: Apache-2.0
import decimal,re,sqlite3
SEED=[[1,'12.30'],[2,'0.00'],[3,'1.05']]
NAMES=('expand-only','backfill','bridge','active-guard','contract','old-write-fault','invalid-amount','execution-failure')
def cents(s):
 if not isinstance(s,str) or not re.fullmatch(r'(0|[1-9][0-9]{0,3})\.[0-9]{2}',s):raise ValueError('canonical amount 0.00..9999.99 required')
 return int(decimal.Decimal(s)*100)
def text(n):
 if type(n) is not int or not 0<=n<=999999:raise ValueError('cent integer 0..999999 required')
 return format(decimal.Decimal(n)/100,'.2f')
def client(db,column):
 sql='SELECT id,'+column+' FROM money ORDER BY id'
 try:return dict(status='OK',sql=sql,rows=[list(x) for x in db.execute(sql)])
 except sqlite3.Error as e:return dict(status='SQL_FAILURE',sql=sql,rows=[],error=type(e).__name__+': '+str(e))
def run(c,observe):
 if c.get('id') not in NAMES or type(c.get('retired')) is not bool:
  return dict(status='REFUSED_INVALID_INPUT',reason='case or retired bool',phases=[],trace=[],guard=None,clients=None)
 phases=[];trace=[];guard=None;status='OK';reason='';db=sqlite3.connect(':memory:');db.set_trace_callback(trace.append)
 def capture(phase):phases.append(dict(phase=phase,direct=observe(db),clients=dict(old=client(db,'amount_text'),new=client(db,'amount_cents'))))
 try:
  db.execute('CREATE TABLE money(id INTEGER PRIMARY KEY,amount_text TEXT NOT NULL)');db.executemany('INSERT INTO money VALUES(?,?)',SEED);db.commit();capture('seed')
  with db:db.execute('ALTER TABLE money ADD COLUMN amount_cents INTEGER')
  capture('expand')
  if c['id']!='expand-only':
   with db:
    for oid,s in db.execute('SELECT id,amount_text FROM money ORDER BY id').fetchall():db.execute('UPDATE money SET amount_cents=? WHERE id=?',(cents(s),oid))
   capture('backfill')
  if c['id'] not in ('expand-only','backfill'):
   try:n=cents(c['amount'])
   except (ValueError,KeyError) as e:status='REFUSED_INVALID_AMOUNT';reason=str(e);capture('write-refused')
   else:
    try:
     with db:
      if c['id']=='old-write-fault':db.execute('UPDATE money SET amount_text=? WHERE id=1',(c['amount'],))
      elif c['id']=='execution-failure':
       db.execute('UPDATE money SET amount_text=? WHERE id=1',(c['amount'],));db.execute('UPDATE money SET nonexistent=? WHERE id=1',(n,))
      else:db.execute('UPDATE money SET amount_text=?,amount_cents=? WHERE id=1',(c['amount'],n))
     capture('old-write-fault' if c['id']=='old-write-fault' else 'bridge')
    except sqlite3.Error as e:status='EXECUTION_FAILURE';reason=type(e).__name__+': '+str(e);capture('write-rollback')
  if c['id'] in ('active-guard','contract','old-write-fault') and status=='OK':
   all_rows=db.execute('SELECT id,amount_text,amount_cents FROM money ORDER BY id').fetchall()
   consistent=all(type(n) is int and cents(s)==n and text(n)==s for _,s,n in all_rows)
   guard=dict(all_rows_consistent=consistent,retired=c['retired'],allowed=consistent and c['retired'])
   if not consistent:status='REFUSED_INCONSISTENT';reason='old/new values differ'
   elif not c['retired']:status='REFUSED_CLIENT_ACTIVE';reason='synthetic retirement input is false'
   capture('guard')
   if guard['allowed']:
    with db:db.execute('ALTER TABLE money DROP COLUMN amount_text')
    capture('contract')
  return dict(status=status,reason=reason,phases=phases,trace=trace,guard=guard,clients=phases[-1]['clients'])
 except sqlite3.Error as e:
  return dict(status='EXECUTION_FAILURE',reason=type(e).__name__+': '+str(e),phases=phases,trace=trace,guard=guard,clients=None)
 finally:db.close()

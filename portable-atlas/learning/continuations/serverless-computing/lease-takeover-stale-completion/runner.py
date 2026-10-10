# SPDX-License-Identifier: Apache-2.0
import sys
sys.dont_write_bytecode=True
import sqlite3,tempfile,datetime,platform
from pathlib import Path
CLAIM="UPDATE jobs SET owner=?, generation=generation+1, expiry=?, state='IN_PROGRESS', result=NULL WHERE job_id='j' AND (state='READY' OR (state='IN_PROGRESS' AND expiry<=?))"
COMPLETE="UPDATE jobs SET state='DONE', result=? WHERE job_id='j' AND owner=? AND generation=? AND state='IN_PROGRESS' AND ?<expiry"
FAULT="UPDATE jobs SET state='DONE', result=? WHERE job_id='j'"
A=dict(op='claim',owner='A',tick=0)
SCHEDULES={
 'takeover':[A,dict(op='claim',owner='B',tick=9),dict(op='claim',owner='B',tick=10),dict(op='complete',owner='B',generation=2,tick=11,result=200),dict(op='complete',owner='A',generation=1,tick=12,result=100)],
 'job-id-fault':[A,dict(op='claim',owner='B',tick=9),dict(op='claim',owner='B',tick=10),dict(op='complete',owner='B',generation=2,tick=11,result=200),dict(op='fault-complete',owner='A',generation=1,tick=12,result=100)],
 'on-time':[A,dict(op='complete',owner='A',generation=1,tick=9,result=100)],
 'expiry-boundary':[A,dict(op='complete',owner='A',generation=1,tick=10,result=100)],
 'owner-mismatch':[A,dict(op='complete',owner='B',generation=1,tick=9,result=100)],
 'generation-mismatch':[A,dict(op='complete',owner='A',generation=2,tick=9,result=100)],
 'done-replay':[A,dict(op='complete',owner='A',generation=1,tick=8,result=100),dict(op='complete',owner='A',generation=1,tick=9,result=200)],
 'sql-error':[A,dict(op='sql-error',owner='A',generation=1,tick=9,result=100)],
 'refusal':[A,dict(op='complete',owner='A',tick=9,result=100)]}
def valid(op):
 return type(op) is dict and op.get('op') in ('claim','complete','fault-complete','sql-error') and op.get('owner') in ('A','B') and type(op.get('tick')) is int and 0<=op['tick']<=20 and (op['op']=='claim' or (type(op.get('generation')) is int and 1<=op['generation']<=9 and type(op.get('result')) is int and 0<=op['result']<=999))
def state(path):
 c=sqlite3.connect('file:'+str(path)+'?mode=ro',uri=True)
 try:return list(c.execute('SELECT state, owner, generation, expiry, result FROM jobs WHERE job_id=?',('j',)).fetchone())
 finally:c.close()
def operate(path,op):
 r=dict(input=op,sql=None,params=[],rowcount=None,sql_issued=False)
 if not valid(op):r.update(status='REFUSED_INPUT',error='owner/tick/generation/result contract');return r
 r['before']=state(path);c=sqlite3.connect(path)
 try:
  name=op['op'];sql=CLAIM if name=='claim' else FAULT if name=='fault-complete' else 'UPDATE missing_jobs SET result=?' if name=='sql-error' else COMPLETE
  params=[op['owner'],op['tick']+10,op['tick']] if name=='claim' else [op['result']] if name in ('fault-complete','sql-error') else [op['result'],op['owner'],op['generation'],op['tick']]
  r.update(sql=sql,params=params,sql_issued=True);cur=c.execute(sql,params);c.commit();r.update(rowcount=cur.rowcount,status='SQL_APPLIED' if cur.rowcount==1 else 'SQL_ZERO_MATCH')
 except sqlite3.Error as e:c.rollback();r.update(status='SQL_EXCEPTION',error_class=type(e).__name__,error_message=str(e),error_code=None,error_name=None)
 finally:c.close()
 r['after']=state(path);return r
_DEFAULT=object()
def run(case,last_tick=_DEFAULT,db_copy=None):
 r=dict(case=case,started_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),python=platform.python_version(),sqlite=sqlite3.sqlite_version,lease=10,events=[],status='OK',model='virtual ticks / sequential fresh SQLite connections')
 if case not in SCHEDULES or (last_tick is not _DEFAULT and (type(last_tick) is not int or not 0<=last_tick<=20)):
  r.update(status='REFUSED_INPUT',stage='validation',error='case and last tick int 0..20 required')
 else:
  with tempfile.TemporaryDirectory(prefix='atlas-lease-owned-') as tmp:
   path=Path(tmp)/'lease.sqlite';c=sqlite3.connect(path);c.execute('CREATE TABLE jobs(job_id TEXT PRIMARY KEY,state TEXT,owner TEXT,generation INTEGER,expiry INTEGER,result INTEGER)');c.execute("INSERT INTO jobs VALUES('j','READY',NULL,0,0,NULL)");c.commit();c.close();r['initial']=state(path)
   ops=[dict(o) for o in SCHEDULES[case]]
   if last_tick is not _DEFAULT:ops[-1]['tick']=last_tick
   for op in ops:
    ev=operate(path,op)
    if ev['status']=='REFUSED_INPUT':ev['after']=state(path) # separate observer; rejected operation issued no SQL
    r['events'].append(ev)
   r['final']=state(path);r['tmp_cleanup']=True
   if db_copy is not None:
    import shutil
    shutil.copy2(path,db_copy)
  r['stage']='complete'
 r['ended_utc']=datetime.datetime.now(datetime.timezone.utc).isoformat();return r

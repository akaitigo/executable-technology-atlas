# SPDX-License-Identifier: Apache-2.0
import sqlite3
# Literal step rowcounts and state expectations; no runner or predicate sharing.
I=['IN_PROGRESS','A',1,10,None];D=['DONE','A',1,10,100];B=['IN_PROGRESS','B',2,20,None];DB=['DONE','B',2,20,200]
EXPECTED={'takeover':[(1,I),(0,I),(1,B),(1,DB),(0,DB)],'job-id-fault':[(1,I),(0,I),(1,B),(1,DB),(1,['DONE','B',2,20,100])],'on-time':[(1,I),(1,D)],'expiry-boundary':[(1,I),(0,I)],'owner-mismatch':[(1,I),(0,I)],'generation-mismatch':[(1,I),(0,I)],'done-replay':[(1,I),(1,D),(0,D)],'sql-error':[(1,I),(None,I)],'refusal':[(1,I),(None,I)]}
TICKS={'takeover':[0,9,10,11,12],'job-id-fault':[0,9,10,11,12],'on-time':[0,9],'expiry-boundary':[0,10],'owner-mismatch':[0,9],'generation-mismatch':[0,9],'done-replay':[0,8,9],'sql-error':[0,9],'refusal':[0,9]}
def check(r,db=None):
 assert r['python']=='3.9.6' and r['lease']==10 and r['status']=='OK' and r['stage']=='complete' and r['tmp_cleanup']
 assert r['started_utc']<=r['ended_utc'] and r['initial']==['READY',None,0,0,None]
 assert [(e['rowcount'],e['after']) for e in r['events']]==EXPECTED[r['case']]
 assert [e['input']['tick'] for e in r['events']]==TICKS[r['case']]
 for i,e in enumerate(r['events']):
  count=EXPECTED[r['case']][i][0]
  if count is None:
   if r['case']=='refusal':assert e['status']=='REFUSED_INPUT' and not e['sql_issued'] and e['sql'] is None
   else:assert e['status']=='SQL_EXCEPTION' and e['error_class']=='OperationalError' and e['error_message']=='no such table: missing_jobs' and e['sql_issued']
  else:assert e['status']==('SQL_APPLIED' if count==1 else 'SQL_ZERO_MATCH') and e['sql_issued'] and e['sql'].startswith('UPDATE')
 assert r['final']==EXPECTED[r['case']][-1][1]
 if db is not None:
  c=sqlite3.connect(db.as_uri()+'?mode=ro&immutable=1',uri=True)
  try:
   c.execute('PRAGMA query_only=ON');row=c.execute("SELECT job_id,result,expiry,generation,owner,state FROM jobs").fetchone();assert list(row)==['j',r['final'][4],r['final'][3],r['final'][2],r['final'][1],r['final'][0]]
  finally:c.close()

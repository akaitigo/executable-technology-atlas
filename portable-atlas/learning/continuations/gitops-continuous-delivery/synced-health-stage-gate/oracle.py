# SPDX-License-Identifier: Apache-2.0
# Independent literal table: no runner import, gate predicate or reconcile algorithm.
COLUMNS=['event','generation','desired','actual','health','stage2_starts']
COMMON=[['initial',1,'v1','v1','Healthy',0],['publish-v2',2,'v2','v1','Progressing',0],['reconcile-v2',2,'v2','v2','Progressing',0]]
TAILS={
'healthy':[['health',2,'v2','v2','Healthy',0],['gate-start',2,'v2','v2','Healthy',1],['gate-already-started',2,'v2','v2','Healthy',1]],
'degraded':[['health',2,'v2','v2','Degraded',0],['gate-block',2,'v2','v2','Degraded',0]],
'desired-only-fault':[['health',2,'v2','v2','Degraded',0],['gate-start',2,'v2','v2','Degraded',1]],
'progressing':[['health',2,'v2','v2','Progressing',0],['gate-block',2,'v2','v2','Progressing',0]],
'rollback':[['health',2,'v2','v2','Degraded',0],['gate-block',2,'v2','v2','Degraded',0],['publish-rollback',3,'v1','v2','Degraded',0],['reconcile-rollback',3,'v1','v1','Progressing',0],['health-rollback',3,'v1','v1','Healthy',0]]}
SYNC={'initial':True,'publish-v2':False,'reconcile-v2':True,'health':True,'gate-start':True,'gate-block':True,'gate-already-started':True,'publish-rollback':False,'reconcile-rollback':True,'health-rollback':True}
def check(r):
 assert r['python']=='3.9.6' and r['started_utc']<=r['ended_utc']
 c=r['case']
 if c=='refusal':assert r['status']=='REFUSED_INPUT' and r['stage']=='validation' and r['events']==[];return
 if c=='failure':assert r['status']=='EXECUTION_FAILURE' and r['stage']=='executor' and r['events']==[] and r['error_class']=='RuntimeError' and r['error_message']=='injected stage executor failure';return
 assert r['status']=='OK' and r['stage']=='complete'
 assert [[e[k] for k in COLUMNS] for e in r['events']]==COMMON+TAILS[c]
 assert all(e['synced']==SYNC[e['event']] for e in r['events'])

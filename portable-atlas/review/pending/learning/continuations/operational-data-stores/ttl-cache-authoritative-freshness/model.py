import sqlite3,json,sys,platform
from fractions import Fraction
def validate(x):
 if type(x)!=dict or set(x)!={'ttl','policy','events'}:return 'SCHEMA'
 if type(x['ttl'])!=int or not 1<=x['ttl']<=10:return 'TTL'
 if x['policy'] not in ['strict','inclusive']:return 'POLICY'
 if type(x['events'])!=list or len(x['events'])>8:return 'EVENTS'
 last=-1
 for e in x['events']:
  if type(e)!=dict or e.get('op') not in ['read','update','invalidate'] or set(e)!=({'t','op','key','value'} if e.get('op')=='update' else {'t','op','key'}):return 'EVENTS'
  if type(e['t'])!=int or not 0<=e['t']<=20 or e['t']<last:return 'CLOCK'
  if e['key']!='item':return 'KEY'
  if e['op']=='update' and e['value'] not in ['red','blue','green']:return 'VALUE'
  last=e['t']
def run(x):
 reason=validate(x)
 if reason:return dict(status='INPUT_REFUSED',reason=reason,sql_executed=False)
 con=sqlite3.connect(':memory:',isolation_level=None);trace=[];con.set_trace_callback(trace.append)
 con.execute('CREATE TABLE authoritative (key TEXT PRIMARY KEY, value TEXT NOT NULL, version INTEGER NOT NULL)')
 con.execute('INSERT INTO authoritative VALUES (?, ?, ?)',('item','red',1));startup=list(trace);cache=None;steps=[]
 def sql(statement,params,phase,records):
  cur=con.execute(statement,params);rows=[list(r) for r in cur.fetchall()] if statement.startswith('SELECT') else None
  records.append(dict(statement=statement,params=list(params),phase=phase,rows=rows,rowcount=cur.rowcount));return rows
 try:
  for i,e in enumerate(x['events']):
   before=cache.copy() if cache else None;records=[];offset=len(trace);ret=None;kind=e['op'].upper();queries=0;expired=None
   if e['op']=='update':sql('UPDATE authoritative SET value=?, version=version+1 WHERE key=?',(e['value'],e['key']),'source-writer',records);kind='SOURCE_UPDATE'
   elif e['op']=='invalidate':cache=None;kind='INVALIDATE'
   else:
    hit=cache is not None and (e['t']<cache['expires_at'] if x['policy']=='strict' else e['t']<=cache['expires_at'])
    if hit:kind='HIT'
    else:
     rows=sql('SELECT value, version FROM authoritative WHERE key=?',(e['key'],),'client-refill',records);cache=dict(value=rows[0][0],version=rows[0][1],expires_at=e['t']+x['ttl']);kind='MISS';queries=1
    ret=dict(value=cache['value'],version=cache['version']);expired=e['t']>=cache['expires_at']
   source=sql('SELECT key, value, version FROM authoritative ORDER BY key',(),'harness-audit',records)[0]
   steps.append(dict(index=i,event=e,source_rows=[source],cache_before=before,cache_after=cache.copy() if cache else None,client=dict(result=kind,returned=ret,source_selects=queries,returned_deadline_expired=expired,authoritative_freshness=('UNOBSERVED_ON_HIT' if kind=='HIT' else 'READ_FROM_SOURCE') if ret else None),harness=dict(source_value=source[1],source_version=source[2],version_stale=ret['version']!=source[2] if ret else None,value_stale=ret['value']!=source[1] if ret else None),sql=records,trace=trace[offset:]))
  final=[list(r) for r in con.execute('SELECT key, value, version FROM authoritative ORDER BY key')];reads=[s for s in steps if s['client']['returned']];hits=[s for s in reads if s['client']['result']=='HIT'];misses=[s for s in reads if s['client']['result']=='MISS']
  stats=dict(reads=len(reads),hits=len(hits),misses=len(misses),hit_ratio=str(Fraction(len(hits),len(reads))) if reads else None,version_stale_hits=sum(s['harness']['version_stale'] for s in hits),value_stale_hits=sum(s['harness']['value_stale'] for s in hits),expired_returns=sum(s['client']['returned_deadline_expired'] for s in reads))
  return dict(status='OBSERVED',clock='FAKE_MONOTONE_INTEGER',policy=x['policy'],ttl=x['ttl'],steps=steps,stats=stats,final_source_rows=final,final_cache=cache,startup_trace=startup,environment=dict(python=platform.python_version(),sqlite=sqlite3.sqlite_version,database=':memory:',isolation_level=None),client_has_harness_audit=False,productionGuarantee='UNCONFIRMED')
 finally:con.close()
if __name__=='__main__':
 try:
  x=json.loads(sys.stdin.read())
  if '--fail' in sys.argv:raise RuntimeError('injected model failure')
  out=run(x)
 except json.JSONDecodeError:out=dict(status='INPUT_REFUSED',reason='JSON',sql_executed=False)
 except Exception as e:out=dict(status='EXECUTION_FAILURE',reason=type(e).__name__)
 print(json.dumps(out));sys.exit(0 if out['status']=='OBSERVED' else 2 if out['status']=='INPUT_REFUSED' else 1)

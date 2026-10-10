import json,sys,math
def fraction(n,d):
 if not d:return None
 g=math.gcd(n,d);n//=g;d//=g;return str(n) if d==1 else str(n)+'/'+str(d)
def cache_from(fill):return dict(value=fill[1],version=fill[2],expires_at=fill[3]) if fill else None
def literal_rows(r):
 rows=[]
 for s in r['steps']:
  e=s['event'];h=s['harness'];c=s['cache_after'];ret=s['client']['returned'];client=s['client'];updates=[q['rowcount'] for q in s['sql'] if q['phase']=='source-writer']
  rows.append([e['t'],e['op'],h['source_value'],h['source_version'],c['value'] if c else None,c['version'] if c else None,c['expires_at'] if c else None,ret['value'] if ret else None,ret['version'] if ret else None,client['result'],h['version_stale'],h['value_stale'],client['returned_deadline_expired'],client['source_selects'],updates[0] if updates else None])
 return rows
def check(r,x,lit=None):
 if lit and lit['status']!='OBSERVED':assert r['status']==lit['status'] and r['reason']==lit['reason'];return
 assert r['status']=='OBSERVED' and r['ttl']==x['ttl'] and r['policy']==x['policy'] and r['clock']=='FAKE_MONOTONE_INTEGER' and not r['client_has_harness_audit'] and r['productionGuarantee']=='UNCONFIRMED'
 assert r['environment']['database']==':memory:' and r['environment']['isolation_level'] is None and isinstance(r['environment']['sqlite'],str)
 fills=[];last_invalidation=-1;counts={'reads':0,'hits':0,'misses':0,'version_stale_hits':0,'value_stale_hits':0,'expired_returns':0};expected=[]
 for i,e in enumerate(x['events']):
  prior_updates=[p for p in x['events'][:i+1] if p['op']=='update'];sv=prior_updates[-1]['value'] if prior_updates else 'red';version=1+len(prior_updates);source=['item',sv,version];old=next((f for f in reversed(fills) if f[0]>last_invalidation),None);before=cache_from(old);kind='SOURCE_UPDATE' if e['op']=='update' else 'INVALIDATE';ret=None;expired=None;queries=0;sql=[];trace=[]
  if e['op']=='invalidate':last_invalidation=i;old=None
  elif e['op']=='update':
   sql.append(dict(statement='UPDATE authoritative SET value=?, version=version+1 WHERE key=?',params=[e['value'],'item'],phase='source-writer',rows=None,rowcount=1));trace.append("UPDATE authoritative SET value='"+e['value']+"', version=version+1 WHERE key='item'")
  else:
   allowed_ticks=range(old[3]+(1 if x['policy']=='inclusive' else 0)) if old else []
   hit=e['t'] in allowed_ticks;kind='HIT' if hit else 'MISS';counts['reads']+=1;counts['hits' if hit else 'misses']+=1
   if not hit:
    old=(i,sv,version,e['t']+x['ttl']);fills.append(old);queries=1;sql.append(dict(statement='SELECT value, version FROM authoritative WHERE key=?',params=['item'],phase='client-refill',rows=[[sv,version]],rowcount=-1));trace.append("SELECT value, version FROM authoritative WHERE key='item'")
   ret=dict(value=old[1],version=old[2]);expired=e['t'] in range(old[3],100);counts['expired_returns']+=expired
   if hit:counts['version_stale_hits']+=ret['version']!=version;counts['value_stale_hits']+=ret['value']!=sv
  sql.append(dict(statement='SELECT key, value, version FROM authoritative ORDER BY key',params=[],phase='harness-audit',rows=[source],rowcount=-1));trace.append('SELECT key, value, version FROM authoritative ORDER BY key')
  expected.append(dict(index=i,event=e,source_rows=[source],cache_before=before,cache_after=cache_from(old),client=dict(result=kind,returned=ret,source_selects=queries,returned_deadline_expired=expired,authoritative_freshness=('UNOBSERVED_ON_HIT' if kind=='HIT' else 'READ_FROM_SOURCE') if ret else None),harness=dict(source_value=sv,source_version=version,version_stale=ret['version']!=version if ret else None,value_stale=ret['value']!=sv if ret else None),sql=sql,trace=trace))
 assert r['steps']==expected
 updates=[e for e in x['events'] if e['op']=='update'];assert r['final_source_rows']==[['item',updates[-1]['value'] if updates else 'red',1+len(updates)]]
 last_fill=next((f for f in reversed(fills) if f[0]>last_invalidation),None);assert r['final_cache']==cache_from(last_fill)
 counts['hit_ratio']=fraction(counts['hits'],counts['reads']);assert r['stats']==counts
 assert r['startup_trace']==['CREATE TABLE authoritative (key TEXT PRIMARY KEY, value TEXT NOT NULL, version INTEGER NOT NULL)',"INSERT INTO authoritative VALUES ('item', 'red', 1)"]
 if lit:assert literal_rows(r)==lit['rows']
if __name__=='__main__':
 q=json.loads(sys.stdin.read());check(q['result'],q['input']);print(json.dumps(dict(status='passed',independent=True)))

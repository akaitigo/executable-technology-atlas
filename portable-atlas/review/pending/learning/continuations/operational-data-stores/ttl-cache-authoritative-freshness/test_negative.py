import json,copy,subprocess,sys
from checker import read,browser,P
from oracle import check
fixture=read('fixture.json');lits=read('oracle.json');pointer=read('evidence/current.json');report=read('evidence/'+pointer['raw']);base=report['attempts'][0]['raw']['result'];mutants=[]
def test(name,fn,index=0):
 r=copy.deepcopy(report['attempts'][index]['raw']['result']);fn(r)
 try:check(r,fixture[index]['input'],lits[fixture[index]['id']])
 except (AssertionError,KeyError,TypeError):mutants.append(name);return
 raise AssertionError('survived '+name)
test('equal-deadline-is-hit',lambda r:r['steps'][3]['client'].update(result='HIT'))
test('source-update-implicitly-refreshes-cache',lambda r:r['steps'][1]['cache_after'].update(value='blue',version=2))
test('hit-extends-deadline',lambda r:r['steps'][2]['cache_after'].update(expires_at=9))
test('refill-uses-original-deadline',lambda r:r['steps'][1]['cache_after'].update(expires_at=10),4)
test('client-knows-unreceived-source',lambda r:r['steps'][2]['client'].update(authoritative_freshness='FRESH'))
test('version-stale-erased',lambda r:r['steps'][2]['harness'].update(version_stale=False))
test('same-value-means-same-version',lambda r:r['steps'][2]['harness'].update(version_stale=False),8)
test('UPDATE-rowcount-zero',lambda r:r['steps'][1]['sql'][0].update(rowcount=0))
test('SQL-trace-erased',lambda r:r['steps'][1].update(trace=[]))
test('harness-SELECT-erased',lambda r:r['steps'][2].update(sql=[]))
test('refill-SELECT-erased',lambda r:r['steps'][3]['sql'].pop(0))
test('hit-returns-harness-version',lambda r:r['steps'][2]['client']['returned'].update(version=2))
test('hit-source-query-count-lied',lambda r:r['steps'][2]['client'].update(source_selects=1))
test('hit-ratio-hardcoded',lambda r:r['stats'].update(hit_ratio='1'))
test('empty-hit-ratio-zero',lambda r:r['stats'].update(hit_ratio='0'),9)
test('fake-clock-called-real',lambda r:r.update(clock='REAL_CLOCK'))
b=read('evidence/browser.json');browser(b)
def bt(name,fn):
 bb=copy.deepcopy(b);fn(bb)
 try:browser(bb)
 except (AssertionError,KeyError,TypeError):mutants.append(name);return
 raise AssertionError('survived '+name)
bt('hardcoded-edited-answer',lambda b:b['cases'][15].update(answer=b['cases'][0]['answer']))
bt('diagram-expires-clamped',lambda b:b['cases'][0]['nodes'][0].update(expires='0'))
bt('stale-applied',lambda b:b['stale']['after_release'].update(raw=None))
bt('reset-retained',lambda b:b['reset']['ttl-override']['after'].update(answer='old answer'))
payloads=[[],dict(fixture[0]['input'],extra=1),dict(fixture[0]['input'],ttl=True),dict(fixture[0]['input'],ttl=1.5),dict(fixture[0]['input'],ttl=-1),dict(fixture[0]['input'],policy='unknown'),dict(fixture[0]['input'],events=[dict(t='0',op='read',key='item')]),dict(fixture[0]['input'],events=[dict(t=0,op='read',key='missing')])]
for x in payloads:
 r=subprocess.run([sys.executable,'-B','model.py'],input=json.dumps(x),text=True,capture_output=True,cwd=P);o=json.loads(r.stdout);assert r.returncode==2 and r.stderr=='' and o['status']=='INPUT_REFUSED' and o['sql_executed'] is False
print(json.dumps(dict(status='passed',mutants_rejected=len(mutants),mutants=mutants,schema_probes=len(payloads))))

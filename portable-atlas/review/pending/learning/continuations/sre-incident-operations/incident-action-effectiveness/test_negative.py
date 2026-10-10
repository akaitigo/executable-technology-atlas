import json,copy,subprocess,sys
from pathlib import Path
from oracle import check
from checker import ui,browser
P=Path(__file__).resolve().parent;fixtures=json.loads((P/'fixture.json').read_text());lits=json.loads((P/'oracle.json').read_text());pointer=json.loads((P/'evidence/current.json').read_text());report=json.loads((P/'evidence'/pointer['raw']).read_text());attempts={c['id']:c for c in report['attempts']};rejected=[]
def reject(name,fn):
 try:fn()
 except AssertionError:rejected.append(name);return
 raise AssertionError('escaped mutant '+name)
for name,id,change in [('done-is-effective','marked-only',lambda r:r.update(decision='VERIFIED_FINITE')),('old-build-PASS-is-current','stale-build-pass',lambda r:r.update(matchesCurrent=True)),('repro-only-is-complete','repro-only-partial',lambda r:r.update(completeSuite=True)),('partial-boundary-hidden','partial-retest',lambda r:r['current'].update(failed=[])),('fake-output','fixed-v2-retest',lambda r:r['current']['tests'][0]['actual'].update(output=3)),('fake-child-stdout','fixed-v2-retest',lambda r:r['current']['tests'][0].update(stdout='{}')),('fake-source-digest','fixed-v2-retest',lambda r:r['current'].update(source_sha256='0'*64)),('test-omitted','fixed-v2-retest',lambda r:r['current']['tests'].pop()),('deadline-cost-faked','bad-retest',lambda r:r['current']['tests'][0]['actual'].update(logical_ticks=2)),('automatic-approval','fixed-v2-retest',lambda r:r.update(approval='APPROVED')),('open-action-closed','open-action-pass',lambda r:r.update(actionEffective=True)),('count-inflated','fixed-v2-retest',lambda r:r.update(testsExecuted=8))]:
 r=copy.deepcopy(attempts[id]['raw']['result']);change(r);c=next(c for c in fixtures if c['id']==id);reject(name,lambda:check(r,c['input'],lits[id]))
b=json.loads((P/'evidence/browser.json').read_text());custom=json.loads((P/'custom-oracle.json').read_text());c=custom[0];o=next(o for o in b['cases'] if o['id']==c['id']);mut=copy.deepcopy(o);mut['answer']='固定答え VERIFIED';reject('hardcoded-editable-answer',lambda:ui(mut,c,c['literal']));mut=copy.deepcopy(o);mut['points'][1]['passed']='true';reject('diagram-hides-failure',lambda:ui(mut,c,c['literal']));mut=copy.deepcopy(b);mut['stale']['after_release']['raw']=mut['stale']['held']['raw'];reject('stale-applied',lambda:browser(mut));mut=copy.deepcopy(b);mut['reset']['prediction-action']['after']['answer']='残存';reject('reset-retained',lambda:browser(mut))
base=copy.deepcopy(fixtures[3]['input']);probes=[[],{},dict(base,extra=1)]
for field,value in [('current_build',None),('retest',1),('suite',['UNLISTED']),('evidence_build','production')]:
 x=copy.deepcopy(base);x[field]=value;probes.append(x)
for x in probes:
 p=subprocess.run([sys.executable,'-B','model.py'],input=json.dumps(x),text=True,capture_output=True,cwd=P);assert p.returncode==2 and json.loads(p.stdout)['status']=='INPUT_REFUSED'
print(json.dumps(dict(status='passed',mutants_rejected=len(rejected),mutants=rejected,schema_probes=len(probes))))

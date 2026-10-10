import json,copy,subprocess,sys
from pathlib import Path
from oracle import check
from checker import ui,browser
P=Path(__file__).resolve().parent;fixtures=json.loads((P/'fixture.json').read_text());lits=json.loads((P/'oracle.json').read_text());pointer=json.loads((P/'evidence/current.json').read_text());report=json.loads((P/'evidence'/pointer['raw']).read_text());attempts={c['id']:c for c in report['attempts']};rejected=[]
def reject(name,fn):
 try:fn()
 except AssertionError:rejected.append(name);return
 raise AssertionError('escaped mutant '+name)
for name,id,change in [('test-revision-recomputes-graph','test-revision',lambda r:r.update(recompute=True)),('old-PASS-current','requirement-revision',lambda r:r['proofs'][0].update(status='CURRENT_PASS')),('all-branches-stale','requirement-revision',lambda r:r['proofs'][1].update(status='STALE')),('missing-is-unaffected','missing-link',lambda r:r['proofs'][0].update(status='CURRENT_PASS')),('lost-old-impact','missing-link',lambda r:r.update(impact=['D-CAP'])),('hash-only-baseline','same-hash-new-revision',lambda r:r.update(recompute=False)),('same-input-stale','same-hash',lambda r:r['proofs'][0].update(status='STALE')),('new-calculation-is-test-run','unchanged',lambda r:r.update(testsExecuted=True)),('automatic-approval','unchanged',lambda r:r.update(approval='APPROVED')),('cross-link-no-fifo-impact','cross-link-add',lambda r:r['proofs'][1].update(status='CURRENT_PASS'))]:
 r=copy.deepcopy(attempts[id]['raw']['result']);change(r);c=next(c for c in fixtures if c['id']==id);reject(name,lambda:check(r,c['input'],lits[id]))
b=json.loads((P/'evidence/browser.json').read_text());custom=json.loads((P/'custom-oracle.json').read_text());c=custom[0];o=next(o for o in b['cases'] if o['id']==c['id']);mut=copy.deepcopy(o);mut['answer']='固定答え CURRENT_PASS';reject('hardcoded-editable-answer',lambda:ui(mut,c,c['literal']));mut=copy.deepcopy(o);mut['nodes'][-1]['rev']='9';reject('diagram-wrong-revision',lambda:ui(mut,c,c['literal']));mut=copy.deepcopy(b);mut['stale']['after_release']['raw']=mut['stale']['held']['raw'];reject('stale-applied',lambda:browser(mut));mut=copy.deepcopy(b);mut['reset']['prediction-graph']['after']['answer']='残存';reject('reset-retained',lambda:browser(mut))
base=copy.deepcopy(fixtures[0]['input']);probes=[[],{},dict(base,extra=1)]
for field,value in [('rev',0),('rev',True),('rev',1.5),('hash','bad')]:
 x=copy.deepcopy(base);x['new']['nodes'][0][field]=value;probes.append(x)
x=copy.deepcopy(base);x['new']['links'].append(x['new']['links'][0]);probes.append(x)
for x in probes:
 p=subprocess.run([sys.executable,'-B','model.py'],input=json.dumps(x),text=True,capture_output=True,cwd=P);assert p.returncode==2 and json.loads(p.stdout)['status']=='INPUT_REFUSED'
print(json.dumps(dict(status='passed',mutants_rejected=len(rejected),mutants=rejected,schema_probes=len(probes))))

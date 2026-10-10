import json,copy,subprocess,sys
from pathlib import Path
from oracle import check
from checker import ui,browser
P=Path(__file__).resolve().parent;fixtures=json.loads((P/'fixture.json').read_text());lits=json.loads((P/'oracle.json').read_text());pointer=json.loads((P/'evidence/current.json').read_text());report=json.loads((P/'evidence'/pointer['raw']).read_text());attempts={c['id']:c for c in report['attempts']};rejected=[]
def reject(name,fn):
 try:fn()
 except AssertionError:rejected.append(name);return
 raise AssertionError('escaped mutant '+name)
def row(r,id):return next(c for c in r['rows'] if c['id']==id)
baseid=fixtures[0]['id']
for name,id,change in [('speed-compensates-wrong',baseid,lambda r:row(r,'A')['new'].update(acceptance='PASS')),('correct-compensates-late',baseid,lambda r:row(r,'B')['new'].update(acceptance='PASS')),('missing-is-zero',baseid,lambda r:row(r,'E')['metrics'].update(worst_ms=0)),('unknown-is-pass','output-unobserved',lambda r:row(r,'C')['new'].update(R_CORRECT='PASS')),('unknown-hides-known-fail','known-fail-and-unknown',lambda r:row(r,'C')['new'].update(acceptance='INSUFFICIENT')),('boundary-strict-less','equal-boundary',lambda r:row(r,'C')['new'].update(acceptance='FAIL')),('all-front-accepted','no-accepted-front',lambda r:r['accepted'].update(new=['A','B'])),('tie-dominates','exact-tie',lambda r:r['dominance'].append(['C','D'])),('missing-on-front',baseid,lambda r:r['pareto'].append('E')),('threshold-changes-data','deadline-relaxed',lambda r:row(r,'B')['metrics'].update(worst_ms=100)),('synthetic-is-measured',baseid,lambda r:r.update(measurementSource='real-network')),('automatic-validation',baseid,lambda r:r.update(validation='APPROVED'))]:
 r=copy.deepcopy(attempts[id]['raw']['result']);change(r);c=next(c for c in fixtures if c['id']==id);reject(name,lambda:check(r,c['input'],lits[id]))
b=json.loads((P/'evidence/browser.json').read_text());custom=json.loads((P/'custom-oracle.json').read_text());c=custom[1];o=next(o for o in b['cases'] if o['id']==c['id']);mut=copy.deepcopy(o);mut['answer']='固定答え Cのみ合格';reject('hardcoded-editable-answer',lambda:ui(mut,c,c['literal']));mut=copy.deepcopy(o);mut['points'][0]['worst']='0';reject('diagram-wrong-data',lambda:ui(mut,c,c['literal']));mut=copy.deepcopy(b);mut['stale']['after_release']['raw']=mut['stale']['held']['raw'];reject('stale-applied',lambda:browser(mut));mut=copy.deepcopy(b);mut['reset']['prediction-acceptance']['after']['answer']='残存';reject('reset-retained',lambda:browser(mut))
base=copy.deepcopy(fixtures[0]['input']);probes=[[],{},dict(base,extra=1)]
for field,value in [('deadline_ms',0),('deadline_ms',True),('deadline_ms',1.5),('min_accuracy_bp',10001)]:
 x=copy.deepcopy(base);x['new'][field]=value;probes.append(x)
x=copy.deepcopy(base);x['candidates'][0]['samples'][0]['elapsed_ms']=-1;probes.append(x)
for x in probes:
 p=subprocess.run([sys.executable,'-B','model.py'],input=json.dumps(x),text=True,capture_output=True,cwd=P);assert p.returncode==2 and json.loads(p.stdout)['status']=='INPUT_REFUSED'
print(json.dumps(dict(status='passed',mutants_rejected=len(rejected),mutants=rejected,schema_probes=len(probes))))

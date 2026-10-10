import json,copy,subprocess,sys
from pathlib import Path
from oracle import check
from checker import ui,browser
P=Path(__file__).resolve().parent;fixtures=json.loads((P/'fixture.json').read_text());lits=json.loads((P/'oracle.json').read_text());pointer=json.loads((P/'evidence/current.json').read_text());report=json.loads((P/'evidence'/pointer['raw']).read_text());attempts={c['id']:c for c in report['attempts']};rejected=[]
def reject(name,fn):
 try:fn()
 except AssertionError:rejected.append(name);return
 raise AssertionError('escaped mutant '+name)
for name,id,change in [('seen-denominator-is-total','seen-only-100-unknown',lambda r:r['counts'].update(eligible=3)),('unknown-is-good','seen-only-100-unknown',lambda r:r.update(decision='CERTAIN_MET')),('unknown-is-bad','seen-only-100-unknown',lambda r:r['counts'].update(bad=1)),('remaining-clamped','late-bad-arrives',lambda r:r['remainingBounds'].update(lower='0')),('future-outcome-peek','seen-only-100-unknown',lambda r:r['groups'].update(bad=['D'])),('same-tick-excluded','arrival-equals-cutoff',lambda r:r['counts'].update(unknown=1)),('budget-rounded','editable-target-five-sixths',lambda r:r.update(allowedBudget='1')),('burn100-zero','target100-good',lambda r:r.update(burnBounds=dict(lower='0',upper='0'))),('empty-is-met','empty-ledger',lambda r:r.update(decision='CERTAIN_MET')),('unknown-forces-indeterminate','certain-met-with-unknown',lambda r:r.update(decision='INDETERMINATE')),('bad-best-case-met','certain-missed-with-unknown',lambda r:r.update(decision='CERTAIN_MET')),('production-approved','seen-only-100-unknown',lambda r:r.update(productionGuarantee='VERIFIED'))]:
 r=copy.deepcopy(attempts[id]['raw']['result']);change(r);c=next(c for c in fixtures+json.loads((P/'custom-oracle.json').read_text()) if c['id']==id);reject(name,lambda:check(r,c['input'],lits.get(id,c.get('literal'))))
b=json.loads((P/'evidence/browser.json').read_text());custom=json.loads((P/'custom-oracle.json').read_text());c=custom[0];o=next(o for o in b['cases'] if o['id']==c['id']);mut=copy.deepcopy(o);mut['answer']='固定答え CERTAIN_MET';reject('hardcoded-editable-answer',lambda:ui(mut,c,c['literal']));mut=copy.deepcopy(o);mut['ranges'][1]['lower']='0';reject('diagram-clamps-negative',lambda:ui(mut,c,c['literal']));mut=copy.deepcopy(b);mut['stale']['after_release']['raw']=mut['stale']['held']['raw'];reject('stale-applied',lambda:browser(mut));mut=copy.deepcopy(b);mut['reset']['prediction-verdict']['after']['answer']='残存';reject('reset-retained',lambda:browser(mut))
base=copy.deepcopy(fixtures[0]['input']);probes=[[],{},dict(base,extra=1)]
for field,value in [('cutoff',-1),('cutoff',True),('cutoff',1.5),('target',dict(num=2,den=1))]:
 x=copy.deepcopy(base);x[field]=value;probes.append(x)
x=copy.deepcopy(base);x['ledger'][0]['eligible']=1;probes.append(x)
for x in probes:
 p=subprocess.run([sys.executable,'-B','model.py'],input=json.dumps(x),text=True,capture_output=True,cwd=P);assert p.returncode==2 and json.loads(p.stdout)['status']=='INPUT_REFUSED'
print(json.dumps(dict(status='passed',mutants_rejected=len(rejected),mutants=rejected,schema_probes=len(probes))))

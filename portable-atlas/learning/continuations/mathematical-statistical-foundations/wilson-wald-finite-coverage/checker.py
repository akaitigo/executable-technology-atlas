"""Independent score test squared inequalities + 256 Fraction product weights. No sqrt/comb/producer import."""
import copy,json,sys
from fractions import Fraction as F
from itertools import product
sys.dont_write_bytecode=True
from runner import ROOT,SOURCES,digest,run,snapshot
HAND=json.loads((ROOT/'hand-oracle.json').read_text());Z=F(49,25);TOL=F(1,10**36)
def oracle(p):
 masses=[F(0)]*9;covered={m:[] for m in ['wald','wilson']}
 for k in range(9):
  a=F(k,8)
  if 8*(p-a)**2<=Z**2*a*(1-a):covered['wald'].append(k)
  if 8*(p-a)**2<=Z**2*p*(1-p):covered['wilson'].append(k)
 for seq in product((0,1),repeat=8):
  weight=F(1)
  for bit in seq:weight*=p if bit else 1-p
  masses[sum(seq)]+=weight
 return masses,covered,{m:sum(masses[k] for k in ks) for m,ks in covered.items()}
def inspect(r,x):
 assert r['status']=='calculated' and len(r['rows'])==9
 p=F(x['p']);masses,covered,cov=oracle(p);hand=HAND['p'][x['p']];s=r['summary'];assert s['input']==x and s['selected']==r['rows'][x['k']]
 assert sum(masses)==1 and F(s['probability_sum'])==1
 for m in ['wald','wilson']:
  assert covered[m]==hand[m+'_k'] and cov[m]==F(hand[m+'_coverage'])
  assert s['covered_k'][m]==covered[m] and F(s['coverage'][m])==cov[m] and F(s['difference_from_nominal'][m])==cov[m]-F(95,100)
 assert F(s['delta'])==cov['wilson']-cov['wald']==F(hand['delta']);assert s['nominal']=='0.95' and s['category']==('equal' if x['p']=='0.5' else 'wilson')
 assert r['context']['wald_clipping'] is False and r['context']['precision']==40
 for k,row in enumerate(r['rows']):
  a=F(k,8);assert row['k']==k and F(row['estimate'])==a and F(row['mass'])==masses[k]
  for m in ['wald','wilson']:
   t=row[m];l,u,w=map(F,[t['lower'],t['upper'],t['width']]);assert l<=u and abs(u-l-w)<TOL and t['contains']==(k in covered[m]) and t['outside_0_1']==(l<0 or u>1)
   reflected=r['rows'][8-k][m];assert abs(l+F(reflected['upper'])-1)<TOL
   if m=='wald':
    assert abs(l+u-2*a)<TOL and abs((w/2)**2-Z**2*a*(1-a)/8)<TOL
    if k in [0,8]:assert l==u==a and w==0
   else:
    assert 0<=l<=u<=1
    for b in [l,u]:assert abs(8*(b-a)**2-Z**2*b*(1-b))<TOL
    assert abs(l+u-(2*F(k)+Z**2)/(8+Z**2))<TOL
    if k in [0,8]:
     ends=HAND['endpoints']['wilson_k'+str(k)];assert abs(l-F(ends[0]))<TOL and abs(u-F(ends[1]))<TOL and w>0
 assert F(r['rows'][1]['wald']['lower'])<0 and F(r['rows'][7]['wald']['upper'])>1

def checkrun(text,expected):
 raw=run(text);r=raw['result'];assert raw['stderr']=='' and json.loads(raw['stdout'])==r
 if expected['status']=='calculated':assert raw['exit']==0;inspect(r,json.loads(text))
 else:assert raw['exit']==2 and r=={'status':'input_refusal','code':expected['code'],'summary':None,'rows':None}
 return raw

def main():
 before=snapshot();rows=json.loads((ROOT/'expected-table.json').read_text())['rows'];results=[checkrun(x['input_json'],x['expected']) for x in rows]
 valid=[x['result'] for x in results if x['exit']==0];mutants=[]
 for name in ['nominal-guarantee','clipped-wald','wald-as-wilson','zero-width-wilson','wrong-inclusion','wrong-mass','wrong-selection','refusal-as-calculation']:
  r=copy.deepcopy(valid[0]);x=r['summary']['input']
  if name=='nominal-guarantee':r['summary']['coverage']['wilson']='.95'
  elif name=='clipped-wald':r['rows'][1]['wald']['lower']='0'
  elif name=='wald-as-wilson':r['rows'][0]['wilson']=r['rows'][0]['wald'].copy()
  elif name=='zero-width-wilson':r['rows'][0]['wilson']['width']='0'
  elif name=='wrong-inclusion':r['rows'][0]['wilson']['contains']=False
  elif name=='wrong-mass':r['rows'][0]['mass']='.5'
  elif name=='wrong-selection':r['summary']['selected']=r['rows'][4]
  else:r={'status':'input_refusal','rows':None,'summary':None}
  try:inspect(r,x)
  except (AssertionError,KeyError,TypeError):mutants.append(name)
  else:raise AssertionError('mutant survived '+name)
 # all selected k, without reading old raw; every 256-sequence oracle independently checked
 for p in ['0.1','0.5','0.9']:
  for k in range(9):checkrun(json.dumps({'n':8,'p':p,'z':'1.96','k':k}),{'status':'calculated'})
 if (ROOT/'observation-data.js').exists():
  fixed=json.loads((ROOT/'observation-data.js').read_text().removeprefix('window.COVERAGE_OBSERVATION=').strip().removesuffix(';'));assert fixed==json.loads((ROOT/'observations'/fixed['run_id']/'raw.json').read_text())
  assert fixed['source_digests']=={n:digest(ROOT/n) for n in SOURCES}
  for row in fixed['rows']:
   r=row['run']['result'];assert json.loads(row['run']['stdout'])==r
   if r['status']=='calculated':inspect(r,json.loads(row['input_json']))
   else:assert row['run']['exit']==2 and r['code']==row['expected']['code']
 assert before==snapshot(),'normal checker changed unit'
 print(json.dumps({'fixed_cases':16,'accepted':9,'refused':7,'all_selected_p_k':27,'fraction_sequences_per_p':256,'mutants_rejected':mutants,'unit_sha_mtime_unchanged':True}));return 0
if __name__=='__main__':sys.exit(main())

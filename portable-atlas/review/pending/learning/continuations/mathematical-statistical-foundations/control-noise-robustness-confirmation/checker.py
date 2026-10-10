"""Independent pairwise dispersion/moment loss and locked-stage oracle."""
import copy,json,sys
from fractions import Fraction as F
sys.dont_write_bytecode=True
from runner import ROOT,SOURCES,digest,run,snapshot
HAND=json.loads((ROOT/'hand-oracle.json').read_text())
def expected(fixture):
 output={}
 for c in range(2):
  raw=fixture['cells'][2*c:2*c+2];values=list(map(F,raw[0]+raw[1]));mean=sum(values)/6;pair=sum((a-b)**2 for i,a in enumerate(values) for b in values[i+1:]);var=pair/36;loss=sum(v*v for v in values)/6-20*mean+100;noise_means=[sum(map(F,r))/3 for r in raw];within=sum(sum((F(a)-F(b))**2 for i,a in enumerate(r) for b in r[i+1:])/9 for r in raw)/2
  output['C'+str(c)]={'mean':mean,'bias':mean-10,'variance_N':var,'sample_variance_Nminus1':pair/30,'within_population_component':within,'between_noise_component':(noise_means[1]-noise_means[0])**2/4,'noise_difference':noise_means[1]-noise_means[0],'loss':loss}
 return output

def inspect_metrics(observed,fixture):
 assert observed['fixture_id']==fixture['id'] and len(observed['cells'])==4;oracle=expected(fixture)
 for c,m in observed['settings'].items():
  for n,v in oracle[c].items():assert F(m[n])==v,(c,n)
  assert m['N']==6 and m['sample_df']==5 and F(m['loss'])==F(m['bias'])**2+F(m['variance_N']) and F(m['variance_N'])==F(m['within_population_component'])+F(m['between_noise_component'])
 for i,cell in enumerate(observed['cells']):
  raw=fixture['cells'][i];mean=sum(map(F,raw))/3;pair=sum((F(a)-F(b))**2 for j,a in enumerate(raw) for b in raw[j+1:]);assert cell['control']=='C'+str(i//2) and cell['noise']==[-1,1][i%2] and cell['observations']==raw and F(cell['mean'])==mean and F(cell['SSE'])==pair/3 and F(cell['sample_variance'])==pair/6

def inspect(r,x):
 assert r['status']=='calculated';s=r['summary'];assert s['input']==x;inspect_metrics(s['selection'],x['selection']);train=expected(x['selection']);minimum=min(m['loss'] for m in train.values());candidates=[c for c,m in train.items() if m['loss']==minimum];winner=candidates[0] if len(candidates)==1 else None
 assert s['winner']==winner and s['selection_candidates']==candidates and F(s['selection_loss'])==minimum and not s['winner_reselected_on_confirmation'];assert s['noise_weights']==['1/2','1/2'] and s['units']['variance_loss']=='arb^2'
 if winner is None:assert s['category']=='tie' and s['confirmation'] is None and s['confirmation_loss'] is None and not s['confirmation_executed'] and s['sequence']==['selection-evaluated','no-unique-choice']
 else:
  inspect_metrics(s['confirmation'],x['confirmation']);loss=expected(x['confirmation'])[winner]['loss'];assert F(s['confirmation_loss'])==loss and s['category']==('pass' if loss<=3 else 'fail') and s['confirmation_executed'] and s['sequence']==['selection-evaluated','setting-locked','confirmation-evaluated']
 assert s['loss_limit']=='3';ctx=r['context'];assert ctx['synthetic'] and ctx['different_fixture_ids_and_arrays'] and not any(ctx[n] for n in ['statistical_independence_established','physical_noise_trial','physical_replication','randomized_execution','signal_factor_varied','tolerance_design','SN_ratio_implemented','orthogonal_array_implemented','causality_or_significance_test'])

def handcheck(r,name):
 s=r['summary'];h=HAND['cases'][name];assert s['winner']==h['winner'] and F(s['selection_loss'])==F(h['selection_loss']) and s['category']==h['category']
 assert (F(s['confirmation_loss']) if s['confirmation_loss'] is not None else None)==(F(h['confirmation_loss']) if h['confirmation_loss'] is not None else None)

def main():
 before=snapshot();rows=json.loads((ROOT/'expected-table.json').read_text())['rows'];valid=[]
 for row in rows:
  raw=run(row['input_json']);r=raw['result'];assert raw['stderr']==''
  if row['expected']['status']=='calculated':assert raw['exit']==0;inspect(r,json.loads(row['input_json']));handcheck(r,row['expected']['hand_case']);valid.append(r)
  else:assert raw['exit']==2 and r=={'status':'input_refusal','code':row['expected']['code'],'summary':None}
 mutants=[]
 for name in ['sample-variance-in-loss','mean-only-selection','confirmation-reselect','same-data-confirmation','bias-not-squared','population-denominator-five','noise-component-erased','units-unsquared','tie-arbitrary-winner','zero-loss-infinity','synthetic-independence-claim','SN-claimed']:
  base=valid[2] if name=='tie-arbitrary-winner' else valid[3] if name=='zero-loss-infinity' else valid[1] if name=='confirmation-reselect' else valid[4] if name=='bias-not-squared' else valid[0];r=copy.deepcopy(base);s=r['summary']
  if name=='sample-variance-in-loss':s['selection']['settings']['C1']['loss']='9/5'
  elif name=='mean-only-selection':s['winner']='C0'
  elif name=='confirmation-reselect':s['winner']='C0';s['winner_reselected_on_confirmation']=True
  elif name=='same-data-confirmation':s['confirmation']=copy.deepcopy(s['selection'])
  elif name=='bias-not-squared':s['selection']['settings']['C1']['loss']='17/3'
  elif name=='population-denominator-five':s['selection']['settings']['C0']['variance_N']='58/5'
  elif name=='noise-component-erased':s['selection']['settings']['C0']['between_noise_component']='0'
  elif name=='units-unsquared':s['units']['variance_loss']='arb'
  elif name=='tie-arbitrary-winner':s['winner']='C0'
  elif name=='zero-loss-infinity':s['selection']['settings']['C0']['loss']='Infinity'
  elif name=='synthetic-independence-claim':r['context']['statistical_independence_established']=True
  else:r['context']['SN_ratio_implemented']=True
  try:inspect(r,s['input'])
  except (AssertionError,KeyError,TypeError,ValueError):mutants.append(name)
  else:raise AssertionError('mutant survived '+name)
 if (ROOT/'observation-data.js').exists():
  fixed=json.loads((ROOT/'observation-data.js').read_text().removeprefix('window.ROBUST_OBSERVATION=').strip().removesuffix(';'));assert fixed==json.loads((ROOT/'observations'/fixed['run_id']/'raw.json').read_text()) and fixed['source_digests']=={n:digest(ROOT/n) for n in SOURCES}
  for row in fixed['rows']:
   r=row['run']['result'];assert json.loads(row['run']['stdout'])==r
   if r['status']=='calculated':inspect(r,json.loads(row['input_json']));handcheck(r,row['expected']['hand_case'])
   else:assert row['run']['exit']==2 and r['code']==row['expected']['code']
 assert before==snapshot();print(json.dumps({'accepted':5,'refused':7,'hand_cases':5,'oracle':'pairwise variance and moment target loss','mutants_rejected':mutants,'unit_sha_mtime_unchanged':True}));return 0
if __name__=='__main__':sys.exit(main())

"""Independent pairwise repeatability / moment reference-error oracle."""
import copy,json,sys
from fractions import Fraction as F
sys.dont_write_bytecode=True
from runner import ROOT,SOURCES,digest,run,snapshot
HAND=json.loads((ROOT/'hand-oracle.json').read_text())
def pair(a):return sum((F(v)-F(w))**2 for i,v in enumerate(a) for w in a[i+1:])
def inspect(r,x):
 assert r['status']=='calculated';s=r['summary'];assert s['input']==x and len(s['cells'])==4;means=[];ss=[];bias=[];flags=[];spread=[]
 for i,c in enumerate(s['cells']):
  a=x['cells'][i];ref=x['references'][i//2];mean=F(sum(a),3);b=mean-ref;sse=pair(a)/3;v=pair(a)/6;mse=F(sum(y*y for y in a),3)-2*ref*mean+ref*ref
  assert c['id']==str(ref)+x['operators'][i%2] and c['reference']==ref and c['operator']==x['operators'][i%2] and c['observations']==a
  for n,o in [('mean',mean),('bias',b),('SSE',sse),('sample_variance',v),('population_variance',pair(a)/9),('reference_MSE',mse)]:assert F(c[n])==o,(i,n)
  assert c['df']==2 and c['bias_flag']==(abs(b)>1) and c['spread_flag']==(v>2) and mse==b*b+pair(a)/9
  means.append(mean);ss.append(sse);bias.append(b)
  if abs(b)>1:flags.append(c['id'])
  if v>2:spread.append(c['id'])
 a=sum(x['cells'],[]);grand=F(sum(a),12);total=pair(a)/12;between=3*(sum(m*m for m in means)-4*grand*grand)
 for n,o in [('within_SSE',sum(ss)),('within_sample_variance',sum(ss)/8),('naive_all_values_sample_variance',pair(a)/132),('all_values_SSE',total),('between_cell_SSE',between),('grand_mean',grand),('aggregate_signed_bias',sum(bias)/4),('max_abs_cell_bias',max(map(abs,bias)))]:assert F(s[n])==o,n
 assert total==sum(ss)+between and s['within_df']==8 and s['fixed_operator_differences']==[str(means[1]-means[0]),str(means[3]-means[2])] and s['bias_flags']==flags and s['spread_flags']==spread
 assert s['category']==('both' if flags and spread else 'bias' if flags else 'spread' if spread else 'within') and s['bias_limit']=='1' and s['sample_variance_limit']=='2' and s['units']=={'response_reference_mean_bias':'arb','SSE_variance_MSE':'arb^2'}
 ctx=r['context'];assert ctx['synthetic'] and ctx['references_assumed_constants'] and not any(v for n,v in ctx.items() if n not in ['synthetic','references_assumed_constants'])
def handcheck(r,name):
 h=HAND['cases'][name];s=r['summary'];assert s['category']==h['category'] and [c['bias'] for c in s['cells']]==h['bias'] and [c['sample_variance'] for c in s['cells']]==h['cell_s2'] and s['within_sample_variance']==h['within'] and s['naive_all_values_sample_variance']==h['naive'] and s['aggregate_signed_bias']==h['aggregate_bias'] and s['fixed_operator_differences']==h['operator_diff']
def main():
 before=snapshot();rows=json.loads((ROOT/'expected-table.json').read_text())['rows'];valid=[]
 for row in rows:
  p=run(row['input_json']);r=p['result'];assert p['stderr']==''
  if row['expected']['status']=='calculated':assert p['exit']==0;inspect(r,json.loads(row['input_json']));handcheck(r,row['expected']['hand_case']);valid.append(r)
  else:assert p['exit']==2 and r=={'status':'input_refusal','code':row['expected']['code'],'summary':None}
 mutants=[]
 for name in ['pooled-values-as-repeatability','population-denominator','bias-sign','bias-as-spread','cancellation-hides-bias','operator-as-population','reference-truth','traceability-claim','process-variation-claim','RR-complete','units-unsquared','MSE-as-sample-variance']:
  r=copy.deepcopy(valid[4] if name=='cancellation-hides-bias' else valid[1] if name=='bias-as-spread' else valid[0]);s=r['summary']
  if name=='pooled-values-as-repeatability':s['within_sample_variance']=s['naive_all_values_sample_variance']
  elif name=='population-denominator':s['cells'][0]['sample_variance']='2/3'
  elif name=='bias-sign':s['cells'][0]['bias']='1'
  elif name=='bias-as-spread':s['cells'][0]['spread_flag']=True
  elif name=='cancellation-hides-bias':s['bias_flags']=[]
  elif name=='operator-as-population':r['context']['population_operator_reproducibility_estimated']=True
  elif name=='reference-truth':r['context']['reference_truth_guaranteed']=True
  elif name=='traceability-claim':r['context']['calibration_traceability_established']=True
  elif name=='process-variation-claim':r['context']['product_process_variation_estimated']=True
  elif name=='RR-complete':r['context']['full_gage_RR_components_implemented']=True
  elif name=='units-unsquared':s['units']['SSE_variance_MSE']='arb'
  else:s['cells'][0]['sample_variance']=s['cells'][0]['reference_MSE']
  try:inspect(r,s['input'])
  except (AssertionError,TypeError,ValueError,KeyError):mutants.append(name)
  else:raise AssertionError('surviving mutant '+name)
 if (ROOT/'observation-data.js').exists():
  raw=json.loads((ROOT/'observation-data.js').read_text().removeprefix('window.MSA_OBSERVATION=').strip().removesuffix(';'));assert raw==json.loads((ROOT/'observations'/raw['run_id']/'raw.json').read_text()) and raw['source_digests']=={n:digest(ROOT/n) for n in SOURCES}
  for row in raw['rows']:
   r=row['run']['result'];assert json.loads(row['run']['stdout'])==r
   if r['status']=='calculated':inspect(r,json.loads(row['input_json']));handcheck(r,row['expected']['hand_case'])
   else:assert r['code']==row['expected']['code'] and row['run']['exit']==2
 assert before==snapshot();print(json.dumps({'hand_cases':5,'refused':7,'mutants_rejected':mutants,'oracle':'pairwise within variance and reference second moments','unit_sha_mtime_unchanged':True}));return 0
if __name__=='__main__':sys.exit(main())

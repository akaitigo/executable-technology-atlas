"""Independent run-level OLS elimination/rank/nested RSS oracle, not cell-contrast implementation."""
import copy,json,sys
from fractions import Fraction as F
sys.dont_write_bytecode=True
from runner import ROOT,SOURCES,digest,run,snapshot
HAND=json.loads((ROOT/'hand-oracle.json').read_text())
def solve(matrix,rhs):
 a=[[F(v) for v in row]+[F(y)] for row,y in zip(matrix,rhs)];n=len(a);rank=0
 for col in range(n):
  pivot=next((i for i in range(rank,n) if a[i][col]),None)
  if pivot is None:continue
  a[rank],a[pivot]=a[pivot],a[rank];v=a[rank][col];a[rank]=[x/v for x in a[rank]]
  for i in range(n):
   if i!=rank:
    v=a[i][col];a[i]=[x-v*y for x,y in zip(a[i],a[rank])]
  rank+=1
 assert rank==n
 return [row[-1] for row in a],rank

def fit(design,y,columns):
 d=[[F(row[c]) for c in columns] for row in design];q=len(columns)
 gram=[[sum(row[i]*row[j] for row in d) for j in range(q)] for i in range(q)];rhs=[sum(row[i]*v for row,v in zip(d,y)) for i in range(q)];beta,rank=solve(gram,rhs);pred=[sum(v*b for v,b in zip(row,beta)) for row in d]
 return beta,rank,pred,sum((v-p)**2 for v,p in zip(y,pred))

def oracle(cells):
 levels=[(-1,-1),(1,-1),(-1,1),(1,1)];design=[];y=[]
 for raw,(a,b) in zip(cells,levels):
  for v in raw:design.append([1,a,b,a*b]);y.append(F(v))
 beta,rank,pred,residual=fit(design,y,[0,1,2,3]);_,_,_,total=fit(design,y,[0]);ss={}
 for name,col in [('A',1),('B',2),('AB',3)]:ss[name]=fit(design,y,[i for i in range(4) if i!=col])[3]-residual
 means=[pred[i*3] for i in range(4)];return beta,rank,means,ss,residual,total

def inspect(r,x):
 assert r['status']=='calculated' and len(r['cells'])==4;s=r['summary'];beta,rank,means,ss,within,total=oracle(x['cells']);assert s['input']==x and s['N']==12 and s['r']==3
 assert [F(s['coefficients'][n]) for n in ['I','A','B','AB']]==beta
 assert [F(v) for v in s['means']]==means
 for n,c in zip(['A','B','AB'],beta[1:]):assert F(s['effects'][n])==2*c and F(s['SS'][n])==ss[n]
 assert F(s['SS']['within'])==within and F(s['SS']['total'])==total and sum(ss.values())+within==total
 assert s['df']=={'A':1,'B':1,'AB':1,'within':12-rank,'total':11} and F(s['MSE'])==within/(12-rank)
 assert F(s['DOD'])==4*beta[3] and F(s['conditional_A']['B-'])==2*(beta[1]-beta[3]) and F(s['conditional_A']['B+'])==2*(beta[1]+beta[3])
 assert s['category']==('crossover' if (beta[1]-beta[3])*(beta[1]+beta[3])<0 else 'interaction' if beta[3] else 'additive')
 _,_,addpred,addrss=fit([[1,*lev,lev[0]*lev[1]] for lev in [(-1,-1),(1,-1),(-1,1),(1,1)] for _ in range(3)],[F(v) for c in x['cells'] for v in c],[0,1,2]);assert [F(v) for v in s['main_only_fitted_means']]==[addpred[i*3] for i in range(4)] and F(s['main_only_SSE'])==addrss
 # Independent 0/1 additive interpolation on only three cell means, rank3; fourth is not observed.
 observed_design=[[1,0,0],[1,1,0],[1,0,1]];ofatbeta,ofatrank,_,_=fit(observed_design,means[:3],[0,1,2]);predmissing=sum(ofatbeta);o=s['ofat'];assert ofatrank==3 and o['observed_cells']==[0,1,2] and o['missing_cell']==3 and not o['interaction_identifiable']
 assert F(o['missing_prediction'])==predmissing and F(o['actual_missing_mean'])==means[3] and F(o['prediction_error'])==means[3]-predmissing==4*beta[3]
 for i,cell in enumerate(r['cells']):
  raw=x['cells'][i];mean=sum(map(F,raw))/3;err=sum((F(v)-mean)**2 for v in raw);assert cell['observations']==raw and F(cell['mean'])==mean and F(cell['SSE'])==err and F(cell['sample_variance'])==err/2
 assert s['units']==HAND['units'];ctx=r['context'];assert ctx['synthetic'] and not any(ctx[n] for n in ['physical_replication_performed','randomized_execution','temporal_run_order_observed','significance_test_performed','causal_claim']) and ctx['coding']==[-1,1] and ctx['effect_equals']=='2*coefficient' and ctx['DOD_equals']=='4*coefficientAB'

def handcheck(r,name):
 h=HAND['cases'][name];s=r['summary'];assert [F(v) for v in s['means']]==h['means'] and [F(s['effects'][n]) for n in ['A','B','AB']]==h['effects'] and [F(s['coefficients'][n]) for n in ['I','A','B','AB']]==h['beta'] and [F(s['SS'][n]) for n in ['A','B','AB','within','total']]==h['SS'] and F(s['MSE'])==h['MSE'] and F(s['DOD'])==h['DOD'] and F(s['ofat']['missing_prediction'])==h['ofat_missing_prediction']

def main():
 before=snapshot();rows=json.loads((ROOT/'expected-table.json').read_text())['rows'];valid=[]
 for row in rows:
  raw=run(row['input_json']);r=raw['result'];assert raw['stderr']==''
  if row['expected']['status']=='calculated':assert raw['exit']==0;inspect(r,json.loads(row['input_json']));handcheck(r,row['expected']['hand_case']);valid.append(r)
  else:assert raw['exit']==2 and r=={'status':'input_refusal','code':row['expected']['code'],'summary':None,'cells':None}
 mutants=[]
 for name in ['main-only-erases-AB','coefficient-as-effect','DOD-as-AB-effect','within-df-Nminus1','variance-divide-r','SSE-mixed-with-effect','units-not-squared','OFAT-fourth-as-observed','synthetic-as-randomized','crossover-no-interaction']:
  r=copy.deepcopy(valid[2]);s=r['summary']
  if name=='main-only-erases-AB':s['coefficients']['AB']='0'
  elif name=='coefficient-as-effect':s['effects']['AB']=s['coefficients']['AB']
  elif name=='DOD-as-AB-effect':s['effects']['AB']=s['DOD']
  elif name=='within-df-Nminus1':s['df']['within']=11
  elif name=='variance-divide-r':r['cells'][0]['sample_variance']='2/3'
  elif name=='SSE-mixed-with-effect':s['SS']['AB']=s['effects']['AB']
  elif name=='units-not-squared':s['units']['MSE']='arb'
  elif name=='OFAT-fourth-as-observed':s['ofat']['observed_cells']=[0,1,2,3]
  elif name=='synthetic-as-randomized':r['context']['randomized_execution']=True
  else:s['category']='additive'
  try:inspect(r,s['input'])
  except (AssertionError,KeyError,TypeError):mutants.append(name)
  else:raise AssertionError('mutant survived '+name)
 if (ROOT/'observation-data.js').exists():
  raw=json.loads((ROOT/'observation-data.js').read_text().removeprefix('window.FACTORIAL_OBSERVATION=').strip().removesuffix(';'));assert raw==json.loads((ROOT/'observations'/raw['run_id']/'raw.json').read_text());assert raw['source_digests']=={n:digest(ROOT/n) for n in SOURCES}
  for row in raw['rows']:
   r=row['run']['result'];assert json.loads(row['run']['stdout'])==r
   if r['status']=='calculated':inspect(r,json.loads(row['input_json']));handcheck(r,row['expected']['hand_case'])
   else:assert row['run']['exit']==2 and r['code']==row['expected']['code']
 assert before==snapshot(),'normal checker mutated unit';print(json.dumps({'accepted':5,'refused':7,'OLS_rank':4,'within_df':8,'hand_checks':5,'mutants_rejected':mutants,'unit_sha_mtime_unchanged':True}));return 0
if __name__=='__main__':sys.exit(main())

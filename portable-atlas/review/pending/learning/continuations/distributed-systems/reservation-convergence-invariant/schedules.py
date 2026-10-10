import itertools,json,sys
from pathlib import Path
from execute import execute
from oracle import check
P=Path(__file__).resolve().parent
def collect():
 base=json.loads((P/'fixture.json').read_text())[0]['input'];pos=list(itertools.permutations(['A>B','B>A']))+list(itertools.permutations(['A>B','A>B','B>A','B>A']));unique=sorted(set(pos));runs=[]
 for s in unique:
  x=dict(base,schedule=list(s));raw=execute(json.dumps(x));check(raw['result'],x)
  for p,v in raw['result']['policies'].items():
   f=v['final'];assert f['converged'];assert f['local_sets']==({'A':['a','b'],'B':['a','b']} if p=='optimistic' else {'A':['a'],'B':['a']});assert f['global_business_ok']==(p=='deferred');assert sum(f['delivery_count'].values())==len(s);assert f['delivered_set']=={'A':['B>A'],'B':['A>B']}
  runs.append(dict(schedule=list(s),multiplicity=pos.count(s),raw=raw))
 return dict(status='passed',positional=len(pos),unique=len(unique),runs=runs)
if __name__=='__main__':
 r=collect()
 if sys.argv[1:]==['--record']:(P/'evidence/schedules.json').write_text(json.dumps(r,indent=2)+'\n')
 print(json.dumps(dict(status=r['status'],positional=r['positional'],unique=r['unique'])))

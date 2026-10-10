import itertools,json
from fractions import Fraction
from pathlib import Path
ROOT=Path(__file__).resolve().parent
C=json.loads((ROOT/'contracts.json').read_text())
def f(v):return str(v.numerator)+'/'+str(v.denominator)
class Refusal(ValueError):pass
def validate(r):
    if set(r)!= {'answers','coin_profile'}:raise Refusal('field-set')
    if type(r['answers']) is not int:raise Refusal('answers-type')
    if r['answers'] not in (1,2):raise Refusal('answers-range')
    if r['coin_profile']!='fair-independent':raise Refusal('coin-profile')
def calculate(n):
    outcomes=[''.join(map(str,b)) for b in itertools.product((0,1),repeat=n)];paths={};distribution={}
    for x in (0,1):
        rows=[];dist={o:Fraction(0) for o in outcomes}
        for coins in itertools.product((0,1),repeat=2*n):
            answer=''.join(str(x if coins[2*i]==0 else coins[2*i+1]) for i in range(n));mass=Fraction(1,4**n);dist[answer]+=mass
            rows.append({'coins':list(coins),'output':answer,'mass':f(mass)})
        paths[str(x)]=rows;distribution[str(x)]=dist
    singleton=[];events=[]
    for mask in range(1,2**len(outcomes)):
        subset=[o for i,o in enumerate(outcomes) if mask&(1<<i)];p0=sum((distribution['0'][o] for o in subset),Fraction(0));p1=sum((distribution['1'][o] for o in subset),Fraction(0));ratio01=p0/p1;ratio10=p1/p0
        row={'outputs':subset,'p0':f(p0),'p1':f(p1),'ratio_0_over_1':f(ratio01),'ratio_1_over_0':f(ratio10)};events.append(row)
        if len(subset)==1:singleton.append(row)
    maximum=max(Fraction(r[key]) for r in events for key in ('ratio_0_over_1','ratio_1_over_0'));bound=Fraction(3**n)
    violates3=[r for r in events if Fraction(r['ratio_0_over_1'])>3 or Fraction(r['ratio_1_over_0'])>3]
    marginal={x:{b:sum((v for o,v in d.items() if o[0]==b),Fraction(0)) for b in ('0','1')} for x,d in distribution.items()}
    marginal_max=max(marginal[a][b]/marginal[z][b] for a,z in (('0','1'),('1','0')) for b in ('0','1'))
    return {'paths':paths,'distribution':{x:{o:f(v) for o,v in d.items()} for x,d in distribution.items()},'path_count_per_input':4**n,'path_mass':f(Fraction(1,4**n)),'singleton_ratios':singleton,'nonempty_events':events,'max_ratio':f(maximum),'normal_bound':f(bound),'normal_bound_holds':maximum<=bound,'epsilon_symbolic':'ln(3)' if n==1 else '2*ln(3)','delta':'0/1','reused_single_bound':'3/1','reused_bound_actually_holds':maximum<=3,'faulty_marginal_max_ratio':f(marginal_max),'faulty_marginal_only_claim_holds':marginal_max<=3,'faulty_claim_basis':'reuse single-answer maximum3 without checking joint output','events_violating_reused_bound':violates3,'random_samples':0}
def execute():
    rows=[]
    for s in C['cases']:
        r={'answers':s['answers'],'coin_profile':'fair-independent'};validate(r);rows.append({'id':s['id'],'status':'accepted-calculation','request':r,**calculate(s['answers'])})
    for s in C['refusals']:
        try:validate(s['request'])
        except Refusal as e:rows.append({'id':s['id'],'status':'expected-refusal','request':s['request'],'reason':str(e),'distribution_created':False})
        else:raise AssertionError('unexpected contract acceptance')
    return {'rows':rows,'adjacency':C['adjacency'],'calculation':'exact full distribution, not sampling, not existing 12-row release DP conversion'}
if __name__=='__main__':print(json.dumps(execute(),ensure_ascii=False))

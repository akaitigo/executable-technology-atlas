"""Atlas: two fixed hypotheses, exact finite probabilities, no sampling."""
from fractions import Fraction
from itertools import product
from math import comb

PS=(Fraction(1,4),Fraction(3,4))
def calculate(request):
    def refuse(reason):return {'accepted':False,'reason':reason,'payload':None}
    if type(request) is not dict or set(request)!= {'weights','observation'}:
        return refuse('request-invalid')
    w=request['weights']
    if type(w) is not list or len(w)!=2 or any(type(x) is not int or not 0<=x<=9 for x in w) or sum(w)==0:
        return refuse('prior-invalid')
    observation=request['observation']
    if type(observation) is not dict:return refuse('observation-invalid')
    if observation.get('type')=='sequence':
        if set(observation)!= {'type','value'} or type(observation['value']) is not str or len(observation['value'])>3 or any(x not in 'HT' for x in observation['value']):
            return refuse('observation-invalid')
        n=len(observation['value']);k=observation['value'].count('H');multiplicity=1
    elif observation.get('type')=='count':
        if set(observation)!= {'type','n','k'} or type(observation['n']) is not int or type(observation['k']) is not int or not 0<=observation['k']<=observation['n']<=3:
            return refuse('observation-invalid')
        n=observation['n'];k=observation['k'];multiplicity=comb(n,k)
    else:return refuse('observation-invalid')
    prior=[Fraction(x,sum(w)) for x in w]
    likelihood=[multiplicity*p**k*(1-p)**(n-k) for p in PS]
    joint=[a*c for a,c in zip(prior,likelihood)]
    evidence=sum(joint,Fraction(0));posterior=[x/evidence for x in joint]
    ignored=[x/sum(likelihood,Fraction(0)) for x in likelihood]
    table=[]
    for chars in product('HT',repeat=3):
        s=''.join(chars);heads=s.count('H')
        mass=[p**heads*(1-p)**(3-heads) for p in PS]
        selected=s.startswith(observation['value']) if observation['type']=='sequence' else s[:n].count('H')==k
        table.append({'sequence':s,'conditionalMass':[str(x) for x in mass],
                      'jointMass':[str(a*c) for a,c in zip(prior,mass)],'inObservedEvent':selected})
    return {'accepted':True,'reason':'ok','payload':{'hypotheses':[str(p) for p in PS],
        'n':n,'k':k,'multiplicity':multiplicity,'prior':[str(x) for x in prior],
        'likelihood':[str(x) for x in likelihood],'joint':[str(x) for x in joint],
        'evidence':str(evidence),'posterior':[str(x) for x in posterior],
        'faults':{'likelihoodAsPosterior':[str(x) for x in likelihood],
                  'ignoresPrior':[str(x) for x in ignored]},'jointTable':table}}

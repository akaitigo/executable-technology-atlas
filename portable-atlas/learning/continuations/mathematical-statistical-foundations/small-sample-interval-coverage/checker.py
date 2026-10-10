"""256 sequences, Fraction weights + squared inequality; no producer/comb/sqrt import."""
import copy,hashlib,json,re
from itertools import product
from fractions import Fraction as F
from datetime import datetime
from pathlib import Path
ROOT=Path(__file__).resolve().parent
HAND={'0.1':([1,2,3],F(56450844,100000000)),'0.5':([2,3,4,5,6],F(119,128)),'0.9':([5,6,7],F(56450844,100000000))}
def oracle(p):
    masses=[F(0) for _ in range(9)];coverage=F(0);covered=[]
    for k in range(9):
        estimate=F(k,8)
        if (p-estimate)**2<=F(49,25)**2*estimate*(1-estimate)/8:covered.append(k)
    for sequence in product((0,1),repeat=8):
        weight=F(1)
        for outcome in sequence:weight*=p if outcome else 1-p
        k=sum(sequence);masses[k]+=weight
        if k in covered:coverage+=weight
    return masses,covered,coverage
def inspect(raw):
    issues=[]
    if len(raw['accepted'])!=3 or [c['input'] for c in raw['accepted']]!=[{'n':8,'p':p,'z':'1.96'} for p in HAND]:return ['finite input denominator']
    for c in raw['accepted']:
        p=c['input']['p'];masses,covered,coverage=oracle(F(p));handk,handcov=HAND[p]
        if covered!=handk or coverage!=handcov:issues.append('independent derivation disagrees with hand check')
        if c['status']!='calculated' or len(c['rows'])!=9 or c['context']['clipping'] is not False or c['context']['precision']!=40:issues.append(p+': calculation contract')
        if F(c['coverage'])!=coverage or F(c['probability_sum'])!=1 or sum(masses)!=1:issues.append(p+': exact coverage / mass')
        for k,row in enumerate(c['rows']):
            estimate=F(k,8);variance=estimate*(1-estimate)/8;lower,upper,width=map(F,(row['lower'],row['upper'],row['width']))
            if row['k']!=k or F(row['estimate'])!=estimate or F(row['variance'])!=variance or F(row['binomial_mass'])!=masses[k] or row['covers_true_p']!=(k in covered):issues.append(p+': independent sequence mass/coverage')
            if abs(lower+upper-2*estimate)>F(1,10**36) or abs((upper-lower)-width)>F(1,10**36) or abs((width/2)**2-F(49,25)**2*variance)>F(1,10**36):issues.append(p+': Wald endpoints squared')
            if row['outside_0_1']!=(lower<0 or upper>1):issues.append(p+': unclipped flag')
            if k in (0,8) and (width!=0 or lower!=estimate or upper!=estimate):issues.append(p+': degenerate boundary')
        if not (F(c['rows'][1]['lower'])<0 and F(c['rows'][7]['upper'])>1):issues.append(p+': clipping changed')
        if datetime.fromisoformat(c['started_at'])>datetime.fromisoformat(c['ended_at']):issues.append('UTC')
    reasons=['invalid-n','invalid-n','invalid-p','invalid-p','invalid-p','invalid-z','invalid-z']
    if len(raw['refused'])!=7 or [c.get('reason') for c in raw['refused']]!=reasons or any(c['status']!='refused' or c['rows'] is not None or 'coverage' in c for c in raw['refused']):issues.append('expected refusals separated from calculations')
    return issues
def main():
    raw=json.loads((ROOT/'observation-data.js').read_text().removeprefix('window.WALD_OBSERVATION = ').strip().removesuffix(';'));folder=ROOT/'observations'/raw['run_id']
    assert raw==json.loads((folder/'raw.json').read_text()),'UI binding'
    contract=json.loads((ROOT/'contracts.json').read_text());assert contract==json.loads((folder/'contracts.json').read_text())
    assert [c['input'] for c in raw['refused']]==[c['input'] for c in contract['refusals']]
    for name,digest in raw['source_digests'].items():assert hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==digest,'source '+name
    for name,info in json.loads((folder/'artifact-index.json').read_text())['artifacts'].items():
        data=(folder/name).read_bytes();assert len(data)==info['bytes'] and hashlib.sha256(data).hexdigest()==info['sha256'],name
    command=json.loads((folder/'command.json').read_text());observed=json.loads(command['stdout']);assert observed['accepted']==raw['accepted'] and observed['refused']==raw['refused'] and command['exit']==0 and command['stderr']==''
    assert not inspect(raw),inspect(raw)
    negatives=[]
    for label in ('nominal-as-exact','clipped','zero-width-hidden','refusal-as-success'):
        bad=copy.deepcopy(raw)
        if label=='nominal-as-exact':bad['accepted'][0]['coverage']='0.95'
        elif label=='clipped':bad['accepted'][0]['rows'][1]['lower']='0'
        elif label=='zero-width-hidden':bad['accepted'][1]['rows'][0]['width']='0.1'
        else:bad['refused'][0]['status']='calculated'
        assert inspect(bad),label;negatives.append(label)
    from route import ROUTES,UNSUPPORTED,route
    assert all(route(q)['target']==t and not route(q)['executed'] for q,t in ROUTES.items())
    assert all(not route(q)['supported'] and not route(q)['executed'] for q in UNSUPPORTED)
    skill=ROOT/'skills/atlas-small-sample-interval-coverage/SKILL.md'
    for target in re.findall(r'\]\(([^)]+)\)',skill.read_text()):assert (skill.parent/target).resolve().is_file(),target
    print(json.dumps({'accepted':3,'expected_refusals':7,'enumerated_sequences_per_p':256,'exact_coverages':{p:str(oracle(F(p))[2]) for p in HAND},'negative_controls':negatives,'skill_routes':'6 normal/4 unsupported, structural only','read_only':True,'binding':True},ensure_ascii=False))
if __name__=='__main__':main()

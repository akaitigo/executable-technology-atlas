"""Independent Fraction/integer + hand-cent oracle. No calculator/runner/Decimal imports."""
import copy
import hashlib
import json
import re
import sys
from fractions import Fraction
from pathlib import Path
ROOT=Path(__file__).resolve().parent
# source, all leaves, A, B, C, unallocated-direct, unallocated-shared, shared-assigned, gap
EXPECTED={
 'normal-weighted':(52,52,24,28,0,0,0,12,0),
 'equal-conserved':(100,100,24,33,43,0,0,10,0),
 'equal-naive':(100,99,23,33,43,0,0,9,1),
 'round-up-conserved':(11,11,4,4,3,0,0,11,0),
 'round-up-naive':(11,12,4,4,4,0,0,12,-1),
 'tie-reordered':(100,100,24,33,43,0,0,10,0),
 'missing-tag':(60,60,25,5,0,30,0,10,0),
 'no-basis':(30,30,20,0,0,0,10,0,0),
 'one-cent':(1,1,1,0,0,0,0,1,0),
 'fractional-usage':(53,53,40,13,0,0,0,10,0),
 'zero-shared':(40,40,20,20,0,0,0,0,0),
}
REJECTED={'zero-quantity':'invalid-quantity','negative-quantity':'invalid-quantity','float-quantity':'invalid-numeric-string','nonfinite-rate':'invalid-numeric-string','duplicate-usage':'duplicate-or-invalid-usage-id','zero-weight':'invalid-weight'}


def sha(raw):return hashlib.sha256(raw).hexdigest()
def half_up(value):
    # Inputs here are nonnegative. Integer arithmetic gives exact rational rounding.
    return (value.numerator*2+value.denominator)//(value.denominator*2)

def summary(tree):
    return (tree['source_total_cents'],tree['allocated_total_cents'],
      *[tree['teams'][team]['direct_cents']+tree['teams'][team]['shared_cents'] for team in ('A','B','C')],
      tree['unallocated']['direct_cents'],tree['unallocated']['shared_cents'],tree['shared_assigned_cents'],tree['rounding_gap_cents'])

def inspect(name,data,result):
    problems=[]
    want_context={'precision':28,'rounding':'ROUND_HALF_UP','Emin':-999999,'Emax':999999,'FloatOperation':'trapped','binary_float':'prohibited','money_unit':'fictional XCU; 100 cents = 1 XCU'}
    if result['context']!=want_context:problems.append('context')
    raw=result['raw']
    if raw[0]['stage']!='input' or raw[0]['input']!=data or raw[0]['decimal_context']!=want_context:problems.append('raw input/context')
    if name in REJECTED:
        if result['status']!=REJECTED[name] or result['tree'] is not None or len(raw)!=2 or raw[-1].get('reason')!=REJECTED[name] or not raw[-1].get('state_unchanged'):problems.append('rejected without cost tree')
        return problems
    if result['status']!='calculated' or not result['tree']:return ['missing cost tree']
    tree=result['tree']
    if summary(tree)!=EXPECTED[name]:problems.append('literal hand cents')
    pool=half_up(Fraction(data['shared_amount'])*100)
    expected_direct=[];direct_totals={team:0 for team in ('A','B','C')};unc=0;reasons=[]
    for usage in data['usage']:
        exact=Fraction(usage['quantity'])*Fraction(data['ratecard'][usage['sku']]);charge=half_up(exact*100)
        target=usage.get('team') if usage.get('team') in direct_totals else 'unallocated'
        if target=='unallocated':
            unc+=charge;reason='missing-tag' if usage.get('team') in (None,'') else 'unknown-tag';reasons.append({'id':usage['id'],'reason':reason,'cents':charge})
        else:direct_totals[target]+=charge;reason=None
        expected_direct.append((usage['id'],exact,charge,target,reason))
    if len(tree['direct_rows'])!=len(expected_direct):problems.append('direct denominator')
    for row,want in zip(tree['direct_rows'],expected_direct):
        if (row['id'],Fraction(row['exact_XCU']),row['charged_cents'],row['destination'],row['reason'])!=want:problems.append('Fraction direct cost')
    if tree['source_direct_cents']!=sum(row[2] for row in expected_direct) or tree['source_shared_cents']!=pool:problems.append('source rounding')
    weights=data['weights'];shares={team:Fraction(pool*weight,sum(weights.values())) for team,weight in weights.items()}
    floors={team:exact.numerator//exact.denominator for team,exact in shares.items()}
    remaining=pool-sum(floors.values()) if weights else 0
    rank=sorted(weights,key=lambda team:(-(shares[team]-floors[team]),team))
    assigned={team:floors[team]+int(team in rank[:remaining]) if data['policy']=='conserved' else half_up(shares[team]) for team in weights}
    if tree['residual_cents']!=remaining or tree['remainder_order']!=rank:problems.append('Fraction remainder rank')
    for team in direct_totals:
        if tree['teams'][team]!={'direct_cents':direct_totals[team],'shared_cents':assigned.get(team,0)}:problems.append('Fraction leaf '+team)
    if len(tree['shares'])!=len(weights):problems.append('share denominator')
    for row in tree['shares']:
        team=row['team']
        if team not in shares:problems.append('unknown share');continue
        if row['weight']!=weights[team] or row['denominator']!=sum(weights.values()) or row['floor_cents']!=floors[team] or row['assigned_cents']!=assigned[team]:problems.append('share row')
        # Raw Decimal repeating fractions are approximations; expected integer cents/rank are exact.
        if abs(Fraction(row['exact_share_cents'])-shares[team])>=Fraction(1,10**24):problems.append('share precision')
        want_extra=int(team in rank[:remaining]) if data['policy']=='conserved' else None
        if row['extra_cents']!=want_extra:problems.append('extra cent recipient')
    if not weights:reasons.append({'id':'shared','reason':'no-allocation-basis','cents':pool})
    if tree['unallocated']!={'direct_cents':unc,'shared_cents':pool if not weights else 0,'reasons':reasons}:problems.append('unallocated explicit')
    leaves=sum(sum(v.values()) for v in tree['teams'].values())+unc+(pool if not weights else 0)
    if leaves!=tree['allocated_total_cents'] or tree['source_total_cents']-leaves!=tree['rounding_gap_cents']:problems.append('cost tree addition')
    if data['policy']=='conserved' and tree['rounding_gap_cents']!=0:problems.append('conservation')
    if raw[-1].get('tree')!=tree or raw[-1].get('conserved')!=(tree['rounding_gap_cents']==0):problems.append('raw final tree')
    if len([x for x in raw if x['stage']=='direct-line'])!=len(expected_direct):problems.append('raw direct denominator')
    if [x['at'] for x in raw]!=sorted(x['at'] for x in raw):problems.append('timestamps')
    return problems

def report(folder):
    assert {p.name for p in folder.iterdir() if p.is_dir()}==set(EXPECTED)|set(REJECTED),'case denominator'
    rows=[]
    for name in list(EXPECTED)+list(REJECTED):
        data=json.loads((folder/name/'input.json').read_text());result=json.loads((folder/name/'result.json').read_text())
        issues=inspect(name,data,result)
        rows.append({'id':name,'expected':EXPECTED.get(name,REJECTED.get(name)),'actual':summary(result['tree']) if result['tree'] else result['status'],'matches':not issues,'issues':issues,'oracle':'independent hand cents + Fraction/integer rounding and allocation'})
    return {'oracle':'no calculator/runner/Decimal imports; exact Fraction + literal hand-cent tuples','rows':rows}

def check():
    payload=json.loads((ROOT/'observation-data.js').read_text().removeprefix('window.FINOPS_OBSERVATION = ').removesuffix(';\n'))
    folder=ROOT/payload['directory'];index=json.loads((folder/'artifact-index.json').read_text());run=json.loads((folder/'run.json').read_text())
    assert set(index)=={p.relative_to(folder).as_posix() for p in folder.rglob('*') if p.is_file() and p.name!='artifact-index.json'}
    for file,digest in index.items():assert sha((folder/file).read_bytes())==digest,'artifact '+file
    for file,digest in run['source_digests'].items():assert sha((ROOT/file).read_bytes())==digest,'stale source '+file
    assert payload['run']==run and run['started_at']<=run['completed_at']
    assert {case['id'] for case in payload['cases']}==set(EXPECTED)|set(REJECTED)
    for case in payload['cases']:
        name=case['id'];data=case['input'];result=case['result']
        assert data==json.loads((folder/name/'input.json').read_text()) and result==json.loads((folder/name/'result.json').read_text()),'UI input/raw/result binding'
        if result['tree']:
            forged=copy.deepcopy(result);forged['tree']['teams']['A']['shared_cents']+=1
            assert inspect(name,data,forged),'leaf negative control'
            forged=copy.deepcopy(result);forged['tree']['unallocated']['direct_cents']+=1
            assert inspect(name,data,forged),'unallocated negative control'
            forged=copy.deepcopy(result);forged['context']['rounding']='ROUND_HALF_EVEN'
            assert inspect(name,data,forged),'rounding context negative control'
    actual=report(folder);assert all(x['matches'] for x in actual['rows']),actual
    assert json.loads(json.dumps(actual))==payload['oracle']==json.loads((folder/'oracle-report.json').read_text())
    sources=json.loads((ROOT/'sources.json').read_text());assert len(sources)>=4 and all(x['url'].startswith('https://') and x['locator'] and x['binding'] for x in sources)
    for file in ('README.md','index.html','skills/atlas-finops-cost-engineering/SKILL.md'):
        text=(ROOT/file).read_text()
        for href in re.findall(r'(?:href="|\]\()([^"\)]+)',text):
            if ':' not in href and not href.startswith('#'):assert (ROOT/Path(file).parent/href.split('#')[0]).is_file(),(file,href)
    for term in ('前提','主要概念','実務判断','限界','次の実験','原典'):
        assert term in (ROOT/'README.md').read_text() and term in (ROOT/'index.html').read_text(),term
    print(json.dumps({'cases':len(actual['rows']),'matches':True,'independent_Fraction':True,'read_only':True,'source_binding':True,'negative_controls':['leaf-cent','unallocated','rounding-context']}))
if __name__=='__main__':
    if len(sys.argv)==3 and sys.argv[1]=='--oracle-json':print(json.dumps(report(Path(sys.argv[2])),ensure_ascii=False))
    elif len(sys.argv)==1:check()
    else:raise SystemExit('usage: checker.py [--oracle-json RUN_DIRECTORY]')

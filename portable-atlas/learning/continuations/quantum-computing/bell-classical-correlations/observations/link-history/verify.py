# SPDX-License-Identifier: Apache-2.0
import argparse,copy,hashlib,itertools,json,math,platform,re,sys
from fractions import Fraction as F
from pathlib import Path
from datetime import datetime,timezone
sys.dont_write_bytecode=True
import quantum as q,route
HERE=Path(__file__).resolve().parent
SOURCES=['quantum.py','verify.py','route.py','serve.py','fixtures.json','hand-oracle.json','README.md','VERIFICATION.md','index.html','coverage.json','sources.json','skills/atlas-bell-classical-correlations/SKILL.md']
SIGNS=[[1,1,1,1],[1,-1,1,-1],[1,1,-1,-1],[1,-1,-1,1]] # handwritten H⊗H times2

def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def close(a,b):assert math.isclose(a,float(b),rel_tol=0,abs_tol=1e-12),(a,b)
def matrix_close(actual,expected):
    assert len(actual)==len(expected)
    for ar,er in zip(actual,expected):
        for (real,imag),v in zip(ar,er):close(real,v);close(imag,0)
def reduced(m):
    # Literal block sums, independent of producer bit/tensor indexing loops.
    a=[[m[0][0]+m[1][1],m[0][2]+m[1][3]],[m[2][0]+m[3][1],m[2][2]+m[3][3]]]
    b=[[m[0][0]+m[2][2],m[0][1]+m[2][3]],[m[1][0]+m[3][2],m[1][1]+m[3][3]]]
    return a,b

def det(m):
    total=F(0);n=len(m)
    for perm in itertools.permutations(range(n)):
        term=F(-1 if sum(perm[i]>perm[j] for i in range(n) for j in range(i+1,n))%2 else 1)
        for i in range(n):term*=m[i][perm[i]]
        total+=term
    return total

def check_metrics(actual,m):
    trace=sum(m[i][i] for i in range(4));purity=sum(m[i][j]*m[j][i] for i in range(4) for j in range(4))
    close(actual['trace'][0],trace);close(actual['trace'][1],0);close(actual['purity'],purity);close(actual['coherence_00_11'][0],m[0][3]);close(actual['coherence_00_11'][1],0);close(actual['coherence_magnitude'],abs(m[0][3]))
    assert actual['hermitian'] and actual['hermitian_residual']<=1e-12
    assert all(m[i][j]==m[j][i] for i in range(4) for j in range(4))
    # Exact all 15 principal minors of each literal Hermitian matrix: finite PSD check.
    for size in range(1,5):
        for subset in itertools.combinations(range(4),size):assert det([[m[i][j] for j in subset] for i in subset])>=0

def check(r,expected,matrices):
    pre=matrices[expected['prepared']];matrix_close(r['prepared_density'],pre);check_metrics(r['prepared_metrics'],pre)
    for actual,m in zip(r['prepared_reduced'],reduced(pre)):matrix_close(actual,m)
    close(r['prepared_metrics']['purity'],F(expected['purity']))
    assert r['comparison_to_intended']==expected['comparison']
    if r['branch_norms'] is not None:
        weighted=sum(row['weight']*row['norm_squared'] for row in r['branch_norms']);close(weighted,sum(pre[i][i] for i in range(4)))
    key=r['basis'];prob=expected['prob'+key]
    if prob is None:
        assert r['status']=='REJECTED' and r['joint_probabilities'] is r['measurement_density'] is r['measurement_metrics'] is r['marginal_probabilities'] is None
        assert r['trace'][-1]['stage']=='reject_measurement';return
    assert r['status']=='MEASURED';m=matrices[expected[key]];matrix_close(r['measurement_density'],m);check_metrics(r['measurement_metrics'],m)
    for actual,local in zip(r['measurement_reduced'],reduced(m)):matrix_close(actual,local)
    for a,b in zip(r['joint_probabilities'],prob):close(a,F(b))
    close(sum(r['joint_probabilities']),1);assert all(-1e-12<=x<=1+1e-12 for x in r['joint_probabilities'])
    p=[F(v) for v in prob];marg=[[p[0]+p[1],p[2]+p[3]],[p[0]+p[2],p[1]+p[3]]]
    for actual,target in zip(r['marginal_probabilities'],marg):
        for a,b in zip(actual,target):close(a,b)
    assert r['trace'][-1]['shots']==0

def execute():
    fixtures=json.loads((HERE/'fixtures.json').read_text());hand=json.loads((HERE/'hand-oracle.json').read_text());matrices={k:[[F(v) for v in row] for row in m] for k,m in hand['matrices'].items()};runs=[]
    assert {f['id'] for f in fixtures}==set(hand['cases'])
    for f in fixtures:
        outcomes={}
        for basis in ['Z','X']:
            r=q.execute(f,basis);check(r,hand['cases'][f['id']],matrices);outcomes[basis]=r
        runs.append(dict(id=f['id'],input=f,hand=hand['cases'][f['id']],bases=outcomes))
    # Verify tensor gate itself against handwritten signs, and every computational CNOT column.
    hh=q.tensor(q.H,q.H)
    for i in range(4):
        for j in range(4):close(hh[i][j],F(SIGNS[i][j],2))
    permutations=[]
    for control,expected in [(0,[0,1,3,2]),(1,[0,3,2,1])]:
        matrix=q.cnot(control)
        for col,target in enumerate(expected):
            assert [matrix[row][col] for row in range(4)]==[1 if row==target else 0 for row in range(4)]
        permutations.append(dict(control=control,column_targets=expected))
    weighted=[]
    for p in [F(0),F(1,4),F(1,2),F(3,4),F(1)]:
        f=dict(fixtures[1],weights=[float(p),float(1-p)]);pre=[[F(0)]*4 for _ in range(4)];pre[0][0]=p;pre[3][3]=1-p
        # Independent literal sign matrix quadratic sum, no tensor/gate helpers.
        x=[[sum(F(SIGNS[i][k]*SIGNS[j][l],4)*pre[k][l] for k in range(4) for l in range(4)) for j in range(4)] for i in range(4)]
        for basis,m in [('Z',pre),('X',x)]:
            r=q.execute(f,basis);matrix_close(r['measurement_density'],m);check_metrics(r['measurement_metrics'],m)
            expected=[p,0,0,1-p] if basis=='Z' else [F(1,4)]*4
            for a,b in zip(r['joint_probabilities'],expected):close(a,b)
            weighted.append(dict(weights=[str(p),str(1-p)],basis=basis,result=r,exact_probabilities=[str(v) for v in expected]))
    invalid=[];base=fixtures[0]
    cases=[('not-object',None,'Z'),('basis-order',dict(base,basis_order=['00','10','01','11']),'Z'),('control-bool',dict(base,control=True),'Z'),('control-range',dict(base,control=2),'Z'),('method',dict(base,method='unknown'),'Z'),('measurement-basis',base,'Y'),('negative-weight',dict(base,weights=[-.5,1.5]),'Z'),('bool-weight',dict(base,weights=[True,0]),'Z'),('weight-sum',dict(base,weights=[.2,.2]),'Z'),('nan-weight',dict(base,weights=[float('nan'),.5]),'Z'),('infinity-weight',dict(base,weights=[float('inf'),.5]),'Z'),('vector-length',dict(base,initial=[1,0]),'Z'),('bool-vector',dict(base,initial=[True,0,0,0]),'Z'),('nan-vector',dict(base,initial=[float('nan'),0,0,0]),'Z'),('vector-norm',dict(base,initial=[2,0,0,0]),'Z')]
    for name,f,basis in cases:
        try:q.execute(f,basis)
        except ValueError as e:invalid.append(dict(id=name,error=str(e),input_description='authored boundary; nonfinite value represented by ID, not invalid JSON numeric'))
        else:raise AssertionError(name)
    bell=runs[0]['bases'];mix=runs[1]['bases'];product=runs[5]['bases']
    for basis in ['Z','X']:
        for which in ['prepared_reduced','measurement_reduced']:
            for r in [bell[basis],mix[basis],product[basis]]:
                for local in r[which]:matrix_close(local,[[F(1,2),0],[0,F(1,2)]])
    for a,b in zip(bell['Z']['joint_probabilities'],mix['Z']['joint_probabilities']):close(a,b)
    assert max(abs(a-b) for a,b in zip(bell['X']['joint_probabilities'],mix['X']['joint_probabilities']))>.24
    return dict(version=q.VERSION,fixture_sha256=digest(HERE/'fixtures.json'),hand_sha256=digest(HERE/'hand-oracle.json'),basis_order=q.BASIS,tensor_order='first written bit=A; H_tensor_I acts on A; intended CNOT Acontrol/Btarget',runs=runs,weighted_mixture_boundaries=weighted,cnot_basis_permutations=permutations,invalid_inputs=invalid,tolerance=1e-12,shots=0,author_routing_smoke={'bell':route.route('bell'),'hardware-run':route.route('hardware-run')},scope='Classical CPU ideal two-qubit model. Exact rational expectations / floating producer. No Bell inequality, general entanglement detector, hardware or quantum advantage.')

def docs(record):
    planned={HERE/'observations/raw.json',HERE/'observations/receipt.json'}
    for f in ['README.md','skills/atlas-bell-classical-correlations/SKILL.md']:
        for link in re.findall(r'\]\(([^)]+)\)',(HERE/f).read_text()):
            if not link.startswith(('https:','#')):
                target=((HERE/f).parent/link.split('#')[0]).resolve();assert target.exists() or record and target in planned,link
    assert all(w in (HERE/'README.md').read_text() for w in ['前提','主要概念','実務判断','限界','原典','未教材'])
    c=json.loads((HERE/'coverage.json').read_text());ids={s['id'] for s in json.loads((HERE/'sources.json').read_text())};assert 2<=len(c['next_experiments'])<=4
    for row in c['areas']+c['next_experiments']:assert row['source'] in ids and row['question']
    assert all(s in (HERE/'index.html').read_text() for s in ['coverage.json','sources.json','README.md'])

def main():
    started=datetime.now(timezone.utc).isoformat();p=argparse.ArgumentParser();g=p.add_mutually_exclusive_group();g.add_argument('--record',action='store_true');g.add_argument('--seal-record',action='store_true');args=p.parse_args();raw=execute();docs(args.record);folder=HERE/'observations';qa=json.loads((folder/'ui-qa.json').read_text());sources={f:digest(HERE/f) for f in SOURCES}
    if qa['status']=='passed':
        for key,f in [('observed_ui_sha256','index.html'),('observed_sources_sha256','sources.json'),('observed_coverage_sha256','coverage.json')]:assert qa[key]==digest(HERE/f)
        rows=json.loads((folder/'ui-matrix.json').read_text())['rows'];assert len(rows)==12 and len({(r['id'],r['basis']) for r in rows})==12
        for row in rows:
            result=next(r for r in raw['runs'] if r['id']==row['id'])['bases'][row['basis']]
            for key in ['status','comparison_to_intended']:assert row[key]==result[key]
            if row['joint_probabilities'] is None:assert result['joint_probabilities'] is None
            else:
                for a,b in zip(row['joint_probabilities'],result['joint_probabilities']):close(a,b)
    if args.seal_record:
        old=json.loads((folder/'raw.json').read_text());assert {k:v for k,v in old.items() if k!='attempt'}==raw
    if args.record or args.seal_record:
        if args.record:
            assert not qa.get('observed_raw_sha256'),'seal observed raw with --seal-record'
            raw['attempt']=dict(command='python3 verify.py --record',started_at_utc=started,completed_at_utc=datetime.now(timezone.utc).isoformat(),toolchain=dict(python=platform.python_version(),os=platform.system(),machine=platform.machine()),status='passed',expected_differences=['mixture X differs despite matching Z and local I/2','wrong control / normalized branch average / local product are valid states with wrong semantics','unscaled branch average trace0.5 rejected'],shots=0)
            (folder/'raw.json').write_text(json.dumps(raw,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
        if qa.get('observed_raw_sha256'):assert qa['observed_raw_sha256']==digest(folder/'raw.json')
        names=['observations/raw.json','observations/ui-qa.json']
        for name in ['ui-matrix.json','preview-http.log','default-bind.txt','skill-smoke.json','iteration-failure.txt','resource-status.json']:
            if (folder/name).exists():names.append('observations/'+name)
        receipt=dict(executed_at_utc=datetime.now(timezone.utc).isoformat(),command='python3 verify.py --seal-record' if args.seal_record else 'python3 verify.py --record',environment=dict(python=platform.python_version(),system=platform.system(),machine=platform.machine()),inputs=dict(fixtures=raw['fixture_sha256'],hand=raw['hand_sha256']),sources=sources,artifacts={f:digest(HERE/f) for f in names},checks=dict(hand_density_probability_partial_trace='passed',principal_minors='all finite literal matrices PSD',author_smoke='passed; not independent AgentEval',actual_iab_qa=qa['status']))
        (folder/'receipt.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n')
    else:
        receipt=json.loads((folder/'receipt.json').read_text());assert receipt['sources']==sources
        for f,h in receipt['artifacts'].items():assert digest(HERE/f)==h,f
        old=json.loads((folder/'raw.json').read_text());assert {k:v for k,v in old.items() if k!='attempt'}==raw
        if qa.get('observed_raw_sha256'):assert qa['observed_raw_sha256']==digest(folder/'raw.json')
    print(json.dumps(dict(status='passed',record=args.record,seal_record=args.seal_record,cases=6,bases=2,weighted_boundaries=5,invalid_inputs=15,cnot_columns=8,shots=0,tolerance=1e-12)))
if __name__=='__main__':main()

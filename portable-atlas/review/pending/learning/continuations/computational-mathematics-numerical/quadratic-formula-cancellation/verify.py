import sys
sys.dont_write_bytecode=True
import argparse,json,hashlib,platform
from pathlib import Path
from fractions import Fraction
from decimal import Decimal,localcontext
from datetime import datetime,timezone
from fixtures import FIXTURES
from solver import solve,METHODS
from oracle import original,checked_roots,dec
from lesson import run
R=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def hashes():return {str(p.relative_to(R)):sha(p) for p in sorted(R.rglob('*')) if p.is_file() and str(p.relative_to(R)) not in ('observations/receipt.json','observations/read-only-proof.json')}
def sources():return {n:sha(R/n) for n in ('CONTRACT.md','fixtures.py','solver.py','oracle.py','lesson.py','verify.py')}
LITERAL=[[[1.,2.],[1.,2.]],[[1.00000761449337e-6,1e6],[1e-6,1e6]],
 [[0.,1e16],[1e-16,1e16]],[[0.,1e16],[1e-16,1e16]],
 [[-1e6,-1.00000761449337e-6],[-1e6,-1e-6]],[[-2.,3.],[-2.,3.]],
 [[0.,2.],[0.,2.]],[[0.,0.],[0.,0.]],
 [[1.000000005,1.000000005],[1.000000005,1.000000005]],[[1.,1.],[1.,1.]]]
def check():
    rows=[]
    for k,f in enumerate(FIXTURES):
        coeff,known=original(f)
        # Original known roots independently cross-check the high precision oracle.
        reference=checked_roots(coeff)
        with localcontext() as ctx:
            ctx.prec=90
            assert [+v for v in reference]==[+dec(v) for v in known]
        for j,m in enumerate(METHODS):
            row=run(f,m);assert row['roots']==LITERAL[k][j]
            rounded=tuple(Fraction.from_float(v) for v in row['float_coefficients'])
            for index,item in enumerate(row['metrics']):
                x=Fraction.from_float(item['computed'])
                for label,cs in [('original',coeff),('rounded',rounded)]:
                    a,b,c=cs;expected=(a*x+b)*x+c
                    assert Fraction(item['residual_'+label]['signed'])==expected
                assert (item['total_rel'] is None)==(known[index]==0)
                exact_total=abs(x-known[index])
                for field,target in [('total_abs',exact_total),('total_rel',exact_total/abs(known[index]) if known[index] else None)]:
                    if target is None: assert item[field] is None
                    elif target==0: assert Fraction(item[field])==0
                    else: assert abs(Fraction(item[field])-target)<=abs(target)*Fraction('1e-34')
            rows.append(row)
    severe=rows[4]; scaled=rows[6]
    assert severe['metrics'][0]['total_rel']=='1' and scaled['metrics'][0]['total_rel']=='1'
    assert Fraction(scaled['metrics'][0]['residual_original']['absolute'])==Fraction('1e-12')
    assert Fraction(scaled['metrics'][0]['residual_original']['term_scaled'])==1
    assert Fraction(scaled['metrics'][0]['residual_original']['coefficient_scaled'])<Fraction('1e-15')
    assert rows[-2]['metrics'][1]['arithmetic_abs']=='0' and Decimal(rows[-2]['metrics'][1]['conversion_root_abs'])>0
    cases=[('a-zero',(0,1,1),'standard'),('bool',(True,1,1),'standard'),
      ('text',('1',1,1),'product'),('nan',(1,float('nan'),1),'standard'),
      ('infinity',(1,1,float('inf')),'product'),('negative-disc',(1,0,1),'standard'),
      ('bb-overflow',(1,1e308,1),'product'),('ac4-overflow',(1e308,0,1),'standard'),
      ('root-overflow',(5e-324,1,0),'product'),('q-zero-nonzero-c',(5e-324,0,-5e-324),'product'),
      ('large-int',(10**400,0,0),'standard'),('unknown-method',(1,0,0),'other'),
      ('decimal-type',(Decimal(1),0,0),'standard')]
    guards=[]
    for name,args,method in cases:
        try:solve(*args,method)
        except ValueError as exc:guards.append(dict(case=name,rejected=True,message=str(exc)))
        else:raise AssertionError(name)
    mutants=[]
    for mutation in ('wrong_q_sign','abs_b_sign','wrong_denominator','wrong_product','drop_zero_special','zero_c_return_one'):
        witnesses=[]
        for f in FIXTURES:
            coeff,_=original(f);args=list(map(float,coeff))
            for m in METHODS:
                good=solve(*args,m)
                try:
                    bad=solve(*args,m,mutation)
                    if bad['roots']!=good['roots']:witnesses.append(dict(fixture=f['id'],method=m,observed_roots=bad['roots']))
                except ValueError as exc:witnesses.append(dict(fixture=f['id'],method=m,observed_error=str(exc)))
        assert witnesses,mutation
        mutants.append(dict(mutant=mutation,killed=True,witnesses=witnesses))
    return dict(rows=rows,guards=guards,mutants=mutants)
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--record');ap.add_argument('--seal-record',action='store_true');args=ap.parse_args()
    result=check();obs=R/'observations'
    if args.record:
        assert args.record=='attempt-01' and not (obs/'attempt-01.json').exists()
        (obs/'attempt-01.json').write_text(json.dumps(dict(utc=datetime.now(timezone.utc).isoformat(),python=platform.python_version(),float_info=dict(mant_dig=sys.float_info.mant_dig,radix=sys.float_info.radix),source_hashes=sources(),scope='finite Python float only',**result),ensure_ascii=False,indent=2)+'\n')
        (obs/'receipt.json').write_text(json.dumps(dict(ui_pending=True,source_hashes=sources()),indent=2)+'\n')
    elif args.seal_record:
        prior=json.loads((obs/'receipt.json').read_text());assert prior['ui_pending']
        (obs/'initial-receipt.json').write_text(json.dumps(prior,indent=2)+'\n')
        assert json.loads((obs/'browser.json').read_text())['observed_all_20']
        (obs/'receipt.json').write_text(json.dumps(dict(ui_pending=False,hashes=hashes()),indent=2)+'\n')
    else:
        raw=json.loads((obs/'attempt-01.json').read_text());assert {k:raw[k] for k in result}==result
        for name,digest in raw['source_hashes'].items():
            old=obs/'initial-sources'/name;assert sha(old if old.exists() else R/name)==digest
        receipt=json.loads((obs/'receipt.json').read_text());assert not receipt['ui_pending'] and receipt['hashes']==hashes()
        browser=json.loads((obs/'browser.json').read_text());assert browser['observed_all_20']
        for b in browser['rows']:
            row=next(v for v in result['rows'] if v['fixture']==b['fixture'] and v['method']==b['method'])
            assert row['roots']==b['roots'] and [v['total_rel'] for v in row['metrics']]==b['total_rel']
    print(json.dumps(dict(rows=len(result['rows']),guards=len(result['guards']),mutants=len(result['mutants']),precision=[160,240],status='passed',repository_gate='not run')))
if __name__=='__main__':main()

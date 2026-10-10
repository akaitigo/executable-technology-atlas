import sys
sys.dont_write_bytecode = True
import argparse, hashlib, json, platform
from pathlib import Path
from datetime import datetime, timezone
from copy import deepcopy
from model import run, MODES
from oracle import sequential
from fixtures import FIXTURES, CHAIN_STAGES, CHAIN_STALL

ROOT = Path(__file__).resolve().parent
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def hashes():
    return {str(p.relative_to(ROOT)):sha(p) for p in sorted(ROOT.rglob('*')) if p.is_file()
            and str(p.relative_to(ROOT)) not in ('observations/receipt.json','observations/read-only-proof.json')}
def source_hashes():
    return {n:sha(ROOT/n) for n in ('CONTRACT.md','fixtures.py','model.py','oracle.py','verify.py')}
def check():
    rows=[]
    for f in FIXTURES:
        expected=[f['expected'].get(i,0) for i in range(32)]
        assert sequential(f['program'],f['initial'])==expected
        for n,mode in enumerate(MODES):
            r=run(f['program'],f['initial'],mode)
            literal=[f['none'].get(i,0) for i in range(32)] if mode=='none' else expected
            assert r['registers']==literal
            assert r['cycles']==f['cycles'][n] and r['retired']==len(f['program'])
            assert r['stalls']==r['cycles']-(len(f['program'])+4) if f['program'] else r['stalls']==0
            if f['id']=='chain':
                assert [t['stages'] for t in r['trace']]==(CHAIN_STALL if mode=='stall' else CHAIN_STAGES)
            rows.append(dict(fixture=f['id'],oracle=expected,matches_oracle=r['registers']==expected,**r))
    p=FIXTURES[0]['program']; z=[0]*32
    cases=[('program-type',None,z,'none'),('length',p*5,z,'none'),('unknown-op',[dict(op='LOAD')],z,'none'),
        ('extra-field',[dict(p[0],extra=1)],z,'none'),('missing-field',[dict(op='ADDI',rd=1,rs1=0)],z,'none'),
        ('negative-rd',[dict(p[0],rd=-1)],z,'none'),('bool-rd',[dict(p[0],rd=True)],z,'none'),
        ('rs2-bound',[dict(p[1],rs2=32)],z,'none'),('imm-low',[dict(p[0],imm=-2049)],z,'none'),
        ('imm-high',[dict(p[0],imm=2048)],z,'none'),('imm-float',[dict(p[0],imm=1.0)],z,'none'),
        ('imm-string',[dict(p[0],imm='1')],z,'none'),('imm-nan',[dict(p[0],imm=float('nan'))],z,'none'),
        ('init-length',p,z[:-1],'none'),('x0-init',p,[1]+z[1:],'none'),
        ('register-high',p,[0,2**32]+z[2:],'none'),('register-bool',p,[0,True]+z[2:],'none'),
        ('unknown-mode',p,z,'automatic')]
    guards=[]
    for name,prog,init,mode in cases:
        try: run(prog,init,mode)
        except ValueError as exc: guards.append(dict(case=name,rejected=True,message=str(exc)))
        else: raise AssertionError(name)
    mutants=[]
    for mutation in ('write_x0','old_priority','drop_wb','unsigned_imm','no_wrap','ignore_mem_stall','read_before_wb','forward_x0'):
        differences=[]
        for f in FIXTURES:
            for mode in ('stall','forwarding'):
                good=run(f['program'],f['initial'],mode)
                bad=run(f['program'],f['initial'],mode,mutation)
                if good!=bad: differences.append(dict(fixture=f['id'],mode=mode,registers=bad['registers'],cycles=bad['cycles']))
        assert differences, mutation
        mutants.append(dict(mutant=mutation,killed=True,witnesses=differences))
    return dict(rows=rows,guards=guards,mutants=mutants)

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--record');ap.add_argument('--seal-record',action='store_true')
    args=ap.parse_args(); result=check(); obs=ROOT/'observations'
    if args.record:
        assert args.record=='attempt-01' and not (obs/'attempt-01.json').exists()
        raw=dict(utc=datetime.now(timezone.utc).isoformat(),python=platform.python_version(),scope='finite module only',source_hashes=source_hashes(),**result)
        (obs/'attempt-01.json').write_text(json.dumps(raw,ensure_ascii=False,indent=2)+'\n')
        (obs/'receipt.json').write_text(json.dumps(dict(ui_pending=True,source_hashes=source_hashes()),indent=2)+'\n')
    elif args.seal_record:
        prior=json.loads((obs/'receipt.json').read_text()); assert prior['ui_pending']
        (obs/'initial-receipt.json').write_text(json.dumps(prior,indent=2)+'\n')
        browser=json.loads((obs/'browser.json').read_text());assert browser['observed_all_27']
        (obs/'receipt.json').write_text(json.dumps(dict(ui_pending=False,hashes=hashes()),indent=2)+'\n')
    else:
        raw=json.loads((obs/'attempt-01.json').read_text());assert {k:raw[k] for k in result}==result
        for n,h in raw['source_hashes'].items():
            archive=obs/'initial-sources'/n
            assert sha(archive if archive.exists() else ROOT/n)==h
        receipt=json.loads((obs/'receipt.json').read_text());assert not receipt['ui_pending'] and receipt['hashes']==hashes()
        browser=json.loads((obs/'browser.json').read_text());assert browser['observed_all_27']
        for b in browser['rows']:
            r=next(v for v in result['rows'] if v['fixture']==b['fixture'] and v['mode']==b['mode'])
            assert b['registers']==r['registers'] and b['cycles']==r['cycles'] and b['stalls']==r['stalls']
    print(json.dumps(dict(rows=len(result['rows']),guards=len(result['guards']),mutants=len(result['mutants']),status='passed',repository_gate='not run')))

if __name__=='__main__': main()

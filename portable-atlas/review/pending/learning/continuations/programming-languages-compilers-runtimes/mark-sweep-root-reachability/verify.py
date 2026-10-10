import sys
sys.dont_write_bytecode=True
import argparse,hashlib,json,platform
from pathlib import Path
from datetime import datetime,timezone
from copy import deepcopy
from fixtures import FIXTURES,BASE,ROOTED_MARK_HAND
from collector import collect,MODES
from oracle import reachable
from lesson import run
R=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def hashes():return {str(p.relative_to(R)):sha(p) for p in sorted(R.rglob('*')) if p.is_file() and str(p.relative_to(R)) not in ('observations/receipt.json','observations/read-only-proof.json')}
def sources():return {n:sha(R/n) for n in ('CONTRACT.md','fixtures.py','collector.py','oracle.py','lesson.py','verify.py')}
def check():
    rows=[]
    for f in FIXTURES:
        baseline=deepcopy(f)
        assert reachable(f['objects'],f['roots'])==f['expected']
        for j,mode in enumerate(MODES):
            row=run(f,mode);expected=f['expected'] if j==0 else f['fault_expected']
            assert row['marked']==expected and row['survivors']==expected
            all_ids={v['id'] for v in f['objects']}
            assert row['reclaimed']==sorted(all_ids-set(expected)) and row['steps']==f['steps'][j]
            assert row['remaining_edges']==[[v['id'],d] for v in f['objects'] if v['id'] in expected for d in v['refs']]
            assert row['mark_bits_after_gc']==[] and row['dangling_edges']==[]
            assert row['premature_reclaimed']==sorted(set(f['expected'])-set(expected))
            assert row['dangling_roots']==sorted(set(f['roots'])-set(expected))
            if mode=='normal':assert row['safe'] and row['matches_oracle'] and not row['dangling_roots']
            for step in row['trace']:
                if step['phase'] in ('init','mark','mark-done'):
                    assert set(step['black']).isdisjoint(step['gray'])
                    assert set(step['marked'])==set(step['gray'])|set(step['black'])
                    assert all(d in step['marked'] for v in f['objects'] if v['id'] in step['black'] for d in v['refs'])
            if f['id']=='rooted-cycle' and mode=='normal':
                hand=[dict(queue=v['queue'],black=v['black']) for v in row['trace'] if v['event'] in ('seed root','scan')]
                assert hand==ROOTED_MARK_HAND
            rows.append(row)
        assert f==baseline
    bad=[]
    def case(name,objects=BASE,roots=['A'],mode='normal'):bad.append((name,deepcopy(objects),roots,mode))
    case('object-type',None);case('count',[dict(id='N'+str(i),refs=[]) for i in range(17)],[])
    case('duplicate-id',[dict(id='A',refs=[]),dict(id='A',refs=[])])
    case('extra-field',[dict(id='A',refs=[],extra=1)]);case('missing-field',[dict(id='A')])
    case('bool-id',[dict(id=True,refs=[])]);case('numeric-id',[dict(id=1,refs=[])])
    case('invalid-id',[dict(id='../A',refs=[])]);case('refs-type',[dict(id='A',refs='A')])
    case('refs-count',[dict(id='A',refs=['A']*17)])
    case('duplicate-edge',[dict(id='A',refs=['A','A'])]);case('dangling',[dict(id='A',refs=['B'])])
    case('edge-limit',[dict(id='N'+str(i),refs=['N'+str(j) for j in range(4)]) for i in range(16)],[])
    case('root-type',BASE,None);case('root-count',BASE,['A']*17)
    case('duplicate-root',BASE,['A','A']);case('unknown-root',BASE,['Z']);case('bool-root',BASE,[True])
    case('unknown-mode',BASE,['A'],'other')
    guards=[]
    for name,objects,roots,mode in bad:
        try:collect(objects,roots,mode)
        except ValueError as exc:guards.append(dict(case=name,rejected=True,message=str(exc)))
        else:raise AssertionError(name)
    mutants=[]
    for mutation in ('skip_refs','reverse_edges','retain_incoming','invert_sweep','clear_before_sweep','no_reset_keep'):
        witnesses=[]
        for f in FIXTURES:
            bad=collect(f['objects'],f['roots'],'normal',mutation)
            if bad['survivors']!=f['expected'] or bad['mark_bits_after_gc']:
                witnesses.append(dict(fixture=f['id'],survivors=bad['survivors'],mark_bits=bad['mark_bits_after_gc'],dangling_edges=bad['dangling_edges']))
        assert witnesses,mutation
        mutants.append(dict(mutant=mutation,killed=True,witnesses=witnesses))
    return dict(rows=rows,guards=guards,mutants=mutants)
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--record');ap.add_argument('--seal-record',action='store_true');a=ap.parse_args();result=check();obs=R/'observations'
    if a.record:
        assert a.record=='attempt-01' and not (obs/'attempt-01.json').exists()
        (obs/'attempt-01.json').write_text(json.dumps(dict(utc=datetime.now(timezone.utc).isoformat(),python=platform.python_version(),source_hashes=sources(),scope='finite synthetic graph only',**result),ensure_ascii=False,indent=2)+'\n')
        (obs/'receipt.json').write_text(json.dumps(dict(ui_pending=True,source_hashes=sources()),indent=2)+'\n')
    elif a.seal_record:
        prior=json.loads((obs/'receipt.json').read_text());assert prior['ui_pending']
        (obs/'initial-receipt.json').write_text(json.dumps(prior,indent=2)+'\n')
        assert json.loads((obs/'browser.json').read_text())['observed_all_18']
        (obs/'receipt.json').write_text(json.dumps(dict(ui_pending=False,hashes=hashes()),indent=2)+'\n')
    else:
        raw=json.loads((obs/'attempt-01.json').read_text());assert {k:raw[k] for k in result}==result
        for name,digest in raw['source_hashes'].items():
            old=obs/'initial-sources'/name;assert sha(old if old.exists() else R/name)==digest
        receipt=json.loads((obs/'receipt.json').read_text());assert not receipt['ui_pending'] and receipt['hashes']==hashes()
        browser=json.loads((obs/'browser.json').read_text());assert browser['observed_all_18']
        for b in browser['rows']:
            row=next(v for v in result['rows'] if v['fixture']==b['fixture'] and v['mode']==b['mode'])
            for field in ('marked','survivors','reclaimed','premature_reclaimed','steps'):assert row[field]==b[field]
    print(json.dumps(dict(rows=len(result['rows']),guards=len(result['guards']),mutants=len(result['mutants']),status='passed',repository_gate='not run')))
if __name__=='__main__':main()

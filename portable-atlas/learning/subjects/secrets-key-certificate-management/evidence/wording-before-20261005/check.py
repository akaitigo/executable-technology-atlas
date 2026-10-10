"""Read-only by default; --record explicitly refreshes this module's evidence."""
import sys
sys.dont_write_bytecode = True
import argparse
import hashlib
import hmac
import json
import platform
import re
from datetime import datetime, timezone
from pathlib import Path
from model import experiment, issue, verify
from oracle import expected, RFC_MAC, ISSUER
ROOT = Path(__file__).resolve().parent

def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def value_sha(value): return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
def write(path, value): path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')

def measure():
    cases = []
    for phase in ['initial', 'overlap', 'revoked']:
        for version in ['v1','v2']:
            for now in [0,100,109,110,111,1000000]:
                for fault in ['none','tamper','unknown','input']:
                    raw = experiment(phase, version, now, fault)
                    answer = expected(phase, version, now, fault)
                    assert raw['trace']['result'] == answer, raw
                    assert raw['issuer'] == ISSUER[phase]
                    cases.append({'expected': answer, 'inputSha256':value_sha(raw['input']), 'rawSha256':value_sha(raw), 'raw': raw})
    old = issue('v1'); new = issue('v2')
    sequence = [verify(old,'initial',100), verify(old,'overlap',100), verify(new,'overlap',100), verify(old,'revoked',100), verify(new,'revoked',100)]
    assert [s['result'] for s in sequence] == ['accept','accept','accept','revoked','accept']
    assert sequence[3]['macMatches'] is True
    rfc = hmac.new(bytes.fromhex('0b'*20), b'Hi There', hashlib.sha256).hexdigest()
    assert rfc == RFC_MAC
    token = issue()
    invalid = [None, [], {}, dict(token, extra=1), dict(token, version=[]), dict(token, payload=0), dict(token, payload=''), dict(token, expires=True), dict(token, expires=-1), dict(token, expires=1.0), dict(token, mac='g'*64), dict(token, mac='a'*63)]
    for bad in invalid: assert verify(bad)['result'] == 'input'
    for kwargs in [{'version':'v9'}, {'payload':''}, {'payload':'a'*81}, {'expires':True}, {'expires':-1}]:
        try: issue(**kwargs)
        except ValueError: pass
        else: raise AssertionError(kwargs)
    for kwargs in [{'phase':'bad'}, {'now':True}, {'now':-1}]:
        try: verify(token, **kwargs)
        except ValueError: pass
        else: raise AssertionError(kwargs)
    # Deliberately faulty comparison models must disagree with the fixed oracle.
    source = (ROOT/'model.py').read_text()
    mutants = []
    for name, before, after, args in [
        ('expiry-exclusive', 'now >= expires', 'now > expires', ('overlap','v1',110,'none')),
        ('revoked-key-accepted', "{'v2'})}", "{'v1', 'v2'})}", ('revoked','v1',100,'none'))
    ]:
        assert before in source
        namespace = {}
        exec(compile(source.replace(before, after), '<in-memory-intentional-fault>', 'exec'), namespace)
        faulty = namespace['experiment'](*args)['trace']['result']
        correct = expected(*args)
        assert faulty != correct, name
        mutants.append({'intentionalFault':name,'input':dict(zip(['phase','version','now','fault'], args)), 'faultyResult':faulty,'independentExpected':correct,'detected':True})
    return {'intentionalFaultComparison':mutants, 'cases': cases, 'sequence': sequence, 'rfc4231': {'locator':'https://www.rfc-editor.org/rfc/rfc4231#section-4.2', 'keyHex':'0b'*20, 'dataHex':b'Hi There'.hex(), 'expected':RFC_MAC, 'actual':rfc}, 'inputRejects':len(invalid)+8}

def docs():
    for file in ['README.md','index.html','skills/atlas-secrets-key-certificate-management/SKILL.md']:
        txt = (ROOT/file).read_text()
        links = re.findall(r'\]\(([^)]+)\)', txt) if file.endswith('.md') else re.findall(r'href="([^"]+)"',txt)
        for link in links:
            if link.startswith(('https://','http://','#')): continue
            target = (ROOT/file).parent / link.split('#')[0]
            assert target.resolve().is_relative_to(ROOT), link
            assert target.exists(), link
    for file in ['README.md','index.html']:
        txt = (ROOT/file).read_text()
        for marker in ['未教材', '実務判断', '原典', 'rfc4231', 'rfc2104', '800/57', 'rfc5280', 'rfc6960', 'rfc8446']:
            assert marker in txt, (file, marker)

def binding_files():
    return sorted(p for p in ROOT.rglob('*') if p.is_file() and p.name != 'bindings.json' and '__pycache__' not in p.parts)

p = argparse.ArgumentParser()
p.add_argument('--record', action='store_true')
a = p.parse_args()
measured = measure()
if a.record:
    write(ROOT/'evidence/run.json', {'schemaVersion':1, 'executedAt':datetime.now(timezone.utc).isoformat(), 'environment':{'python':platform.python_version(),'system':platform.system(),'release':platform.release(),'machine':platform.machine()}, 'command':'python3 -B check.py --record', 'clock':'fixed integer model clock; real execution time is executedAt', 'measurements':measured})
if a.record:
    write(ROOT/'evidence/bindings.json', {'algorithm':'sha256','files':{str(f.relative_to(ROOT)):sha(f) for f in binding_files()}, 'sourceBinding':{'HMAC construction':'RFC 2104 §2 -> model.py issue/verify','HMAC primitive oracle':'RFC 4231 §4.2 -> oracle.py RFC_MAC','MAC comparison':'Python hmac.compare_digest -> model.py verify','rotation/time':'local fixed policy, not standardized by RFC','coverage':'README/index -> NIST SP 800-57; RFC 5280/6960/8446'},'recordedAt':datetime.now(timezone.utc).isoformat()})
docs()
ui = json.loads((ROOT/'evidence/ui-qa.json').read_text())
assert ui['status'] == 'passed actual IAB HTTP QA'
assert ui['ownedServerStopped'] and ui['ownedTabClosed']
for observed in ui['rows']:
    row = dict(observed)
    digest = row.pop('observedSha256')
    assert value_sha(row) == digest, 'UI raw digest mismatch'
    if 'raw' in row:
        inp = row['raw']['input']
        assert experiment(**inp) == row['raw'], 'UI observed raw differs from model recomputation'
    else:
        assert row['case'] == 'invalid-api-now' and row['result'] == '入力拒否'
record = json.loads((ROOT/'evidence/run.json').read_text())
assert record['measurements'] == measured, 'raw evidence differs from recomputation'
bind = json.loads((ROOT/'evidence/bindings.json').read_text())
assert bind['files'] == {str(f.relative_to(ROOT)):sha(f) for f in binding_files()}, 'source/artifact digest mismatch'
print(json.dumps({'status':'passed','cases':len(measured['cases']),'sequence':5,'rfc4231':'passed','inputRejects':measured['inputRejects'],'localLinksRoadmapSourceBinding':'passed','actualIABRows':len(ui['rows']), 'digestFiles':len(bind['files']),'mode':'record' if a.record else 'read-only'},ensure_ascii=False))

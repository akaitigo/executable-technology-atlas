import sys
sys.dont_write_bytecode=True
import argparse,datetime,hashlib,json,re
from pathlib import Path
import model,oracle
from tool import command,probe,ROOT
SHA=lambda b:hashlib.sha256(b).hexdigest()
def measurements(bootstrap=False):
    results=[];assert set(model.CASES)==set(oracle.CONDITIONS)
    for name,e in oracle.CONDITIONS.items():
        d=model.experiment(name);assert d['input']['verificationEpoch']==oracle.TIMES[e['time']]
        assert d['input']['certificate']=='certs/leaf-'+e['leaf']+'.pem' and d['input']['trustAnchor']=='certs/root-'+e['ca']+'.pem'
        fields=d['raw']['fields'];assert fields['exit']==0
        out=fields['stdout'];want=oracle.FIELDS[e['leaf']]
        assert 'DNS:'+want['san'] in out and want['eku'] in out and 'CA:FALSE' in out and 'Digital Signature' in out
        assert 'notBefore=Oct  5 00:00:00 2026 GMT' in out and 'notAfter=Oct  6 00:00:00 2026 GMT' in out
        assert 'subject=CN=api.atlas.invalid' in out and 'issuer=CN=Atlas Dummy Root A' in out
        for label in ('strict','noName','chainOnly'):
            r=d['raw']['runs'][label];assert r['accepted']==e[label],(name,label,r)
            assert r['exit']==(0 if e[label] else 2)
            assert all(k in r['argv'] for k in ('-no-CAfile','-no-CApath','-no-CAstore','-attime','-CAfile','-x509_strict','-check_ss_sig'))
            assert ('-verify_hostname' in r['argv'])==(label=='strict') and ('-purpose' in r['argv'])==(label!='chainOnly')
            if e[label]:assert r['stdout'].strip().endswith(': OK') and not r['stderr']
        if e['error'] is not None:assert 'error '+str(e['error'])+' at 0 depth' in d['raw']['runs']['strict']['stderr']
        assert d['inputSha256']==model.digest(d['input']) and d['rawSha256']==model.digest(d['raw'])
        results.append({'case':name,'expected':e,'actual':d})
    roots=[]
    for root in ('a','b'):
        r=command(['x509','-in','certs/root-'+root+'.pem','-noout','-subject','-issuer','-dates','-ext','basicConstraints,keyUsage']);assert r['exit']==0
        assert 'CA:TRUE, pathlen:0' in r['stdout'] and 'Certificate Sign, CRL Sign' in r['stdout']
        assert 'notBefore=Jan  1 00:00:00 2026 GMT' in r['stdout'] and 'notAfter=Jan  1 00:00:00 2030 GMT' in r['stdout'];roots.append(r)
    before=datetime.datetime(2026,10,5,tzinfo=datetime.timezone.utc);assert int(before.timestamp())==oracle.TIMES['start'] and int((before+datetime.timedelta(days=1)).timestamp())==oracle.TIMES['end']
    assert not list(ROOT.glob('.dummykeys-*')) and not list(ROOT.rglob('*.key'))
    for p in (ROOT/'certs').glob('*.pem'):assert p.read_text().startswith('-----BEGIN CERTIFICATE-----')
    rejected=[]
    for case,mode in [('real-server','offline'),('normal','tls')]:
        try:model.experiment(case,mode)
        except ValueError as e:rejected.append({'case':case,'mode':mode,'error':str(e)})
        else:raise AssertionError('unsupported accepted')
    for file in ('README.md','index.html'):
        text=(ROOT/file).read_text();assert all(url in text for url in model.SOURCES.values());assert '未実行' in text and 'OCSP' in text
    for link in re.findall(r'\]\(([^)#]+)(?:#[^)]*)?\)',(ROOT/'README.md').read_text()):
        if link.startswith('http'):continue
        if bootstrap and link in ('evidence/run.json','evidence/bindings.json','evidence/ui-qa.json','evidence/routing-smoke.json'):continue
        assert (ROOT/link).is_file(),link
    wrong=next(r['actual'] for r in results if r['case']=='wrong-san');assert wrong['raw']['runs']['noName']['accepted'] and not wrong['raw']['runs']['strict']['accepted']
    eku=next(r['actual'] for r in results if r['case']=='wrong-eku');assert eku['raw']['runs']['chainOnly']['accepted'] and not eku['raw']['runs']['strict']['accepted']
    return {'caseCount':len(results),'verifyCount':len(results)*3,'unsupportedCount':len(rejected),'omissionCounterexamples':2,'results':results,'rootFields':roots,'unsupported':rejected,'sources':model.SOURCES}
def bindings():return {str(p.relative_to(ROOT)):SHA(p.read_bytes()) for p in sorted(ROOT.rglob('*')) if p.is_file() and '__pycache__' not in p.parts and p.name!='bindings.json'}
def main():
    p=argparse.ArgumentParser();p.add_argument('--record',action='store_true');a=p.parse_args();m=measurements(a.record)
    if a.record:
        (ROOT/'evidence/run.json').write_text(json.dumps({'recordedAt':datetime.datetime.now(datetime.timezone.utc).isoformat(),'environment':{'python':sys.version.split()[0],'platform':sys.platform,'toolProbe':probe()},'measurements':m},ensure_ascii=False,indent=2)+'\n')
        (ROOT/'evidence/bindings.json').write_text(json.dumps({'sources':model.SOURCES,'files':bindings()},indent=2)+'\n')
    else:
        assert json.loads((ROOT/'evidence/run.json').read_text())['measurements']==m
        assert json.loads((ROOT/'evidence/bindings.json').read_text())=={'sources':model.SOURCES,'files':bindings()}
        qa=json.loads((ROOT/'evidence/ui-qa.json').read_text());assert qa['serverStopped'] and qa['tabClosed'] and len(qa['cases'])==10
        for row in qa['cases']:
            if row['mode']=='tls':assert row['status']=='入力拒否: unsupported case/mode; offline fixed fixtures only' and row['rawCleared'];continue
            d=model.experiment(row['case']);assert row['inputSha256']==d['inputSha256'] and row['rawSha256']==d['rawSha256']
            assert row['accepted']=={k:v['accepted'] for k,v in d['raw']['runs'].items()}
        assert json.loads((ROOT/'evidence/routing-smoke.json').read_text())['forwardAgentEval']=='not-run'
    print(json.dumps({k:v for k,v in m.items() if k not in ('results','rootFields','unsupported')},ensure_ascii=False))
if __name__=='__main__':main()

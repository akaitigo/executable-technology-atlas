"""Read-only unless --record explicitly requests evidence refresh."""
import sys
sys.dont_write_bytecode=True
import argparse,copy,hashlib,json,platform,re
from datetime import datetime,timezone
from pathlib import Path
from model import CASES,GENESIS,experiment,validate,seal,new_ledger,validated_append,digest
from oracle import HAND,traverse,ABC_SHA256
ROOT=Path(__file__).resolve().parent

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
def measure():
    rows=[]
    for case in CASES:
        for amount in range(1,101):
            x=experiment(case,amount);answer=traverse(x['ledger']);full=x['fullValidation']
            assert {'result':full['result'],'balances':full['balances']}==answer,(case,amount)
            if amount==10:assert (full['result'],full['balances'])==HAND[case]
            if full['result']=='accept':assert sum(full['balances'].values())==150 and min(full['balances'].values())>=0
            rows.append({'input':x['input'],'inputSha256':digest(x['input']),'raw':x,'rawSha256':digest(x),'independentOracle':answer})
    first=new_ledger();before=copy.deepcopy(first)
    accepted=validated_append(first,{'id':'t1','sender':'mock-a','receiver':'mock-b','amount':10})
    assert first==before and accepted[:-1]==first
    second=validated_append(accepted,{'id':'t2','sender':'mock-b','receiver':'mock-a','amount':5})
    assert second[:-1]==accepted and validate(second)['balances']=={'mock-a':95,'mock-b':55} and traverse(second)['balances']=={'mock-a':95,'mock-b':55}
    # Returned prefixes are copied, so modifying a disposable candidate cannot modify prior ledger.
    discarded=validated_append(accepted,{'id':'probe','sender':'mock-b','receiver':'mock-a','amount':1});discarded[0]['balances']['mock-a']=0;assert accepted[0]['balances']['mock-a']==100 and first==before
    rejects=0
    for tx in [{'id':'t1','sender':'mock-a','receiver':'mock-b','amount':10},{'id':'t3','sender':'mock-a','receiver':'mock-b','amount':101}]:
        try:validated_append(accepted,tx)
        except ValueError:rejects+=1
        else:raise AssertionError('invalid append accepted')
    for kwargs in [{'case':'live-chain'},{'amount':True},{'amount':0},{'amount':101},{'amount':1.5}]:
        try:experiment(**kwargs)
        except ValueError:rejects+=1
        else:raise AssertionError(kwargs)
    for ledger in [None,{},[],[seal(GENESIS)]*101]:
        assert validate(ledger)['result']=='input';rejects+=1
    good=experiment()['ledger']
    invalid_tx=[None,{},dict(good[1]['tx'],amount=True),dict(good[1]['tx'],amount=1.5),dict(good[1]['tx'],id=[]),dict(good[1]['tx'],sender=[]),dict(good[1]['tx'],extra=0)]
    for tx in invalid_tx:
        b=copy.deepcopy(good);body={k:v for k,v in b[1].items() if k!='hash'};body['tx']=tx;b[1]=seal(body)
        assert validate(b)['result']=='input' and traverse(b)['result']=='input';rejects+=1
    for claims in [None,{'mock-a':90},{'mock-a':True,'mock-b':60},{'mock-a':90.0,'mock-b':60}]:
        b=copy.deepcopy(good);body={k:v for k,v in b[1].items() if k!='hash'};body['balances']=claims;b[1]=seal(body)
        assert validate(b)['result']=='input' and traverse(b)['result']=='input';rejects+=1
    changed=copy.deepcopy(GENESIS);changed['balances']['mock-a']=100.0
    assert validate([seal(changed)])['result']=='genesis-mismatch' and traverse([seal(changed)])['result']=='genesis-mismatch';rejects+=1
    b=copy.deepcopy(good);b[1]['height']=True;assert validate(b)['result']=='input' and traverse(b)['result']=='input';rejects+=1
    source=(ROOT/'model.py').read_text();faults=[]
    for name,before,after,case in [('balance-check-missing','elif claims!=expected:','elif False and claims!=expected:','forged-balance'),('zero-accepted',"tx['amount']<=0", "tx['amount']<0",'zero'),('replay-not-checked',"elif tx['id'] in seen:","elif False and tx['id'] in seen:",'replay')]:
        assert before in source;ns={};exec(compile(source.replace(before,after),'<in-memory-intentional-fault>','exec'),ns)
        candidate=experiment(case)['ledger'];faulty=ns['validate'](candidate)['result'];answer=traverse(candidate)['result'];assert faulty!=answer
        faults.append({'fault':name,'case':case,'faultyResult':faulty,'independentExpected':answer,'detected':True})
    kat=hashlib.sha256(b'abc').hexdigest();assert kat==ABC_SHA256
    return {'cases':rows,'acceptedLedger':second,'appendPrefixPreserved':True,'inputRejects':rejects,'intentionalFaults':faults,'sha256KAT':{'inputHex':'616263','expected':ABC_SHA256,'actual':kat,'locator':'https://csrc.nist.gov/CSRC/media/Projects/Cryptographic-Standards-and-Guidelines/documents/examples/SHA256.pdf'}}

def docs():
    for file in ['README.md','index.html','skills/atlas-decentralized-systems-blockchain/SKILL.md']:
        txt=(ROOT/file).read_text();links=re.findall(r'\]\(([^)]+)\)',txt) if file.endswith('.md') else re.findall(r'href="([^"]+)"',txt)
        for link in links:
            if link.startswith(('http://','https://','#')):continue
            target=((ROOT/file).parent/link.split('#')[0]).resolve();assert target.is_relative_to(ROOT) and target.exists(),link
    for file in ['README.md','index.html']:
        txt=(ROOT/file).read_text()
        for marker in ['未教材','実務判断','原典','8202','180-4','rfc8785','consensus','総量','署名']:assert marker in txt,(file,marker)
    from html.parser import HTMLParser
    class Fields(HTMLParser):
        def __init__(self):super().__init__();self.ids=[];self.in_title=False;self.title=''
        def handle_starttag(self,t,a):
            if t=='title':self.in_title=True
            self.ids.extend(v for k,v in a if k=='id')
        def handle_endtag(self,t):
            if t=='title':self.in_title=False
        def handle_data(self,d):
            if self.in_title:self.title+=d
    f=Fields();f.feed((ROOT/'index.html').read_text());assert f.title=='架空ledger・hash chain実験室';assert len(f.ids)==len(set(f.ids));assert all(x in f.ids for x in ['prediction','case','amount','run','blocks','naive','full','raw'])
def files():return sorted(p for p in ROOT.rglob('*') if p.is_file() and p.name!='bindings.json' and '__pycache__' not in p.parts)
p=argparse.ArgumentParser();p.add_argument('--record',action='store_true');a=p.parse_args();measured=measure()
if a.record:
    write(ROOT/'evidence/run.json',{'schemaVersion':1,'executedAt':datetime.now(timezone.utc).isoformat(),'environment':{'python':platform.python_version(),'system':platform.system(),'release':platform.release(),'machine':platform.machine()},'command':'python3 -B check.py --record','input':'fixed synthetic cases; no live account or chain','measurements':measured})
    write(ROOT/'evidence/accepted-ledger.json',measured['acceptedLedger'])
    write(ROOT/'evidence/bindings.json',{'algorithm':'sha256','files':{str(f.relative_to(ROOT)):sha(f) for f in files()},'recordedAt':datetime.now(timezone.utc).isoformat(),'sourceBinding':{'ledger':'NIST IR 8202 -> chain/link vs transactions/consensus distinction and coverage','hash':'FIPS 180-4 -> model SHA256; NIST SHA256 example abc -> oracle.ABC_SHA256','canonicalization':'RFC 8785 -> unimplemented general JCS; current serializer has limited model scope','oracle':'oracle.py independent debit/credit traversal + HAND; shared hashlib, not independent crypto implementation','rule':'local synthetic positive integer / known accounts / fixed genesis / exact balances / unique id'}})
docs();assert json.loads((ROOT/'evidence/run.json').read_text())['measurements']==measured;assert json.loads((ROOT/'evidence/accepted-ledger.json').read_text())==measured['acceptedLedger']
assert json.loads((ROOT/'evidence/bindings.json').read_text())['files']=={str(f.relative_to(ROOT)):sha(f) for f in files()},'source/artifact digest mismatch'
ui=json.loads((ROOT/'evidence/ui-qa.json').read_text())
if ui['status']=='passed actual IAB HTTP QA':
    assert ui['ownedServerStopped'] and ui['ownedTabClosed']
    for observed in ui['rows']:
        row=dict(observed);got=row.pop('observedSha256');assert digest(row)==got
        if 'rawProjection' in row:
            obs=row['rawProjection'];x=experiment(**obs['input']);full=x['fullValidation'];answer=traverse(x['ledger'])
            actual={'input':x['input'],'ledgerSha256':x['ledgerSha256'],'naive':x['naiveChainOnly']['result'],'full':full['result'],'balances':full['balances'],'oracle':answer,'decisionResults':[d['result'] for d in full['decisions']],'hashMatches':[t['hashMatches'] for t in full['chain']['trace']],'linkMatches':[t['linkMatches'] for t in full['chain']['trace']]}
            assert obs==actual,'UI projection mismatch'
        else:
            assert row['result']=='入力拒否'
            try:experiment(**row['input'])
            except ValueError:pass
            else:raise AssertionError('invalid API no longer rejected')
print(json.dumps({'status':'passed' if ui['status']=='passed actual IAB HTTP QA' else 'core-passed-ui-pending','comparisons':len(measured['cases']),'handCases':len(HAND),'inputRejects':measured['inputRejects'],'intentionalFaults':len(measured['intentionalFaults']),'appendPrefix':'preserved','sha256KAT':'passed','roadmapLocalLinksSourceBinding':'passed','digestFiles':len(files()),'actualIABRows':len(ui.get('rows',[])),'mode':'record' if a.record else 'read-only'},ensure_ascii=False))

import sys
sys.dont_write_bytecode=True
import argparse,copy,datetime,hashlib,json,platform,re
from html.parser import HTMLParser
import model,oracle
R=model.ROOT
p=argparse.ArgumentParser();p.add_argument('--record',action='store_true');a=p.parse_args()
def canonical(x):return json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(',',':'))
def sha(x):return hashlib.sha256(x if isinstance(x,bytes) else x.encode()).hexdigest()
rules=json.loads((R/'rules.json').read_text());model.validate_rules(rules);assert model.SOURCES==oracle.LOCATORS
rows=[];bypasses=0
addresses=['10.0.0.'+str(x) for x in range(256)]+['0.0.0.0','255.255.255.255','9.255.255.255','10.0.1.0','10.0.1.255','10.1.0.0','192.0.2.1','127.0.0.1']
ports=[0,1,21,22,23,52,53,54,442,443,444,65534,65535]
def compare(row):
    p=row['input']['packet'];expect=oracle.expected(p,row['input']['order'])
    assert (row['first']['decision'],row['naive']['decision'],row['bypass'])==(expect['first'],expect['naive'],expect['bypass'])
    for name in ('first','naive'):
        result=row[name];trace=result['trace'];assert result['traceSha256']==sha(canonical(trace))
        assert [s['index'] for s in trace]==list(range(len(trace)))
        terminal=[s for s in trace if s['terminal']]
        assert len(terminal)<=1 and (not terminal or terminal[0] is trace[-1])
        if result['winner']=='default-deny':assert result['decision']=='deny' and len(trace)==4
        else:assert trace[-1]['terminal'] and trace[-1]['ruleId']==result['winner']
    row['oracle']=expect;row['inputSha256']=sha(canonical(row['input']));row['rawSha256']=sha(canonical({'first':row['first'],'naive':row['naive']}));return row
for address in addresses:
    for protocol in ('tcp','udp'):
        for port in ports:
            for order in ('deny-first','allow-first'):
                row=compare(model.experiment(address,protocol,port,order));bypasses+=row['bypass'];rows.append(row)
# Full port space against separately fixed policy, not a second rule matcher.
full_port=[]
for source in ('10.0.0.1','10.0.0.130'):
    for protocol in ('tcp','udp'):
        results=[]
        for port in range(65536):
            p=model.packet(source,protocol,port);e=oracle.expected(p,'deny-first');f=model.evaluate(p,rules,'first-match');n=model.evaluate(p,rules,'naive-any-allow');assert (f['decision'],n['decision'])==(e['first'],e['naive']);results.append([port,f['decision'],n['decision']])
        full_port.append({'source':source,'protocol':protocol,'count':len(results),'allowedFirst':[r[0] for r in results if r[1]=='allow'],'allowedNaive':[r[0] for r in results if r[2]=='allow'],'rawSha256':sha(canonical(results)),'rawDecisionRows':results})
hand=[]
for source,protocol,port,order,f,n in oracle.HAND:
    row=compare(model.experiment(source,protocol,port,order));assert (row['first']['decision'],row['naive']['decision'])==(f,n);hand.append(row)
rejects=[]
for source,protocol,port,order in [('256.0.0.1','tcp',443,'deny-first'),('10.0.0','tcp',443,'deny-first'),('010.0.0.1','tcp',443,'deny-first'),('','tcp',443,'deny-first'),('localhost','tcp',443,'deny-first'),('::1','tcp',443,'deny-first'),('10.0.0.1/24','tcp',443,'deny-first'),('10.0.0.1','icmp',443,'deny-first'),('10.0.0.1','TCP',443,'deny-first'),('10.0.0.1','tcp',-1,'deny-first'),('10.0.0.1','tcp',65536,'deny-first'),('10.0.0.1','tcp',True,'deny-first'),('10.0.0.1','tcp',443.0,'deny-first'),('10.0.0.1','tcp','443','deny-first'),('10.0.0.1','tcp',443,'random')]:
    try:model.experiment(source,protocol,port,order)
    except ValueError as e:rejects.append({'input':[source,protocol,port,order],'error':str(e)})
    else:raise AssertionError('unexpected input acceptance')
for label,change in [('noncanonical CIDR',lambda r:r[0].update(source='10.0.0.129/25')),('IPv6 rule',lambda r:r[0].update(source='::/0')),('reversed ports',lambda r:r[0].update(ports=[443,22])),('bool ports',lambda r:r[0].update(ports=[False,443])),('duplicate id',lambda r:r[1].update(id=r[0]['id'])),('unsupported action',lambda r:r[0].update(action='jump')),('extra key',lambda r:r[0].update(extra=1))]:
    changed=copy.deepcopy(rules);change(changed)
    try:model.validate_rules(changed)
    except ValueError as e:rejects.append({'input':label,'error':str(e)})
    else:raise AssertionError(label)
# Actual fault experiments: deny ignored, rule order wrong, quarantined prefix shrunk.
faults=[]
for label,changed,mode in [('ignore deny',rules,'naive-any-allow'),('broad allow first',[rules[1],rules[0],*rules[2:]],'first-match'),('wrong prefix',[dict(rules[0],source='10.0.0.192/26'),*rules[1:]],'first-match')]:
    p=model.packet('10.0.0.130','tcp',443);actual=model.evaluate(p,changed,mode);expected=oracle.expected(p,'deny-first')['first'];assert actual['decision']!=expected;faults.append({'fault':label,'rules':changed,'packet':p,'raw':actual,'policyExpected':expected,'detected':True})
class Page(HTMLParser):
    def __init__(self):super().__init__();self.ids=[];self.links=[]
    def handle_starttag(self,t,attrs):
        d=dict(attrs)
        if 'id'in d:self.ids.append(d['id'])
        if t=='a' and 'href'in d:self.links.append(d['href'])
page=Page();page.feed((R/'index.html').read_text());assert len(page.ids)==len(set(page.ids))
for i in ['prediction','source','protocol','port','order','run','first-flow','naive-flow','raw','answer','roadmap']:assert i in page.ids
readme=(R/'README.md').read_text();html=(R/'index.html').read_text()
for url in oracle.LOCATORS.values():assert url in readme and url in html
for marker in ['conntrack','IPv6','identity','platform','TLS','LSM']:assert marker.lower() in (readme+html).lower()
for link in re.findall(r'\]\(([^)]+)\)',readme)+page.links:
    if link.startswith(('https://','#')):continue
    if a.record and link.startswith('evidence/') and not (R/link).exists():continue
    target=(R/link.split('#')[0]).resolve();assert target.is_relative_to(R) and target.exists(),link
ui=None
if (R/'evidence/ui-qa.json').exists():
    ui=json.loads((R/'evidence/ui-qa.json').read_text());assert ui['status']=='passed'
    assert len(ui['rows'])==14
    for observed in ui['rows']:
        source,protocol,port,order=observed['input']
        if observed['status']=='input-rejected':
            assert observed['staleTraceCleared'] is True
            try:model.experiment(source,protocol,port,order)
            except ValueError:pass
            else:raise AssertionError('UI rejection mismatch')
        else:
            row=compare(model.experiment(source,protocol,port,order));projection={'first':row['first']['decision'],'naive':row['naive']['decision'],'bypass':row['bypass'],'winnerFirst':row['first']['winner'],'winnerNaive':row['naive']['winner'],'traceFirst':row['first']['traceSha256'],'traceNaive':row['naive']['traceSha256'],'oracle':row['oracle']};assert observed['projection']==projection
            assert observed['projectionSha256']==sha(canonical(projection))
run={'schema':1,'executedAt':datetime.datetime.now(datetime.timezone.utc).isoformat(),'environment':{'python':platform.python_version(),'system':platform.system(),'release':platform.release(),'machine':platform.machine()},'command':'python3 -B check.py --record','measurements':{'grid':rows,'bypassCount':bypasses,'fullPortSpace':full_port,'hand':hand,'inputRejects':rejects,'faults':faults},'sourceBinding':oracle.LOCATORS,'rulesSourceSha256':sha((R/'rules.json').read_bytes())}
if a.record:(R/'evidence/run.json').write_text(json.dumps(run,ensure_ascii=False,separators=(',',':'))+'\n')
else:
    saved=json.loads((R/'evidence/run.json').read_text());assert saved['measurements']==run['measurements'] and saved['sourceBinding']==run['sourceBinding'] and saved['rulesSourceSha256']==run['rulesSourceSha256']
files={str(f.relative_to(R)):sha(f.read_bytes()) for f in sorted(R.rglob('*')) if f.is_file() and '__pycache__' not in f.parts and f!=R/'evidence/bindings.json'}
if a.record:(R/'evidence/bindings.json').write_text(json.dumps({'schema':1,'sha256':files,'sourceBinding':oracle.LOCATORS},ensure_ascii=False,indent=2)+'\n')
else:assert json.loads((R/'evidence/bindings.json').read_text())['sha256']==files
print(json.dumps({'status':'passed' if ui else 'core-passed-ui-pending','gridComparisons':len(rows),'fullPortComparisons':sum(x['count'] for x in full_port),'handCases':len(hand),'bypassCount':bypasses,'inputRejects':len(rejects),'intentionalFaults':len(faults),'roadmapLocalLinksSourceBinding':'passed','digestFiles':len(files),'actualIABRows':len(ui['rows']) if ui else 0,'mode':'record' if a.record else 'read-only'}))

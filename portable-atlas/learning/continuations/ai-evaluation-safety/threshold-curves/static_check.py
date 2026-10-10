#!/usr/bin/env python3
"""Atlas: saved documents and data bindings, no browser or producer execution."""
import ast,hashlib,json,re
from pathlib import Path
from urllib.parse import unquote
ROOT=Path(__file__).resolve().parent
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def main():
    checks=[];links=[]
    def ck(name,ok):
        if not ok:raise ValueError(name)
        checks.append(name)
    fixed=json.loads((ROOT/'records/pre-execution-inputs.json').read_text())
    for n,h in fixed['sha256'].items():ck('fixed producer input '+n,sha(ROOT/n)==h)
    for n in ['threshold_sweep.py','producer.py','run.py','verify.py','resources.py','resource_parse.py','priority_launcher.py','static_check.py']:
        ast.parse((ROOT/n).read_text());ck('syntax '+n,True)
    data=(ROOT/'data.js').read_text();embedded=json.loads(data.split('window.ATLAS_DATA_TEXT = ',1)[1].removesuffix(';\n'));bundle=json.loads(embedded)
    ck('embedded digest pin',hashlib.sha256(embedded.encode()).hexdigest() in (ROOT/'lesson.js').read_text())
    ck('expected exact text bytes',bundle['expected_text'].encode()==(ROOT/'expected.json').read_bytes())
    status=json.loads((ROOT/'status.json').read_text())
    ck('GUI held without full acceptance',status['browser_start_hold'] and status['actual_dom_states']==status['captures']==0 and status['independent_acceptance'] is False)
    ck('no source integration or credit',status['integrated'] is False and status['author_credit']==0)
    if status['observation'] is None:
        ck('pending has no synthetic result',bundle['run_text'] is None and status['target_count']==0)
        report=json.loads((ROOT/'records/pending-reader/stdout.json').read_text())
        ck('pending model read',report['passed'] and report['mode']=='pending-only' and report['modeled_states']==[])
    else:
        runfile=ROOT/status['observation'];ck('actual run bytes',runfile.read_bytes()==bundle['run_text'].encode() and sha(runfile)==bundle['run_sha256']==status['observation_sha256'])
        run=json.loads(bundle['run_text']);ck('completed target exactly once',run['collection_complete'] and run['target_count']==status['target_count']==1 and run['target_retry']==0)
        report=json.loads((ROOT/'records/reader-model.stdout.json').read_text())
        ck('24 modeled states only',report['passed'] and report['mode']=='saved-results' and len(report['modeled_states'])==24 and report['actual_dom_states']==report['browser_starts']==report['captures']==0)
        for n,h in report['source_sha256'].items():ck('tested model source '+n,sha(ROOT/n)==h)
    for name in ['CONTRACT.md','README.md','COVERAGE.md','SOURCES.md','HAND_TRACE.md','SKILL.md','index.html','HANDOFF.md']:
        text=(ROOT/name).read_text();ck('Atlas name '+name,'Atlas' in text);ck('reader wording '+name,'原票' not in text)
        refs=re.findall(r'\]\(([^)]+)\)',text) if name.endswith('.md') else re.findall(r'(?:href|src)="([^"]+)"',text)
        for ref in refs:
            if ref.startswith(('https://','http://','#')):continue
            target=unquote(ref.split('#',1)[0]);ck(name+' link '+target,(ROOT/target).exists());links.append({'from':name,'target':target})
    print(json.dumps({'project':'Atlas','passed':True,'mode':status['state'],'check_count':len(checks),'checks':checks,'local_references':links,'new_producer_execution':0,'browser_starts':0},ensure_ascii=False,indent=2))
if __name__=='__main__':main()

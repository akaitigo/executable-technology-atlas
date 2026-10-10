#!/usr/bin/env python3
"""Atlas: check saved documents, embedded bytes and source bindings without browser/producer."""
import ast,hashlib,json,re
from pathlib import Path
from urllib.parse import unquote
ROOT=Path(__file__).resolve().parent
checks=[]
def ck(name,value):
    if not value:raise ValueError(name)
    checks.append(name)
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def main():
    fixed=json.loads((ROOT/'records/pre-execution-inputs.json').read_text())
    for name,wanted in fixed['sha256'].items():ck('fixed input '+name,sha(ROOT/name)==wanted)
    for name in ['compiler_vm.py','producer.py','run.py','verify.py','resources.py','resource_parse.py','priority_launcher.py','static_check.py']:
        ast.parse((ROOT/name).read_text());ck('Python syntax '+name,True)
    data=(ROOT/'data.js').read_text();embedded=json.loads(data.split('window.ATLAS_DATA_TEXT = ',1)[1].removesuffix(';\n'));bundle=json.loads(embedded)
    ck('outer digest pin',hashlib.sha256(embedded.encode()).hexdigest() in (ROOT/'lesson.js').read_text())
    for kind in ['run','expected']:
        b=(ROOT/bundle[kind+'_path']).read_bytes()
        ck(kind+' exact embedded bytes',b==bundle[kind+'_text'].encode())
        ck(kind+' exact original digest',hashlib.sha256(b).hexdigest()==bundle[kind+'_sha256'])
    run=json.loads(bundle['run_text']);ck('one completed producer',run['collection_complete'] and run['target_count']==1 and run['target_retry']==0)
    model=json.loads((ROOT/'records/reader-model.stdout.json').read_text())
    ck('model result only',model['passed'] and model['check_count']==178 and model['actual_dom_states']==model['browser_starts']==model['captures']==model['producer_runs']==0)
    for name,digest in model['source_sha256'].items():ck('tested model source '+name,sha(ROOT/name)==digest)
    ck('all trace rows modeled',len(model['modeled_states'])==33)
    for case in ['final-empty','final-extra']:
        ck(case+' finish rendered',any(r['case']==case and r['raw']['step']['phase']=='finish' and '終端検査' in r['diagram_text'] for r in model['modeled_states']))
    files=['CONTRACT.md','README.md','COVERAGE.md','SOURCES.md','HAND_TRACE.md','SKILL.md','index.html']
    links=[]
    for name in files:
        text=(ROOT/name).read_text();ck('Atlas name '+name,'Atlas' in text);ck('reader wording '+name,'原票' not in text)
        refs=re.findall(r'\]\(([^)]+)\)',text) if name.endswith('.md') else re.findall(r'(?:href|src)="([^"]+)"',text)
        for ref in refs:
            if ref.startswith(('https://','http://','#')):continue
            target=unquote(ref.split('#',1)[0]);ck(name+' link '+target,(ROOT/target).exists());links.append({'from':name,'target':target})
    status=json.loads((ROOT/'status.json').read_text())
    ck('GUI held and not accepted',status['browser_start_hold'] and status['actual_dom_states']==status['captures']==0 and status['independent_acceptance'] is False)
    ck('read status input binding',status['observation_sha256']==sha(ROOT/status['observation']))
    ck('no new global credit',status['author_credit']==0 and status['integrated'] is False)
    print(json.dumps({'project':'Atlas','passed':True,'check_count':len(checks),'checks':checks,'local_references':links,'browser_starts':0,'producer_runs':0},ensure_ascii=False,indent=2))
if __name__=='__main__':main()

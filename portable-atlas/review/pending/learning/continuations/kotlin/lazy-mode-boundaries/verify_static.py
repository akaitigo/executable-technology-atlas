#!/usr/bin/env python3
"""Atlas: inspect fixed inputs, references and pending state without compiler, browser or server."""
import ast,hashlib,importlib.util,json,re
from pathlib import Path
ROOT=Path(__file__).resolve().parent
checks=[]
def ck(label,condition):
    checks.append({'label':label,'passed':bool(condition)})
    if not condition:raise AssertionError(label)
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
try:
    pre=json.loads((ROOT/'records/pre-implementation.json').read_text())
    for name,sha in [('CONTRACT.md','5bc040658c38ecdb1e5a8df4df1787f7fa416eef261917eaabc1ca6bb4febd90'),('expected.json','502baddf94f2de968e396a06a5db8066ce399a95f5e27af811640e7b06d9af13')]:ck('unchanged fixed '+name,digest(ROOT/name)==sha)
    for f in ROOT.glob('*.py'):ast.parse(f.read_text());ck('Python syntax '+f.name,True)
    for row in json.loads((ROOT/'sources.json').read_text())['rows']:
        data=(ROOT/row['local_path']).read_bytes();ck('fixed source '+row['id'],hashlib.sha256(data).hexdigest()==row['file_sha256'])
        selected=b''.join(data.splitlines(keepends=True)[row['line_start']-1:row['line_end']]);ck('fixed lines '+row['id'],hashlib.sha256(selected).hexdigest()==row['range_sha256'])
    manifest=json.loads((ROOT/'reader-data.json').read_text());status=json.loads((ROOT/'status.json').read_text())
    if manifest['state']=='not-executed':
        ck('pending state has no observation',manifest['observation'] is None)
        ck('native not claimed',status['compile_count']==status['jvm_count']==0)
        keys=['expected','decision']
    else:
        ck('measured state',manifest['state']=='measured' and status['compile_count']==status['jvm_count']==1)
        keys=['observation','expected','verification']
    for k in keys:ck('manifest '+k,digest(ROOT/manifest[k]['path'])==manifest[k]['sha256'])
    js=(ROOT/'lesson.js').read_text();ck('manifest bytes pinned',re.search(r'MANIFEST_SHA="([a-f0-9]+)"',js).group(1)==digest(ROOT/'reader-data.json'))
    spec=importlib.util.spec_from_file_location('preview',ROOT/'preview.py');module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    refs=module.REFERENCES;aliases={e['http_alias']:slug for slug,e in refs.items() if e.get('http_alias')}
    for slug,e in refs.items():
        ck('reference bytes '+slug,digest(Path(e['path']))==e['sha256']);body=module.reference_html(slug);ck('reference rendering without server '+slug,len(body)>100 and b'Atlas' in body)
    files=list(ROOT.glob('*.md'))+list((ROOT/'skills').rglob('*.md'))+list(ROOT.glob('*.html'))
    for f in files:
        content=f.read_text();ck('Atlas in text '+str(f.relative_to(ROOT)),'Atlas' in content or 'ATLAS' in content)
        ck('reader wording '+str(f.relative_to(ROOT)),'原票' not in content)
        links=re.findall(r'\]\(([^)]+)\)',content) if f.suffix=='.md' else re.findall(r'(?:href|src)="([^"]+)"',content)
        for target in links:
            if target.startswith(('http:','https:','#')):continue
            target=target.split('#')[0];resolved=(f.parent/target).resolve()
            if target.startswith('reference/'):exists=target[10:] in refs
            else:exists=resolved.is_file()
            ck('local reference '+str(f.relative_to(ROOT))+' -> '+target,exists)
    print(json.dumps({'project':'Atlas','passed':True,'check_count':len(checks),'checks':checks,'compiler':0,'jvm':0,'browser':0,'server':0},ensure_ascii=False,indent=2))
except Exception as e:
    print(json.dumps({'project':'Atlas','passed':False,'checks':checks,'error':repr(e)},ensure_ascii=False,indent=2));raise

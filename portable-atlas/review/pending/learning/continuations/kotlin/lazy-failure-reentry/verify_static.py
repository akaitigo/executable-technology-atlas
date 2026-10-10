#!/usr/bin/env python3
"""Atlas: light saved-file checks, not runtime or browser acceptance."""
import ast,hashlib,json,re,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parent
checks=[]
def ck(label,condition):
    checks.append({'label':label,'passed':bool(condition)})
    if not condition: raise ValueError(label)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
for p in sorted(ROOT.glob('*.py')):
    ast.parse(p.read_text());ck('Python syntax '+p.name,True)
r=subprocess.run(['node','--check',str(ROOT/'lesson.js')],capture_output=True,text=True,timeout=5)
ck('JavaScript syntax',r.returncode==0)
manifest=json.loads((ROOT/'reader-data.json').read_text())
ck('manifest pin',sha(ROOT/'reader-data.json') in (ROOT/'lesson.js').read_text())
ck('expected pin',sha(ROOT/manifest['expected']['path'])==manifest['expected']['sha256'])
fixed=json.loads((ROOT/'records/contract-before-implementation.json').read_text())
for name,value in fixed['files'].items():ck('pre-implementation fixed '+name,sha(ROOT/name)==value)
for name,value in json.loads((ROOT/'sources/provenance.json').read_text())['files'].items():ck('fixed source '+name,sha(ROOT/'sources'/name)==value)
refs=json.loads((ROOT/'reference-map.json').read_text())['entries']
for e in refs:ck('read-only reference '+e['slug'],sha(Path(e['path']))==e['sha256'])
for name in ['index.html','README.md','COVERAGE.md','CONTRACT.md','SOURCES.md','HAND_TRACE.md','references.html','GUI_VERIFICATION.md','HANDOFF.md','skills/atlas-lazy-failure/SKILL.md']:
    s=(ROOT/name).read_text();ck('Atlas named '+name,'Atlas' in s or 'ATLAS' in s);ck('natural record wording '+name,'\u539f\u7968' not in s)
    links=re.findall(r'href="([^"]+)"',s) if name.endswith('.html') else re.findall(r'\]\(([^)]+)\)',s)
    for url in links:
        if url.startswith(('http:','https:','#')):continue
        if url.startswith('reference/'):ck(name+' reference route '+url,any(e['slug']==url.split('/')[1] for e in refs))
        else:ck(name+' file link '+url,(ROOT/name).parent.joinpath(url.split('#')[0]).exists())
status=json.loads((ROOT/'status.json').read_text())
if manifest['observation'] is None:
    ck('unmeasured state',status['compile_count']==status['jvm_count']==0 and not status['runtime_accepted'])
    ck('pending screen label','測定前・結果なし' in (ROOT/'index.html').read_text())
    ck('Skill pending branch','observationがnull' in (ROOT/'skills/atlas-lazy-failure/SKILL.md').read_text())
else:ck('saved observation pin',sha(ROOT/manifest['observation']['path'])==manifest['observation']['sha256'])
print(json.dumps({'project':'Atlas','passed':True,'checks':checks,'check_count':len(checks),'native_execution':0,'browser_execution':0,'node_stdout':r.stdout,'node_stderr':r.stderr},ensure_ascii=False,indent=2))

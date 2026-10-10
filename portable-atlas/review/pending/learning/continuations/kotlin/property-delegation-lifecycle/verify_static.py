"""Atlas: local links, copied source excerpts, bundle binding; no browser/native."""
import hashlib,json,re
from pathlib import Path
from html.parser import HTMLParser
from urllib.parse import urlsplit,unquote
ROOT=Path(__file__).resolve().parent
checks=[]
def check(v,n):
    if not v:raise AssertionError(n)
    checks.append(n)
class Links(HTMLParser):
    def handle_starttag(self,tag,attrs):
        for k,v in attrs:
            if k in ['href','src'] and v:
                u=urlsplit(v)
                if not u.scheme and u.path:check((ROOT/unquote(u.path)).is_file(),'relative HTML '+v)
for n in ['index.html','reference.html']:Links().feed((ROOT/n).read_text())
for n in ['README.md','SKILL.md','COVERAGE.md','SOURCES.md','RUN_CONDITIONS.md']:
    s=(ROOT/n).read_text();check('Atlas' in s,'project '+n);check('原票' not in s,'reader wording '+n)
    for dest in re.findall(r'\]\(([^)]+)\)',s):
        u=urlsplit(dest)
        if not u.scheme and u.path:check((ROOT/unquote(u.path)).is_file(),'relative document '+dest)
b=json.loads((ROOT/'bundle.json').read_text());run=json.loads((ROOT/b['run_path']).read_text());check(b['run']==run,'bundled run values exact');check(b['expected']==json.loads((ROOT/'expected.json').read_text()),'bundled hand expectations exact');check(hashlib.sha256((ROOT/b['run_path']).read_bytes()).hexdigest()==b['run_sha256'],'saved run bytes bound');h=hashlib.sha256((ROOT/'bundle.json').read_bytes()).hexdigest();check("DATA_SHA='"+h+"'" in (ROOT/'lesson.js').read_text(),'bundle digest pinned');check(len(run['records'])==5,'runtime records count')
s=json.loads((ROOT/'sources.json').read_text())
def walk(v):
    if isinstance(v,dict):
        if 'local_excerpt' in v:
            f=ROOT/v['local_excerpt'];key=next(k for k in v if 'excerpt' in k and 'sha' in k);check(hashlib.sha256(f.read_bytes()).hexdigest()==v[key],'excerpt '+v['local_excerpt'])
        for x in v.values():walk(x)
    elif isinstance(v,list):
        for x in v:walk(x)
walk(s)
report={'project':'Atlas','passed':True,'checks':checks,'count':len(checks),'actual_browser':0,'actual_dom':0,'target_execution':0};(ROOT/'records/static-check.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print(json.dumps({'passed':True,'count':len(checks),'browser':0}))

"""Atlas: source/link/binding read only; never starts a server or browser."""
import ast
import datetime
import hashlib
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import sys
from urllib.parse import urlsplit, parse_qs

BASE = Path(__file__).resolve().parent
checks = []
def check(ok, label):
    if not ok:
        raise AssertionError(label)
    checks.append(label)
def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()
class Tags(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids=[]
        self.links=[]
    def handle_starttag(self, tag, attrs):
        attrs=dict(attrs)
        if 'id' in attrs:self.ids.append(attrs['id'])
        for key in ('href','src'):
            if key in attrs:self.links.append(attrs[key])

tree=ast.parse((BASE/'serve.py').read_text())
allowed=next(ast.literal_eval(node.value) for node in tree.body if isinstance(node,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='ALLOWED' for t in node.targets))
related=json.loads((BASE/'related-sources.json').read_text())
links=[]
for name in ('index.html','related.html'):
    h=Tags();h.feed((BASE/name).read_text())
    check(len(h.ids)==len(set(h.ids)),name+' unique IDs')
    links.extend(h.links)
    if name=='index.html':
        app=(BASE/'app.js').read_text()
        for ident in sorted(set(re.findall(r"\$\('([^']+)'\)",app))):
            check(ident in h.ids,'app target '+ident)
for name in ('README.md','COVERAGE.md','REPRODUCE.md','SKILL.md','SOURCES.md'):
    text=(BASE/name).read_text();check('Atlas' in text,name+' project name')
    links.extend(re.findall(r'\]\(([^)]+)\)',text))
for link in links:
    u=urlsplit(link)
    if u.scheme or not u.path:continue
    check(u.path in allowed,'server allows '+link)
    check((BASE/u.path).is_file(),'local file '+link)
    if u.path=='related.html':
        check(parse_qs(u.query).get('topic',[''])[0] in related,'related key '+link)
for key,source in related.items():
    check(sha(Path(source['path']))==source['sha256'],'related fixed bytes '+key)
    check(source['sha256'] in (BASE/'related.js').read_text(),'related JS pin '+key)
for key,source in json.loads((BASE/'reader-inputs.json').read_text()).items():
    check(sha(BASE/source['path'])==source['sha256'],'reader fixed bytes '+key)
    check(source['sha256'] in (BASE/'app.js').read_text(),'app pin '+key)
raw=json.loads((BASE/'observations/run-01/results.json').read_text())
for name,digest in raw['inputs'].items():
    check(sha(BASE/name)==digest,'runtime current '+name)
    check(sha(BASE/'observations/run-01/inputs'/name)==digest,'runtime snapshot '+name)
for path in BASE.glob('*.py'):
    ast.parse(path.read_text());check(True,'Python syntax '+path.name)
check('__INPUTS__' not in app,'no placeholder')
check('if(g!==generation)return' in app and 'controller?.abort()' in app,'response invalidation source present')
record={'Atlas':'Bayes static source and reference check','at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'passed':True,'checks':len(checks),'details':checks,'localReferenceCountIncludingRepeated':sum(not urlsplit(x).scheme for x in links),'producerExecuted':False,'browserExecuted':False,'serverExecuted':False,'javascriptEngineParsed':False,'domChecked':False,'imageChecked':False}
if '--record' in sys.argv:
    with (BASE/'verification/static-reader-check.json').open('x') as f:json.dump(record,f,ensure_ascii=False,indent=2);f.write('\n')
print(json.dumps({k:record[k] for k in ('passed','checks','localReferenceCountIncludingRepeated','domChecked')},ensure_ascii=False))

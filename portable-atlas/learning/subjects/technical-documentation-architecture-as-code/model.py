"""小JSON→Markdown/SVG、sourceとartifactを結び付ける有限生成器。"""
import copy, hashlib, html, json, re, subprocess, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parent
SCENARIOS = ('baseline','stale-contract','regenerated','stale-code','broken-anchor','unsupported-function','wrong-output','tampered-svg')
SOURCES = {
 'examples': 'https://docs.python.org/3/library/doctest.html#how-it-works',
 'markdown': 'https://spec.commonmark.org/0.31.2/#fenced-code-blocks',
 'svg': 'https://www.w3.org/TR/SVG2/struct.html#SVGElement',
 'decisions': 'https://adr.github.io/'
}
def digest(data):
    return hashlib.sha256(data.encode() if isinstance(data,str) else data).hexdigest()
def canonical(value):
    return json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(',',':'))
def validate(c):
    if type(c) is not dict or set(c) != {'schema','title','functions'} or c['schema'] != 1:
        raise ValueError('contract schema')
    if not isinstance(c['title'],str) or len(c['title']) > 80 or '\n' in c['title']:
        raise ValueError('title')
    if type(c['functions']) is not list or not 1 <= len(c['functions']) <= 4:
        raise ValueError('function count')
    seen = set()
    for f in c['functions']:
        if set(f) != {'name','summary','examples'} or f['name'] not in {'clamp','add'}:
            raise ValueError('unsupported function')
        if f['name'] in seen: raise ValueError('duplicate function')
        seen.add(f['name'])
        if not isinstance(f['summary'],str) or not re.fullmatch(r'[^\n<>\[\]`]{1,80}', f['summary']): raise ValueError('summary')
        if type(f['examples']) is not list or not 1 <= len(f['examples']) <= 10: raise ValueError('example count')
        for e in f['examples']:
            if set(e) != {'args','stdout'} or type(e['args']) is not list or len(e['args']) != (3 if f['name']=='clamp' else 2): raise ValueError('example schema')
            if any(type(x) is not int or abs(x)>100 for x in e['args']): raise ValueError('argument range')
            if f['name']=='clamp' and e['args'][1]>e['args'][2]: raise ValueError('bounds')
            if not isinstance(e['stdout'],str) or not re.fullmatch(r'-?[0-9]{1,4}\n',e['stdout']): raise ValueError('stdout')
def generate(c, code):
    validate(c)
    md = [f"# {c['title']}", '', '[構造図](architecture.svg)', '', '## 索引', '']
    md += [f"- [{f['name']}](#api-{f['name']})" for f in c['functions']]
    for f in c['functions']:
        md += ['', f'<a id="api-{f["name"]}"></a>', f'## {f["name"]}', '', f['summary'], '']
        for e in f['examples']:
            call = f"{f['name']}({', '.join(map(str,e['args']))})"
            md += ['```python', f'from api import {f["name"]}', f'print({call})', '```', '', '期待stdout:', '```text', e['stdout'].rstrip('\n'), '```', '']
    md += ['## 原典', ''] + [f'- [{k}]({v})' for k,v in SOURCES.items()]
    markdown='\n'.join(md)+'\n'
    svg='<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 600 200" role="img"><title>契約から文書と実行例への流れ</title>'
    for i,label in enumerate(['JSON契約','生成Markdown / SVG','snippet実行']):
        x=10+i*200
        svg+=f'<rect x="{x}" y="50" width="180" height="80" rx="10" fill="#e0f2fe"/><text x="{x+90}" y="95" text-anchor="middle" font-size="14">{html.escape(label)}</text>'
        if i<2: svg+=f'<path d="M {x+180} 90 h 20" stroke="#164e63"/>'
    svg+='</svg>\n'
    artifacts={'api.md':markdown,'architecture.svg':svg}
    manifest={'contractSha256':digest(canonical(c)), 'implementationSha256':digest(code), 'artifacts':{k:digest(v) for k,v in artifacts.items()}}
    return artifacts,manifest

def inspect(c,code,artifacts,manifest):
    validate(c)
    failures=[]
    if manifest['contractSha256'] != digest(canonical(c)): failures.append('stale-contract')
    if manifest['implementationSha256'] != digest(code): failures.append('stale-code')
    for name,raw in artifacts.items():
        if manifest['artifacts'].get(name)!=digest(raw): failures.append('artifact-digest:'+name)
    ids=set(re.findall(r'<a id="([a-z-]+)"></a>',artifacts['api.md']))
    refs=re.findall(r'\]\(#([a-z-]+)\)',artifacts['api.md'])
    if any(ref not in ids for ref in refs): failures.append('broken-local-anchor')
    if failures:
        return {'status':'rejected','failures':failures,'snippets':[], 'snippetExecution':'skipped before integrity'}
    documented=re.findall(r'```python\n(.*?)```\n\n期待stdout:\n```text\n(.*?)```', artifacts['api.md'], re.S)
    count=sum(len(f['examples']) for f in c['functions'])
    if len(documented)!=count: return {'status':'rejected','failures':['snippet-count'],'snippets':[],'snippetExecution':'skipped malformed document'}
    rows=[]
    for f in c['functions']:
        for e in f['examples']:
            source=f"from api import {f['name']}\nprint({f['name']}({','.join(map(str,e['args']))}))\n"
            doc_source,doc_expected=documented[len(rows)]
            if doc_source!=source.replace(',', ', ') or doc_expected!=e['stdout']:
                return {'status':'rejected','failures':['snippet-contract'],'snippets':[],'snippetExecution':'skipped unrecognized snippet'}
            source=doc_source
            p=subprocess.run([sys.executable,'-B','-c',source],cwd=ROOT,text=True,capture_output=True,timeout=3)
            rows.append({'function':f['name'],'args':e['args'],'source':source,'expected':e['stdout'],'stdout':p.stdout,'stderr':p.stderr,'exitCode':p.returncode,'passed':p.returncode==0 and p.stdout==e['stdout']})
    return {'status':'passed' if all(r['passed'] for r in rows) else 'rejected','failures':[] if all(r['passed'] for r in rows) else ['snippet-output'],'snippets':rows,'snippetExecution':'actual subprocess'}

def experiment(scenario):
    if scenario not in SCENARIOS: raise ValueError('unsupported scenario')
    c=json.loads((ROOT/'contract.json').read_text()); code=(ROOT/'api.py').read_bytes()
    artifacts={p.name:p.read_text() for p in (ROOT/'generated').iterdir() if p.name in {'api.md','architecture.svg'}}
    manifest=json.loads((ROOT/'generated/manifest.json').read_text())
    if scenario in {'stale-contract','regenerated'}:
        c['functions'][0]['examples'][-1]={'args':[11,0,8],'stdout':'8\n'}
        if scenario=='regenerated': artifacts,manifest=generate(c,code)
    if scenario=='stale-code': code+=b'\n# changed implementation input\n'
    if scenario=='broken-anchor':
        artifacts['api.md']=artifacts['api.md'].replace('](#api-add)','](#api-missing)')
        manifest['artifacts']['api.md']=digest(artifacts['api.md']) # integrity alone cannot validate links
    if scenario=='unsupported-function': c['functions'][1]['name']='divide'
    if scenario=='wrong-output':
        c['functions'][1]['examples'][0]['stdout']='6\n'
        artifacts,manifest=generate(c,code)
    if scenario=='tampered-svg': artifacts['architecture.svg']=artifacts['architecture.svg'].replace('JSON契約','手編集')
    try: result=inspect(c,code,artifacts,manifest)
    except ValueError as e: result={'status':'rejected','failures':[str(e)],'snippets':[],'snippetExecution':'skipped unsupported input'}
    return {'scenario':scenario,'contract':c,'manifest':manifest,'observedArtifactSha256':{k:digest(v) for k,v in artifacts.items()},'result':result,'artifacts':artifacts}

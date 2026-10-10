"""Atlas: local source/links/data checks only; never launch a browser or target."""
import argparse,hashlib,json,re
from pathlib import Path
ROOT=Path(__file__).resolve().parent
p=argparse.ArgumentParser();p.add_argument('--output',type=Path,default=ROOT/'records/static-checks.json');a=p.parse_args();checks=[]
def check(ok,n):
 if not ok:raise AssertionError(n)
 checks.append(n)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
for name in ['README.md','CONTRACT.md','COVERAGE.md','SOURCES.md','SKILL.md','RUN_CONDITIONS.md','index.html','reference.html','MEASUREMENTS.md','GUI_VERIFICATION.md','HANDOFF.md']:
 s=(ROOT/name).read_text();check('Atlas' in s,'project name '+name);check('原票' not in s,'reader language '+name)
 patterns=[r'href="([^"#]+)(?:#[^"]*)?"'] if name.endswith('.html') else [r'\]\(([^)]+)\)']
 for pattern in patterns:
  for link in re.findall(pattern,s):
   if link.startswith(('https:','http:')):continue
   q=(ROOT/link.split('#')[0]).resolve();check(q.is_relative_to(ROOT) and q.is_file(),'local usable reference '+name+' -> '+link)
for x in json.loads((ROOT/'sources.json').read_text())['excerpts']:check(sha(ROOT/x['local_excerpt'])==x['excerpt_sha256'],'fixed excerpt '+x['local_excerpt'])
b=json.loads((ROOT/'bundle.json').read_text());check(b['expected_text']==(ROOT/'expected.json').read_text(),'expected original bytes in reader');check(sha(ROOT/'bundle.json') in (ROOT/'lesson.js').read_text(),'bundle pin')
check((ROOT/'SKILL.md').read_text().startswith('---\nname:') and '\ndescription:' in (ROOT/'SKILL.md').read_text(),'Skill metadata')
if b['run_text'] is not None:
 r=json.loads(b['run_text']);s=json.loads((ROOT/'status.json').read_text());check(b['run_text']==(ROOT/s['observation']).read_text(),'saved execution bytes in reader');check(r['collection_complete'] is True,'reader uses complete result')
r={'project':'Atlas','kind':'static-only-not-browser','passed':True,'checks':checks,'count':len(checks),'browser_starts':0,'target_starts':0};a.output.write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n');print(json.dumps({'passed':True,'checks':len(checks),'actual_DOM':0}))

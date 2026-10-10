import hashlib,json,re,sys
from pathlib import Path
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parent.parent;Q=ROOT/'qa'
def snap():return {str(p.relative_to(ROOT)):(hashlib.sha256(p.read_bytes()).hexdigest(),p.stat().st_mtime_ns) for p in ROOT.rglob('*') if p.is_file()}
def cleared(s):
 assert s['resultsHidden'] and s['answerHidden'] and not s['answerOpen'] and not s['traceOpen'];assert all(v=='' for v in s['fields'].values());assert all(v is None for v in s['links'].values())
def result(r):return {k:r[k] for k in ['exit','exception_class','final_value']}
before=snap();raw=json.loads((ROOT/'observation-data.js').read_text().removeprefix('window.CYCLE_OBSERVATION=').strip().removesuffix(';'));records={r['id']:r for r in raw['rows']};table=json.loads((ROOT/'expected-table.json').read_text());expected={e['id']:e for e in table['rows']};options=['','throws','one','live'];rows=json.loads((Q/'iab-matrix.json').read_text())
assert len(rows)==20 and {(r['case'],r['prediction']) for r in rows}=={(c,p) for c in expected for p in options}
for row in rows:
 c,p=row['case'],row['prediction'];e=expected[c];r=records[c];reset=row['caseReset'];cl=row['cleared'];co=row['compared'];op=row['opened'];cleared(reset);cleared(cl);assert reset['prediction']==reset['value']=='' and cl['prediction']==p and cl['value']==('2' if c=='live-update' else '1')
 assert co['message'].startswith('予想未選択。' if not p else '予想と一致。' if p==e['category'] else '予想と不一致。')
 assert not co['resultsHidden'] and not co['answerHidden'] and not co['answerOpen'] and not co['traceOpen'] and co['fields']['answer-body']
 assert op['answerOpen'] and op['traceOpen'] and op['fields']==co['fields']
 f=co['fields'];assert json.loads(f['outcome'])==result(e['expected']);assert json.loads(f['graph'])=={'edges':e['graph'],'cycle':e['cycle']}
 for id in ['immediate','delayed']:assert json.loads(f[id])==result(expected[id]['expected'])
 assert f['events']=='\n'.join(f"{i+1}. "+json.dumps(ev,separators=(',',':')) for i,ev in enumerate(e['expected']['events']))
 assert f['stdout']==r['stdout'] and f['stderr']==(r['stderr'] or '（空）') and str(r['pid']) in f['process'] and raw['run_id'] in f['run']
 assert co['links']=={'raw':f"observations/{raw['run_id']}/raw.json",'command':f"observations/{raw['run_id']}/command.json",'fixture-a':f"fixtures/{c}/a.mjs",'fixture-b':f"fixtures/{c}/b.mjs"}
 if e['category']=='throws':assert '成功値なし' in f['classification'] and json.loads(f['outcome'])['final_value'] is None
 for s in [cl,co,op]:assert s['viewport']==s['scrollWidth']
controls=json.loads((Q/'prediction-controls.json').read_text());assert len(controls)==4 and {r['target'] for r in controls}==set(options)
for r in controls:
 s,c=r['success'],r['cleared'];assert s['message'].startswith('予想と一致。') and s['answerOpen'] and s['traceOpen'] and s['fields']['answer-body'];assert s['prediction']!=r['target'];cleared(c);assert c['prediction']==r['target'] and c['value']==s['value'] and c['message']=='予想を変更しました。比較するで照合してください。'
edits=json.loads((Q/'editable-controls.json').read_text());targets=['','0','1','2','9','abc','10','-1'];assert len(edits)==8 and {r['target'] for r in edits}==set(targets)
for r in edits:
 s,c,f=r['success'],r['cleared'],r['compared'];assert s['message'].startswith('予想と一致。') and s['answerOpen'] and s['traceOpen'] and s['fields']['answer-body'] and s['value']!=r['target'];cleared(c);assert c['value']==r['target'] and c['prediction']==s['prediction'] and c['scenario']==s['scenario'] and c['message']=='予想値を変更しました。比較するで照合してください。'
 if r['target'] in ['abc','10','-1']:cleared(f);assert f['message'].startswith('予想入力を拒否。') and f['value']==r['target']
 else:assert f['message'].startswith('予想と不一致。') and not f['resultsHidden'] and not f['answerOpen']
trans=json.loads((Q/'success-to-failure.json').read_text());assert len(trans)==3 and {t['target'] for t in trans}=={'immediate','early-call','prediction-input'}
for t in trans:
 s,r,f=t['success'],t['reset'],t['failure'];assert s['scenario']=='delayed' and s['answerOpen'] and s['message'].startswith('予想と一致。');cleared(r)
 if t['target']=='prediction-input':cleared(f);assert f['value']=='abc' and f['message'].startswith('予想入力を拒否。')
 else:
  assert r['prediction']==r['value']=='' and f['message'].startswith('予想と一致。') and not f['answerOpen'] and not f['traceOpen'];assert json.loads(f['fields']['outcome'])=={'exit':1,'exception_class':'ReferenceError','final_value':None};assert 'ReferenceError' in f['fields']['stderr'] and not 'entry:final' in f['fields']['events']
caps=json.loads((Q/'capture-dom.json').read_text());assert len(caps)==3
for c in caps:
 s=c['dom'];assert s['viewport']==s['scrollWidth'] and (Q/(c['name']+'.jpg')).read_bytes()[:2]==b'\xff\xd8'
 if c['name']=='mobile-prediction-refusal':cleared(s);assert s['value']=='abc' and s['message'].startswith('予想入力を拒否。')
 else:assert s['answerOpen'] and s['message'].startswith('予想と一致。')
preview=json.loads((Q/'preview.json').read_text());assert preview['iab']['status']=='closed' and preview['iab']['blank_closed'] and preview['viewport_reset'] and preview['server']['stopped'] and preview['server']['stop_exit']==0
links=[]
for doc in [ROOT/'README.md',ROOT/'index.html']:
 targets=re.findall(r'\]\(([^)]+)\)',doc.read_text()) if doc.suffix=='.md' else re.findall(r'(?:href|src)="([^"]+)"',doc.read_text())
 for target in targets:
  if target.startswith(('https:','http:','#')):continue
  assert (doc.parent/target.split('#')[0]).exists(),target;links.append(str(doc.relative_to(ROOT))+':'+target)
assert snap()==before
print(json.dumps({'status':'passed','run_id':raw['run_id'],'comparisons':20,'select_controls_open_then_empty':4,'editable_controls_open_then_empty':8,'success_to_failure':3,'captures':3,'local_links_exist':links,'read_only_files':len(before),'all_hash_mtime_equal':True},ensure_ascii=False))

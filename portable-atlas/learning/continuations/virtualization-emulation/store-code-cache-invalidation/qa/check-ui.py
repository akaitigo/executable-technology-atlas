import hashlib,json,re,sys
from pathlib import Path
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parent.parent;Q=ROOT/'qa'
def snap():return {str(p.relative_to(ROOT)):(hashlib.sha256(p.read_bytes()).hexdigest(),p.stat().st_mtime_ns) for p in ROOT.rglob('*') if p.is_file()}
def cleared(s):
 assert s['resultsHidden'] and s['answerHidden'] and not s['answerOpen'] and not s['traceOpen']
 for k in ['answerBody','fetch','invalidate','stale','ranges','memory','trace','run','classification']:assert s[k]=='',k
 assert s['raw'] is None and s['command'] is None
before=snap();raw=json.loads((ROOT/'observation-data.js').read_text().removeprefix('window.STORE_OBSERVATION=').strip().removesuffix(';'));records={r['id']:r for r in raw['rows']};table=json.loads((ROOT/'expected-table.json').read_text());expected={e['id']:e for e in table['rows']};options=['','stale-diverges','same-halt','illegal','input','budget']
rows=json.loads((Q/'iab-matrix.json').read_text());assert len(rows)==60 and {(r['case'],r['prediction']) for r in rows}=={(c,p) for c in expected for p in options}
for row in rows:
 c,p=row['case'],row['prediction'];r=records[c];e=expected[c];reset=row['caseReset'];cl=row['cleared'];co=row['compared'];op=row['opened'];cleared(reset);cleared(cl);assert reset['prediction']=='' and cl['prediction']==p
 assert co['message'].startswith('予想未選択。' if not p else '予想と一致。' if p==e['category'] else '予想と不一致。')
 assert not co['resultsHidden'] and not co['answerHidden'] and not co['answerOpen'] and not co['traceOpen'] and co['answerBody']
 assert op['answerOpen'] and op['traceOpen'] and op['answerBody']==co['answerBody']
 for mode in ['fetch','invalidate','stale']:
  assert json.loads(co[mode])=={k:e[mode][k] for k in ['status','pc','a','steps','diagnostic']}
  assert json.loads(co['trace'])[mode]=={k:r['variants'][mode][k] for k in ['trace','cache_events','decoded_blocks']}
 ranges=json.loads(co['ranges']);assert ranges['prewarm']==r['prewarm'] and ranges['invalidating']==r['variants']['invalidate']['store_events'] and ranges['stale']==r['variants']['stale']['store_events']
 assert ranges['predecoded']==[{k:b[k] for k in ['start','addresses','instructions']} for b in r['variants']['invalidate']['decoded_blocks'][:len(r['prewarm'])]]
 assert co['raw']==f"observations/{raw['run_id']}/raw.json" and co['command']==f"observations/{raw['run_id']}/command.json" and raw['run_id'] in co['run']
 if e['category']=='input':assert 'traceなし' in co['memory'] and r['variants']['fetch']['memory'] is None
 elif e['category']=='budget':assert '最終A7は主張しません' in co['answerBody']
 for s in [cl,co,op]:assert s['viewport']==s['scrollWidth']
controls=json.loads((Q/'prediction-controls.json').read_text());assert len(controls)==6 and {r['target'] for r in controls}==set(options)
for r in controls:
 s,c=r['success'],r['cleared'];assert s['message'].startswith('予想と一致。') and s['answerOpen'] and s['traceOpen'] and s['answerBody'];assert s['prediction']!=r['target'];cleared(c);assert c['prediction']==r['target'] and c['message']=='予想を変更しました。比較するで照合してください。'
trans=json.loads((Q/'success-to-refusal.json').read_text());assert len(trans)==3 and {t['failure']['scenario'] for t in trans}=={'input','illegal','budget'}
for t in trans:
 assert t['success']['scenario']=='operand' and t['success']['answerOpen'] and t['success']['answerBody'];cleared(t['reset']);f=t['failure'];assert f['message'].startswith('予想と一致。') and not f['answerOpen']
 assert json.loads(f['fetch'])['status']=={'input':'input','illegal':'illegal','budget':'budget'}[f['scenario']]
captures=json.loads((Q/'capture-dom.json').read_text());assert len(captures)==3
for c in captures:assert c['dom']['viewport']==c['dom']['scrollWidth'] and c['dom']['answerOpen'] and c['dom']['message'].startswith('予想と一致。') and (Q/(c['name']+'.jpg')).read_bytes()[:2]==b'\xff\xd8'
preview=json.loads((Q/'preview.json').read_text());assert preview['iab']['status']=='closed' and preview['iab']['blank_closed'] and preview['viewport_reset'] and preview['server']['stopped'] and preview['server']['stop_exit']==0
links=[]
for doc in [ROOT/'README.md',ROOT/'SPEC.md',ROOT/'index.html']:
 targets=re.findall(r'\]\(([^)]+)\)',doc.read_text()) if doc.suffix=='.md' else re.findall(r'(?:href|src)="([^"]+)"',doc.read_text())
 for target in targets:
  if target.startswith(('https:','http:','#')):continue
  assert (doc.parent/target.split('#')[0]).exists(),target;links.append(str(doc.relative_to(ROOT))+':'+target)
assert snap()==before
print(json.dumps({'status':'passed','run_id':raw['run_id'],'comparisons':60,'all_prediction_controls_open_then_empty':6,'success_to_refusal':3,'captures':3,'local_links_exist':links,'read_only_files':len(before),'all_hash_mtime_equal':True},ensure_ascii=False))

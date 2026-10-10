import hashlib,json,re,sys
from pathlib import Path
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2];Q=Path(__file__).resolve().parent
def snapshot():return {str(p.relative_to(ROOT)):(hashlib.sha256(p.read_bytes()).hexdigest(),p.stat().st_mtime_ns) for p in ROOT.rglob('*') if p.is_file()}
def cleared(state):
 assert state['resultsHidden'] and state['answerHidden'] and not state['answerOpen'] and not state['traceOpen']
 assert state['artifactLinkHidden'] and state['artifactHref'] is None
 assert all(state[k]=='' for k in ['answerText','normal','faulty','classification','trace','artifact','direct','reachable','declared','Bdigest','buildStatus'])
before=snapshot();raw=json.loads((ROOT/'observation-data.js').read_text().removeprefix('window.MATERIAL_OBSERVATION=').strip().removesuffix(';'));records={r['id']:r for r in raw['rows']};table=json.loads((ROOT/'expected-table.json').read_text());expected={r['id']:r for r in table['rows']}
rows=json.loads((Q/'iab-matrix.json').read_text());assert len(rows)==56 and {r['case'] for r in rows}==set(expected)
for row in rows:
 c=row['case'];pred=row['prediction'];reset=row['caseReset'];clear=row['cleared'];comp=row['compared'];opened=row['opened'];r=records[c];e=expected[c]
 for state in [reset,clear]:cleared(state)
 assert reset['prediction']=='' and clear['prediction']==pred
 if pred:assert clear['message']=='予想を変更しました。比較するで照合してください。'
 prefix='予想未選択。' if not pred else '予想と一致。' if pred==e['category'] else '予想と不一致。';assert comp['message'].startswith(prefix)
 assert not comp['resultsHidden'] and not comp['answerOpen'] and not comp['traceOpen']
 assert comp['answerHidden']==(e['category']=='error') and opened['traceOpen'] and opened['answerOpen']==(e['category']!='error')
 assert (comp['answerText']=='')==(e['category']=='error') and opened['answerText']==comp['answerText']
 assert comp['viewport']==comp['scrollWidth']
 assert json.loads(comp['normal'])==r['normal'] and json.loads(comp['faulty'])==r['faulty'] and json.loads(comp['trace'])=={'materials':r['materials'],'declared':r['declared'],'trace':r['trace']}
 assert comp['reachable']=='実到達集合: '+(json.dumps(e['reachable'],separators=(',',':')) if e['reachable'] is not None else '未確定')
 assert comp['declared']=='申告集合: '+(json.dumps(sorted(r['declared']),separators=(',',':')) if r['declared'] is not None else '未読取')
 if e['artifact_literal']:
  b=bytes.fromhex(table['literal_artifacts'][e['artifact_literal']]);sha=hashlib.sha256(b).hexdigest()
  assert comp['artifact']==f"artifact SHA256: {sha}\nbytes: {len(b)}\n実生成bytes:\n{b.decode('ascii')}"
  assert not comp['artifactLinkHidden'] and comp['artifactHref']==f"observations/{raw['run_id']}/{c}/artifact.bin"
  assert (ROOT/comp['artifactHref']).read_bytes()==b
 else:assert comp['artifact']=='artifactなし（build前拒否 / 読取失敗）' and comp['artifactLinkHidden'] and comp['artifactHref'] is None
 assert comp['Bdigest']==(f"B実digest: {r['materials']['B']['sha256']} / bytes: {r['materials']['B']['size']}" if 'B' in r['materials'] else 'B実digest: 未読取')
 assert comp['buildStatus']==f"生成観測: {r['status']} / artifact: {'生成済み' if r['artifact'] else 'なし'}"
 assert raw['run_id'] in comp['run'] and comp['raw']==f"observations/{raw['run_id']}/raw.json"
controls=json.loads((Q/'prediction-controls.json').read_text());targets=['','agree','changed','undeclared','closure','refused','error'];assert len(controls)==7 and {r['target'] for r in controls}==set(targets)
for r in controls:
 s,c=r['success'],r['cleared'];assert s['answerOpen'] and s['traceOpen'] and s['answerText'] and not s['artifactLinkHidden'];assert s['prediction']!=r['target'];cleared(c);assert c['prediction']==r['target'] and c['scenario']==s['scenario']
conditions=json.loads((Q/'condition-controls.json').read_text());assert len(conditions)==8 and {r['target'] for r in conditions}==set(expected)
for r in conditions:
 s,c=r['success'],r['cleared'];assert s['answerOpen'] and s['traceOpen'] and s['answerText'] and s['scenario']!=r['target'];cleared(c);assert c['scenario']==r['target'] and c['prediction']==''
transitions=json.loads((Q/'success-to-failure.json').read_text());assert len(transitions)==4
for t in transitions:
 s,reset,f=t['success'],t['reset'],t['failure'];assert s['scenario']=='baseline' and s['answerOpen'] and s['traceOpen'] and s['answerText'];cleared(reset);assert reset['prediction']=='' and reset['scenario']==t['target'];assert not f['answerOpen'] and not f['traceOpen']
 assert json.loads(f['normal'])==records[t['target']]['normal'];assert json.loads(f['trace'])=={'materials':records[t['target']]['materials'],'declared':records[t['target']]['declared'],'trace':records[t['target']]['trace']}
 if t['target']=='B-undeclared':assert not f['artifactLinkHidden'] and f['artifactHref'] and f['answerText']
 else:assert f['artifactLinkHidden'] and f['artifactHref'] is None and records[t['target']]['artifact'] is None
 assert f['answerHidden']==(t['target']=='read-failure')
 if t['target']=='read-failure':assert f['answerText']==''
before_bug=json.loads((Q/'before-bug.json').read_text());after_bug=json.loads((Q/'after-fresh.json').read_text());assert before_bug['changed']['answerText']==before_bug['success']['answerText'] and before_bug['changed']['prediction']=='agree';assert after_bug['success']['answerText']==before_bug['success']['answerText'];cleared(after_bug['changed']);assert after_bug['changed']['prediction']=='agree'
assert '20261005T153136167655Z-material'==raw['run_id']
context=json.loads((Q/'context.json').read_text());archive=ROOT/context['before'];manifest=json.loads((archive/'snapshot.json').read_text());assert manifest['original_file_count']==64
changed=[]
for n,v in manifest['files'].items():
 p=archive/'files'/n;assert hashlib.sha256(p.read_bytes()).hexdigest()==v['sha256'] and p.stat().st_mtime_ns==v['mtime_ns']
 current=ROOT/n
 if hashlib.sha256(current.read_bytes()).hexdigest()!=v['sha256']:changed.append(n)
 else:assert current.stat().st_mtime_ns==v['mtime_ns'],n
assert set(changed)=={'app.js','README.md','observation-data.js'},changed
preview=json.loads((Q/'preview.json').read_text());assert preview['server']['old_origin']['stopped'] and preview['server']['fresh_origin']['stopped'] and preview['viewport_reset']
captures=json.loads((Q/'capture-dom.json').read_text());assert len(captures)==2
for c in captures:
 assert c['dom']['viewport']==c['dom']['scrollWidth'] and (Q/(c['name']+'.jpg')).read_bytes()[:2]==b'\xff\xd8'
 if c['name']=='after-reset':cleared(c['dom']);assert c['dom']['prediction']=='agree'
 else:assert c['dom']['answerHidden'] and c['dom']['answerText']=='' and c['dom']['artifactLinkHidden'] and c['dom']['artifactHref'] is None
links=[]
for doc in [ROOT/'README.md',ROOT/'index.html']:
 targets=re.findall(r'\]\(([^)]+)\)',doc.read_text()) if doc.suffix=='.md' else re.findall(r'(?:href|src)="([^"]+)"',doc.read_text())
 for target in targets:
  if target.startswith(('http:', 'https:','#')):continue
  assert (doc.parent/target.split('#')[0]).exists(),target;links.append(str(doc.relative_to(ROOT))+':'+target)
assert snapshot()==before
print(json.dumps({'status':'passed','run_id':raw['run_id'],'comparisons':56,'prediction_clears':56,'case_resets':8,'all_prediction_controls_open_then_empty':7,'all_condition_controls_open_then_empty':8,'success_to_failure_transitions':4,'before_snapshot_files':64,'original_nonmodified_files_hash_mtime_preserved':61,'artifact_file_literal_bytes_verified':True,'local_links_exist':links,'read_only_files':len(before),'all_hash_mtime_equal':True},ensure_ascii=False))

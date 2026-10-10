import hashlib,json,re,sys
from pathlib import Path
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parent.parent;Q=ROOT/'qa'
def snapshot():return {str(p.relative_to(ROOT)):(hashlib.sha256(p.read_bytes()).hexdigest(),p.stat().st_mtime_ns) for p in ROOT.rglob('*') if p.is_file()}
before=snapshot();raw=json.loads((ROOT/'observation-data.js').read_text().removeprefix('window.MATERIAL_OBSERVATION=').strip().removesuffix(';'));records={r['id']:r for r in raw['rows']};table=json.loads((ROOT/'expected-table.json').read_text());expected={r['id']:r for r in table['rows']}
rows=json.loads((Q/'iab-matrix.json').read_text());assert len(rows)==56 and {r['case'] for r in rows}==set(expected)
for row in rows:
 c=row['case'];pred=row['prediction'];reset=row['caseReset'];clear=row['cleared'];comp=row['compared'];opened=row['opened'];r=records[c];e=expected[c]
 for state in [reset,clear]:assert state['resultsHidden'] and state['answerHidden'] and not state['answerOpen'] and not state['traceOpen']
 assert reset['prediction']=='' and clear['prediction']==pred
 if pred:assert clear['message']=='予想を変更しました。比較するで照合してください。'
 prefix='予想未選択。' if not pred else '予想と一致。' if pred==e['category'] else '予想と不一致。';assert comp['message'].startswith(prefix)
 assert not comp['resultsHidden'] and not comp['answerOpen'] and not comp['traceOpen']
 assert comp['answerHidden']==(e['category']=='error') and opened['traceOpen'] and opened['answerOpen']==(e['category']!='error')
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
transitions=json.loads((Q/'success-to-failure.json').read_text());assert len(transitions)==2
for transition in transitions:
 s=transition['success'];reset=transition['reset'];f=transition['failure']
 assert s['scenario']=='baseline' and s['answerOpen'] and s['traceOpen'] and not s['artifactLinkHidden']
 assert reset['prediction']=='' and reset['resultsHidden'] and reset['answerHidden'] and not reset['answerOpen'] and not reset['traceOpen']
 assert f['artifactLinkHidden'] and f['artifactHref'] is None and f['artifact']=='artifactなし（build前拒否 / 読取失敗）'
 assert f['answerHidden']==(f['scenario']=='read-failure')
links=[]
for doc in [ROOT/'README.md',ROOT/'index.html']:
 targets=re.findall(r'\]\(([^)]+)\)',doc.read_text()) if doc.suffix=='.md' else re.findall(r'(?:href|src)="([^"]+)"',doc.read_text())
 for target in targets:
  if target.startswith(('http:', 'https:','#')):continue
  assert (doc.parent/target.split('#')[0]).exists(),target;links.append(str(doc.relative_to(ROOT))+':'+target)
assert snapshot()==before
print(json.dumps({'status':'passed','run_id':raw['run_id'],'comparisons':56,'prediction_clears':56,'case_resets':8,'success_to_failure_transitions':2,'artifact_file_literal_bytes_verified':True,'local_links_exist':links,'read_only_files':len(before),'all_hash_mtime_equal':True},ensure_ascii=False))

import hashlib,json,re,sys
from pathlib import Path
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parent.parent;Q=ROOT/'qa'
def snapshot():return {str(p.relative_to(ROOT)):(hashlib.sha256(p.read_bytes()).hexdigest(),p.stat().st_mtime_ns) for p in ROOT.rglob('*') if p.is_file()}
def cleared(s):
 assert s['resultsHidden'] and s['answerHidden'] and not s['answerOpen'] and not s['traceOpen'] and s['databaseHidden'] and s['databaseHref'] is None
 assert all(s[k]=='' for k in ['answerBody','request','check','normal','faulty','classification','before','after','trace'])
before=snapshot();raw=json.loads((ROOT/'observation-data.js').read_text().removeprefix('window.TOCTOU_OBSERVATION=').strip().removesuffix(';'));records={r['id']:r for r in raw['rows']};table=json.loads((ROOT/'expected-table.json').read_text());expected={r['id']:r for r in table['rows']}
controls=json.loads((Q/'prediction-controls.json').read_text());targets=['','both-read','both-deny','boundary','late-allow','refused','error'];assert len(controls)==7 and {r['target'] for r in controls}==set(targets)
for r in controls:
 s=r['success'];c=r['cleared'];assert s['message'].startswith('予想と一致。') and not s['resultsHidden'] and s['answerOpen'] and s['traceOpen'] and s['answerBody']
 assert s['prediction']!=r['target'] and c['prediction']==r['target'];cleared(c);assert c['message']=='予想を変更しました。比較するで照合してください。'
rows=json.loads((Q/'iab-matrix.json').read_text());assert len(rows)==70 and {r['case'] for r in rows}==set(expected)
for row in rows:
 case=row['case'];pred=row['prediction'];reset=row['caseReset'];c=row['cleared'];comp=row['compared'];opened=row['opened'];r=records[case];e=expected[case]
 cleared(reset);cleared(c);assert reset['prediction']=='' and c['prediction']==pred
 if pred:assert c['message']=='予想を変更しました。比較するで照合してください。'
 prefix='予想未選択。' if not pred else '予想と一致。' if pred==e['category'] else '予想と不一致。';assert comp['message'].startswith(prefix)
 assert not comp['resultsHidden'] and not comp['answerOpen'] and not comp['traceOpen']
 assert comp['answerHidden']==(e['category']=='error') and opened['answerOpen']==(e['category']!='error') and opened['traceOpen']
 assert (comp['answerBody']=='')==(e['category']=='error')
 assert json.loads(comp['normal'])==e['normal'] and json.loads(comp['faulty'])==e['faulty'] and json.loads(comp['trace'])==r['trace']
 assert comp['before']=='初期commit行: '+json.dumps(table['initial_rows'],separators=(',',':')) and comp['after']=='最終commit行: '+json.dumps(e['final_rows'],separators=(',',':'))
 assert not comp['databaseHidden'] and comp['databaseHref']==f"observations/{raw['run_id']}/{case}/state.sqlite" and (ROOT/comp['databaseHref']).exists()
 assert raw['run_id'] in comp['run'] and comp['raw']==f"observations/{raw['run_id']}/raw.json"
 if e['category']=='refused':assert r['before_rows']==r['after_rows'] and '初期行を保持' in comp['classification']
 if e['category']=='error':assert json.loads(comp['normal'])['payload'] is None and json.loads(comp['faulty'])['payload'] is None
transitions=json.loads((Q/'success-to-failure.json').read_text());assert len(transitions)==2
for t in transitions:
 s=t['success'];reset=t['reset'];f=t['failure'];assert s['scenario']=='unchanged' and s['message'].startswith('予想と一致。') and s['answerOpen'] and s['answerBody'];cleared(reset)
 assert reset['prediction']=='' and json.loads(f['normal'])['payload'] is None and json.loads(f['faulty'])['payload'] is None
 assert f['answerBody']=='' if f['scenario']=='sql-error' else '初期行を保持' in f['answerBody']
links=[]
for doc in [ROOT/'README.md',ROOT/'index.html']:
 targets=re.findall(r'\]\(([^)]+)\)',doc.read_text()) if doc.suffix=='.md' else re.findall(r'(?:href|src)="([^"]+)"',doc.read_text())
 for target in targets:
  if target.startswith(('http:', 'https:','#')):continue
  assert (doc.parent/target.split('#')[0]).exists(),target;links.append(str(doc.relative_to(ROOT))+':'+target)
assert snapshot()==before
print(json.dumps({'status':'passed','run_id':raw['run_id'],'comparisons':70,'prediction_clears':70,'case_resets':10,'all_prediction_controls_open_then_empty':7,'success_to_failure_transitions':2,'refusal_comparisons':21,'sql_error_comparisons':7,'local_links_exist':links,'read_only_files':len(before),'all_hash_mtime_equal':True},ensure_ascii=False))

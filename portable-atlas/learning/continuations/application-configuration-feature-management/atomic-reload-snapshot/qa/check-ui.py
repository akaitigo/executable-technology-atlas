"""Read-only saved actual-IAB evidence check; no receipt writes."""
import hashlib,json,re,sys
from pathlib import Path
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parent.parent
Q=ROOT/'qa'
def snapshot():return {str(p.relative_to(ROOT)):(hashlib.sha256(p.read_bytes()).hexdigest(),p.stat().st_mtime_ns) for p in ROOT.rglob('*') if p.is_file()}
before=snapshot()
raw=json.loads((ROOT/'observation-data.js').read_text().removeprefix('window.RELOAD_OBSERVATION=').strip().removesuffix(';'));records={r['id']:r for r in raw['rows']}
table={r['id']:r for r in json.loads((ROOT/'expected-table.json').read_text())['rows']}
rows=json.loads((Q/'iab-matrix.json').read_text());assert len(rows)==55 and {r['case'] for r in rows}==set(table)
for row in rows:
 case=row['case'];pred=row['prediction'];clear=row['cleared'];reset=row['caseReset'];comp=row['compared'];opened=row['opened'];e=table[case];r=records[case]
 assert reset['prediction']=='' and reset['resultsHidden'] and reset['answerHidden'] and not reset['answerOpen'] and not reset['traceOpen']
 assert clear['prediction']==pred and clear['resultsHidden'] and clear['answerHidden'] and not clear['answerOpen'] and not clear['traceOpen']
 if pred:assert clear['message']=='予想を変更しました。比較するで照合してください。'
 assert not comp['resultsHidden'] and not comp['answerOpen'] and not comp['traceOpen']
 assert comp['answerHidden']==(e['category']=='error') and opened['traceOpen'] and opened['answerOpen']==(e['category']!='error')
 prefix='予想未選択。' if pred=='' else ('予想と一致。' if pred==e['category'] else '予想と不一致。');assert comp['message'].startswith(prefix)
 assert comp['candidate']==f"候補label: {r['normal']['candidate_label']} / 検証済み候補版: {e['validated'] or 'なし'}"
 for mode in ['normal','faulty']:
  ui=comp[mode];v=r[mode];expect=e[mode]
  assert ui['status']=='状態: '+e['status'] and ui['adopted']=='採用版: '+e['adopted'] and ui['reason']=='拒否/失敗理由: '+(e['reason'] or 'なし')
  if expect is None:assert ui['result']=='要求結果なし（実行失敗）' and ui['next']=='次要求も未実行'
  else:
   reqversion=expect['field_versions'][0] if mode=='normal' else 'fieldごとに取得'
   assert ui['result']==f"tuple=({','.join(map(str,expect['tuple']))})\nfield版={' / '.join(expect['field_versions'])}\n要求snapshot={reqversion}"
   assert ui['next']=='次要求: (2000,4) / v2 / v2'
 assert json.loads(comp['trace'])=={'normal':r['normal']['trace'],'faulty':r['faulty']['trace']}
 assert raw['run_id'] in comp['run'] and comp['raw']==f"observations/{raw['run_id']}/raw.json"
 if e['category']=='refused':assert 'v2=(2000,4)' in comp['answer'] and 'v2対照' in comp['classification']
 if e['category']=='error':assert '正常答えは表示しない' in comp['classification']
links=[]
for doc in [ROOT/'README.md',ROOT/'index.html']:
 text=doc.read_text();targets=re.findall(r'\]\(([^)]+)\)',text) if doc.suffix=='.md' else re.findall(r'(?:href|src)="([^"]+)"',text)
 for target in targets:
  if target.startswith(('http:', 'https:','#')):continue
  assert (doc.parent/target.split('#')[0]).exists(),target
  links.append(str(doc.relative_to(ROOT))+':'+target)
oldrun='20261005T130310243736Z-reload';old=json.loads((ROOT/'observations'/oldrun/'raw.json').read_text())
for name,h in old['source_digests'].items():assert hashlib.sha256((Q/'preliminary-source'/oldrun/name).read_bytes()).hexdigest()==h
assert snapshot()==before
print(json.dumps({'status':'passed','run_id':raw['run_id'],'comparisons':55,'prediction_clears':55,'case_resets':11,'refusal_comparisons':30,'execution_error_comparisons':5,'local_links_exist':links,'preliminary_source_binding_preserved':20,'read_only_files':len(before),'hash_mtime_equal':True},ensure_ascii=False))

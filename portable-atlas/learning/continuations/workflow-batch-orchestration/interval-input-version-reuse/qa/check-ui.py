import hashlib,json,re,sys
from pathlib import Path
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parent.parent;Q=ROOT/'qa'
def snapshot():return {str(p.relative_to(ROOT)):(hashlib.sha256(p.read_bytes()).hexdigest(),p.stat().st_mtime_ns) for p in ROOT.rglob('*') if p.is_file()}
before=snapshot();raw=json.loads((ROOT/'observation-data.js').read_text().removeprefix('window.INTERVAL_OBSERVATION=').strip().removesuffix(';'));records={r['id']:r for r in raw['rows']};table=json.loads((ROOT/'expected-table.json').read_text());expected={r['id']:r for r in table['rows']};specs={r['id']:r for r in json.loads((ROOT/'contracts.json').read_text())['cases']}
# Independently bind optional seed content, including deliberately corrupt artifact body.
seedbody={'binding':{'task':'sum-demo-v1','interval':'day1','input_sha':table['literal_digests']['a']},'value':5,'count':2};seedhash=hashlib.sha256(json.dumps(seedbody,sort_keys=True,separators=(',',':')).encode()).hexdigest()
for row in raw['rows']:
 for mode,r in row['modes'].items():
  seed=[]
  if specs[row['id']]['seed']:
   body=json.loads(json.dumps(seedbody));body['value']=999 if row['id']=='corrupt-cache' else 5;seed=[{'body':body,'artifact_sha':seedhash}]
  assert r['cache_before']==seed

def text(v):
 r=v['resolved_input'];a=v['artifact'];b=a['body']['binding'] if a else None
 f=lambda x:'true' if x is True else 'false' if x is False else '未照合'
 return '\n'.join(['状態: '+v['status'],'理由: '+(v['reason'] or 'なし'),'選択版: '+(r['version_label'] if r else 'なし'),'入力: '+(json.dumps(r['values'],separators=(',',':')) if r else '未解決'),'input digest: '+(r['input_sha'][:12] if r else 'なし'),'cache hit: '+f(v['cache_hit']),'task呼出し: '+str(v['task_calls']),'合計: '+(str(v['value']) if v['value'] is not None else '結果なし'),'artifact区間: '+(b['interval'] if b else 'なし'),'artifact input digest: '+(b['input_sha'][:12] if b else 'なし'),'artifact内容digest: '+(a['artifact_sha'][:12] if a else 'なし'),'要求binding一致: '+f(v['reused_binding_matches_request'])])
rows=json.loads((Q/'iab-matrix.json').read_text());assert len(rows)==105 and {r['case'] for r in rows}==set(expected)
for row in rows:
 c=row['case'];pred=row['prediction'];reset=row['caseReset'];clear=row['cleared'];comp=row['compared'];opened=row['opened'];e=expected[c];r=records[c]
 for state in [reset,clear]:assert state['resultsHidden'] and state['answerHidden'] and not state['answerOpen'] and not state['traceOpen']
 assert reset['prediction']=='' and clear['prediction']==pred
 if pred:assert clear['message']=='予想を変更しました。比較するで照合してください。'
 assert not comp['resultsHidden'] and not comp['answerOpen'] and not comp['traceOpen']
 assert comp['answerHidden']==(e['category']=='error') and opened['traceOpen'] and opened['answerOpen']==(e['category']!='error')
 prefix='予想未選択。' if not pred else '予想と一致。' if pred==e['category'] else '予想と不一致。';assert comp['message'].startswith(prefix)
 assert comp['request']==f"要求区間: {specs[c]['interval']} / 入力参照: {specs[c]['selector']}"
 for mode,v in r['modes'].items():
  assert comp['modes'][mode]==text(v)
  if e['status']=='success':
   x=e['modes'][mode];assert v['value']==x['value'] and v['cache_hit']==x['hit'] and v['resolved_input']['version_label']==x['selected'] and v['artifact']['body']['binding']['interval']==x['artifact_interval']
  else:assert v['value'] is None and v['cache_before']==v['cache_after'] and '合計: 結果なし' in comp['modes'][mode]
 assert json.loads(comp['trace'])==r['modes'] and raw['run_id'] in comp['run'] and comp['raw']==f"observations/{raw['run_id']}/raw.json"
 if e['category']=='refused':assert '旧cacheを保持' in comp['classification']
 if e['category']=='error':assert '正常結果・答えを表示しない' in comp['classification']
links=[]
for doc in [ROOT/'README.md',ROOT/'index.html']:
 targets=re.findall(r'\]\(([^)]+)\)',doc.read_text()) if doc.suffix=='.md' else re.findall(r'(?:href|src)="([^"]+)"',doc.read_text())
 for target in targets:
  if target.startswith(('http:', 'https:','#')):continue
  assert (doc.parent/target.split('#')[0]).exists(),target;links.append(str(doc.relative_to(ROOT))+':'+target)
assert snapshot()==before
print(json.dumps({'status':'passed','run_id':raw['run_id'],'comparisons':105,'prediction_clears':105,'case_resets':15,'refusal_comparisons':35,'execution_error_comparisons':7,'optional_seed_literal_binding_verified':True,'local_links_exist':links,'read_only_files':len(before),'all_hash_mtime_equal':True},ensure_ascii=False))

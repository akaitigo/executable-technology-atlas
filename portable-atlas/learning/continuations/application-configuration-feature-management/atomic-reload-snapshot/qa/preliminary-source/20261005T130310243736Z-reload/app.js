'use strict';
const $=id=>document.getElementById(id), data=window.RELOAD_OBSERVATION;
const labels={'before-reload':'要求完了後にv2採用','after-reload':'v2採用後に要求','between-reads':'2field読取の間にv2採用','before-commit':'commit直前 / 故障1field更新後に要求','bad-type':'拒否 · timeout文字列','bad-range':'拒否 · timeout範囲外','bad-bool':'拒否 · retries boolean','bad-version':'拒否 · version数値','bad-field':'拒否 · field欠損','bad-syntax':'拒否 · JSON構文','read-failure':'実行失敗 · 候補ファイルなし'};
for(const r of data.rows){const o=document.createElement('option');o.value=r.id;o.textContent=labels[r.id];$('scenario').appendChild(o);}
$('run').textContent=`保存run: ${data.run_id} / Python ${data.environment.python} / 4更新順序・6入力拒否・1読取失敗`;
$('raw').href=`observations/${data.run_id}/raw.json`;$('command').href=`observations/${data.run_id}/command.json`;
function clear(message){$('results').hidden=true;$('answer').hidden=true;$('answer').open=false;$('trace-disclosure').open=false;$('prediction-result').textContent=message;}
$('scenario').addEventListener('change',()=>{$('prediction').value='';clear('予想してから比較する。');});
$('prediction').addEventListener('change',()=>clear('予想を変更しました。比較するで照合してください。'));
function requestText(q){return q?`tuple=(${q.tuple.join(',')})\nfield版=${q.field_versions.join(' / ')}\n要求snapshot=${q.request_snapshot??'fieldごとに取得'}`:'要求結果なし（実行失敗）';}
$('compare').addEventListener('click',()=>{
 const r=data.rows.find(x=>x.id===$('scenario').value), status=r.normal.status;
 const mixed=r.faulty.request&&new Set(r.faulty.request.field_versions).size>1;
 const category=status==='execution-error'?'error':status==='expected-refusal'?'refused':mixed?'mixed':'consistent';
 $('prediction-result').textContent=$('prediction').value===''?'予想未選択。選んで結果と照合する。':$('prediction').value===category?'予想と一致。tuple・field版・採用版を照合しよう。':'予想と不一致。候補版と採用版、要求内の版を読み直そう。';
 $('candidate').textContent=`候補label: ${r.normal.candidate_label} / 検証済み候補版: ${r.normal.validated_candidate_version??'なし'}`;
 for(const mode of ['normal','faulty']){const v=r[mode];$(mode+'-status').textContent=`状態: ${v.status}`;$(mode+'-adopted').textContent=`採用版: ${v.adopted_version}`;$(mode+'-reason').textContent=`拒否/失敗理由: ${v.reason??'なし'}`;$(mode+'-result').textContent=requestText(v.request);$(mode+'-next').textContent=v.next_request?`次要求: (${v.next_request.tuple.join(',')}) / ${v.next_request.field_versions.join(' / ')}`:'次要求も未実行';}
 $('classification').textContent=category==='mixed'?'故障tupleはv1/v2どちらにも一致しない。':category==='refused'?'入力拒否。候補v3は採用せず、両版のv2対照を保持。':category==='error'?'実行失敗。入力拒否と分け、正常答えは表示しない。':'両版の要求tupleはそれぞれ同一版に一致する。';
 $('trace').textContent=JSON.stringify({normal:r.normal.trace,faulty:r.faulty.trace},null,2);$('results').hidden=false;$('answer').hidden=category==='error';$('answer').open=false;$('trace-disclosure').open=false;
 $('answer-text').textContent=category==='refused'?'不正候補を検証段階で拒否し、last-known-goodのv2=(2000,4)を両版で保持した。':category==='mixed'?'要求開始時の正常snapshotはv1を維持する。故障版は別々の時点のfieldを組み合わせるため、(1000,4)または(2000,2)となる。':'要求と更新の順序を固定すると、両版ともv1またはv2のtupleを読む。混在しなかった1順序だけではfield別更新の安全性を保証しない。';
});

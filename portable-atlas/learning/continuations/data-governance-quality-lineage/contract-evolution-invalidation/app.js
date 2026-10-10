'use strict';
const data=window.CONTRACT_OBSERVATION,$=id=>document.getElementById(id);
for(const r of data.rows){const o=document.createElement('option');o.value=r.id;o.textContent=r.status==='expected-refusal'?`拒否 · ${r.id.replace('refuse-','')}`:r.label;$('scenario').append(o);}
$('run').textContent=`保存run: ${data.run_id} / Python ${data.environment.python} / 4比較 + 5入力拒否`;$('raw').href=`observations/${data.run_id}/raw.json`;$('command').href=`observations/${data.run_id}/command.json`;
function clear(message){$('results').hidden=true;$('refusal').hidden=true;$('answer').open=false;$('trace-disclosure').open=false;$('prediction-result').textContent=message;}
$('scenario').addEventListener('change',()=>{$('prediction').value='';clear('予想してから比較する。');});$('prediction').addEventListener('change',()=>clear('予想を変更しました。比較するで照合してください。'));
$('compare').addEventListener('click',()=>{
 const r=data.rows.find(x=>x.id===$('scenario').value),refused=r.status==='expected-refusal';$('results').hidden=refused;$('refusal').hidden=!refused;
 const actual=refused?'refused':r.normal.cache_state==='reused'?'reused':r.normal.accepted?'accepted':'rejected',pred=$('prediction').value;
 $('prediction-result').textContent=!pred?'予想未選択。予想を選んで結果と照合する。':pred===actual?'予想と一致。失効と再評価を照合しよう。':'予想と不一致。binding・違反・合計を読み直そう。';
 if(refused){$('reason').textContent=`${r.stage} / ${r.reason}`;$('input').textContent=JSON.stringify({source_json:r.source_json,contract_json:r.contract_json},null,2);return;}
 $('normal').textContent=`正常: ${r.normal.cache_state} → ${r.normal.validation_state} / amount_sum=${r.normal.amount_sum}`;
 $('faulty').textContent=`source-only故障版: reused → cache-reused-accepted / amount_sum=${r.faulty.amount_sum}`;$('violations').textContent=JSON.stringify(r.normal.violations,null,2);
 $('meaning').textContent=`raw文字列同じ=${r.raw_contract_equal} / 正規化binding同じ=${r.normalized_contract_equal} / validation規則の意味同じ=${r.validation_semantics_equal}`;
 $('trace').textContent=JSON.stringify({current_contract:r.current_contract,binding:r.binding,raw_contract_sha256:r.raw_contract_sha256,normalized_contract_sha256:r.normalized_contract_sha256,normal:r.normal.trace,faulty:r.faulty.trace},null,2);
});

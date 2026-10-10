'use strict';
const data=window.CUSTODY_OBSERVATION,$=id=>document.getElementById(id),pretty=x=>JSON.stringify(x,null,2);let revision=0;
for(const r of data.rows){const o=document.createElement('option');o.value=r.id;o.textContent=r.label;$('scenario').append(o);}
$('input-json').value=data.rows[0].input_json;$('initial-run').textContent=data.run_id;$('initial-raw').href='observations/'+data.run_id+'/raw.json';
function clear(message){revision++;$('results').hidden=true;$('answer').hidden=true;$('answer').open=false;$('trace-disclosure').open=false;for(const id of ['classification','normal','faulty','bytes','hashes','ledger','trace','run','answer-body'])$(id).textContent='';$('raw').removeAttribute('href');$('prediction-result').textContent=message;}
$('scenario').addEventListener('change',()=>{$('input-json').value=data.rows.find(r=>r.id===$('scenario').value).input_json;$('prediction').value='';clear('入力例を変更しました。予想もresetしました。');});
$('input-json').addEventListener('input',()=>clear('合成JSONを変更しました。新しい入力で比較してください。'));
$('prediction').addEventListener('change',()=>clear('予想を変更しました。新しい予想で比較してください。'));
$('compare').addEventListener('click',async()=>{
 clear('所有tmp内で実byteコピーと台帳照合を実行中です。');const mine=revision,text=$('input-json').value,pred=$('prediction').value;
 try{
  const response=await fetch('/measure',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({input_json:text,revision:mine})});if(!response.ok)throw Error('HTTP '+response.status);const raw=await response.json();if(mine!==revision)return;
  if(raw.revision!==mine||raw.input_json!==text)throw Error('応答binding不一致');const r=raw.run.result;
  if(!['observed','input_refusal'].includes(r.status)||raw.run.exit!==(r.status==='input_refusal'?2:0))throw Error('実コピー/実行に失敗');
  const cat=r.status==='input_refusal'?'input':r.normal.decision==='ledger_refusal'?'ledger':r.integrity_match?'match':'mismatch';
  $('prediction-result').textContent=(!pred?'予想未選択。':pred===cat?'予想と一致。':'予想と不一致。')+' 観測: '+cat;$('results').hidden=false;
  $('classification').textContent=r.status==='input_refusal'?`入力契約拒否 ${r.code}、exit${raw.run.exit}。コピー・台帳判定・正常答えなし。`:`integrity ${r.integrity_match?'match':'mismatch'} / 台帳 ${r.ledger_consistent?'整合':'整合拒否'} / 正常 ${r.normal.decision} / 故障 ${r.faulty.decision}。`;
  $('normal').textContent=r.normal?pretty(r.normal):'判定なし';$('faulty').textContent=r.faulty?pretty(r.faulty):'判定なし';$('bytes').textContent=r.status==='observed'?pretty({original:r.original_ascii,copy_before:r.copy_before_ascii,copy_after:r.copy_after_ascii,changed_bytes:r.changed_bytes,original_unchanged:r.original_unchanged,temporary_cleanup:r.temporary_cleanup}):'ファイル未作成';$('hashes').textContent=r.status==='observed'?pretty({original:r.original_sha256,copy_before:r.copy_before_sha256,copy_after:r.copy_after_sha256}):'hashなし';$('ledger').textContent=r.status==='observed'?pretty({errors:r.ledger_errors,trace:r.ledger_trace}):'台帳判定なし';$('trace').textContent=pretty(raw.run);$('run').textContent=`request ${raw.request_id} · Python実コピー · exit${raw.run.exit}`;$('raw').setAttribute('href',raw.raw_href);
  if(r.status==='observed'){$('answer').hidden=false;$('answer-body').textContent=`実evidenceID=${r.evidenceID}、原本=${JSON.stringify(r.original_ascii)}、複製後=${JSON.stringify(r.copy_after_ascii)}。原本SHA256=${r.original_sha256}、複製後SHA256=${r.copy_after_sha256}。変更byte=${r.changed_bytes}、原本保持=${r.original_unchanged}、tmp cleanup=${r.temporary_cleanup}。hash比較は${r.integrity_match?'integrity-match':'mismatch'}、台帳errors=${JSON.stringify(r.ledger_errors)}。正常判定=${r.normal.decision}、故障判定=${r.faulty.decision}（${r.faulty.claim}）。hash一致や合成台帳の整合は、出所・真正性・本人認証・法的chain of custodyの証明ではありません。`;}
 }catch(error){if(mine!==revision)return;clear('実行/通信失敗。正常答えは生成していません。 '+error.message);}
});

'use strict';
const data=window.CHAIN_OBSERVATION,$=id=>document.getElementById(id),pretty=x=>JSON.stringify(x,null,2);let revision=0;
for(const r of data.rows){const o=document.createElement('option');o.value=r.id;o.textContent=r.label;$('scenario').append(o);}
$('input-json').value=data.rows[0].input_json;$('initial-run').textContent=data.run_id;$('initial-raw').href='observations/'+data.run_id+'/raw.json';
function clear(message){revision++;$('results').hidden=true;$('answer').hidden=true;$('answer').open=false;$('trace-disclosure').open=false;for(const id of ['classification','normal','faulty','packet','trace','run','answer-body'])$(id).textContent='';$('raw').removeAttribute('href');$('prediction-result').textContent=message;}
$('scenario').addEventListener('change',()=>{$('input-json').value=data.rows.find(r=>r.id===$('scenario').value).input_json;$('prediction').value='';clear('入力例を変更しました。予想もresetしました。');});
$('input-json').addEventListener('input',()=>clear('JSONを変更しました。新しい入力で比較してください。'));
$('prediction').addEventListener('change',()=>clear('予想を変更しました。新しい予想で比較してください。'));
$('compare').addEventListener('click',async()=>{
 clear('Pythonで合成packetを実計算中です。');const mine=revision,text=$('input-json').value,pred=$('prediction').value;
 try{
  const response=await fetch('/measure',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({input_json:text,revision:mine})});if(!response.ok)throw Error('HTTP '+response.status);const raw=await response.json();if(mine!==revision)return;
  if(raw.revision!==mine||raw.input_json!==text)throw Error('応答binding不一致');const r=raw.run.result;
  if(!['observed','input_refusal'].includes(r.status)||raw.run.exit!==(r.status==='input_refusal'?2:0))throw Error('実計算に失敗');
  const cat=r.status==='input_refusal'?'input':r.normal.final!==r.faulty.final?'mismatch':r.normal.final==='accept'?'accept':'drop';
  $('prediction-result').textContent=(!pred?'予想未選択。':pred===cat?'予想と一致。':'予想と不一致。')+' 観測: '+cat;$('results').hidden=false;
  $('classification').textContent=r.status==='input_refusal'?`subset拒否 ${r.code}、exit${raw.run.exit}。packet判定・正常答えなし。`:`正常 ${r.normal.final} / 故障 ${r.faulty.final}。`;
  $('normal').textContent=r.normal?pretty(r.normal):'判定なし';$('faulty').textContent=r.faulty?pretty(r.faulty):'判定なし';$('packet').textContent=r.packet?pretty(r.packet):'有効なpacketなし';$('trace').textContent=pretty(raw.run);$('run').textContent=`request ${raw.request_id} · Python合成模型 · exit${raw.run.exit}`;$('raw').setAttribute('href',raw.raw_href);
  if(r.status==='observed'){
   $('answer').hidden=false;const service=r.normal.trace.some(e=>e==='chain service priority=10'),skipped=r.normal.trace.includes('skip service disabled');
   $('answer-body').textContent=`この実入力は ${r.packet.source} ${r.packet.protocol}/${r.packet.dport}。priority順は ${r.ordered_chains.join(' → ')}。正常版はservice chain${service?'訪問':skipped?'無効のためskip':'未訪問'}、最終${r.normal.final}。故障版は最終${r.faulty.final}。正常trace: ${r.normal.trace.join(' / ')}。故障trace: ${r.faulty.trace.join(' / ')}。同じhookの有限模型であり、実packetの配送・firewall安全性は未検証です。`;
  }
 }catch(error){if(mine!==revision)return;clear('実行/通信失敗。正常答えは生成していません。 '+error.message);}
});

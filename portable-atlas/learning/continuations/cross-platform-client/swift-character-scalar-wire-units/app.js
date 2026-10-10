'use strict';
const data=window.SWIFT_OBSERVATION,$=id=>document.getElementById(id),pretty=x=>JSON.stringify(x,null,2);let revision=0,pending=false;
for(const r of data.rows){const o=document.createElement('option');o.value=r.id;o.textContent=r.label;$('scenario').append(o);}$('input-json').value=data.rows[0].input_json;
function clear(message){revision++;$('results').hidden=true;$('answer').hidden=true;$('answer').open=false;$('trace-disclosure').open=false;for(const id of ['classification','normal','faulty','counts','wire','trace','run','answer-body'])$(id).textContent='';$('raw').removeAttribute('href');$('prediction-result').textContent=message;}
$('scenario').addEventListener('change',()=>{$('input-json').value=data.rows.find(r=>r.id===$('scenario').value).input_json;$('prediction').value='';clear('入力例を変更しました。予想をresetしました。');});
$('input-json').addEventListener('input',()=>clear('JSON入力を変更しました。比較するで実行してください。'));
$('prediction').addEventListener('change',()=>clear('予想を変更しました。比較するで実行してください。'));
$('compare').addEventListener('click',async()=>{
 clear('実SwiftでJSON往復を実行中です。');const mine=revision,text=$('input-json').value,pred=$('prediction').value;
 try{
  const response=await fetch('/measure',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({input_json:text,revision:mine})});if(!response.ok)throw Error('HTTP '+response.status);const raw=await response.json();if(mine!==revision)return;
  if(raw.revision!==mine||raw.input_json!==text)throw Error('応答binding不一致');const r=raw.run.result;
  if(r.status==='execution_error')throw Error('Swift実行失敗');
  const cat=r.status==='input_refusal'?'input':r.normal.accepted!==r.faulty.accepted?'mismatch':r.normal.accepted?'accepted':'refused';
  $('prediction-result').textContent=(!pred?'予想未選択。':pred===cat?'予想と一致。':'予想と不一致。')+' 観測: '+cat;$('results').hidden=false;
  $('classification').textContent=r.status==='input_refusal'?`decode拒否 ${r.exception_class}、exit${raw.run.exit}。測定値・正常答えなし。`:`実Swift観測。正常${r.normal.accepted?'受入':'拒否'} / 故障${r.faulty.accepted?'受入':'拒否'}。`;
  $('normal').textContent=pretty(r.normal);$('faulty').textContent=pretty(r.faulty);$('counts').textContent=r.decoded?pretty({character:r.decoded.character,scalar:r.decoded.scalar,utf16:r.decoded.utf16,utf8:r.decoded.utf8}):'測定なし';$('wire').textContent=r.decoded?`scalar配列保持 ${r.scalar_sequence_preserved} / UTF8保持 ${r.utf8_preserved}`:'JSON stringをdecodeできません。';$('trace').textContent=pretty(raw.run);$('run').textContent=`request ${raw.request_id} · Swift CLI · exit${raw.run.exit}`;$('raw').setAttribute('href',raw.raw_href);
  if(r.status==='observed'){$('answer').hidden=false;const n=r.normal,f=r.faulty,c=r.decoded;$('answer-body').textContent=`この実入力はCharacter=${c.character}、scalar=${c.scalar}、UTF16=${c.utf16}、UTF8=${c.utf8}。正常scalar gate=${n.scalar_ok}、byte gate=${n.byte_ok}で${n.accepted?'受入':'拒否'}。Characterへ置換したscalar gate=${f.scalar_ok}で故障は${f.accepted?'受入':'拒否'}。再decode後もscalar配列保持=${r.scalar_sequence_preserved}、UTF8保持=${r.utf8_preserved}。文字列payloadの単位でありJSON全体のbyteではありません。`;}
 }catch(error){if(mine!==revision)return;clear('実行/通信失敗。正常答えは生成していません。 '+error.message);}
});

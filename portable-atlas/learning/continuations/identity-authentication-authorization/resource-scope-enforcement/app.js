'use strict';
const data=window.SCOPE_OBSERVATION,$=id=>document.getElementById(id);
for(const r of data.rows){const o=document.createElement('option');o.value=r.id;o.textContent=r.status==='expected-refusal'?`拒否 · ${r.id.replace('refuse-','')}`:`${r.request.subject} · ${r.request.scope}→${r.request.resource.replace('doc-','')} · ${r.request.action}`;$('scenario').append(o);}
$('run').textContent=`保存run: ${data.run_id} / Python ${data.environment.python} / 24全組合せ + 6入力拒否 / 実読取 正常2・故障4`;
$('raw').href=`observations/${data.run_id}/raw.json`;$('command').href=`observations/${data.run_id}/command.json`;
function clear(message){$('results').hidden=true;$('refusal').hidden=true;$('answer').open=false;$('trace-disclosure').open=false;$('prediction-result').textContent=message;}
$('scenario').addEventListener('change',()=>{$('prediction').value='';clear('予想してから比較する。');});
$('prediction').addEventListener('change',()=>clear('予想を変更しました。比較するで照合してください。'));
$('compare').addEventListener('click',()=>{
 const r=data.rows.find(x=>x.id===$('scenario').value),refused=r.status==='expected-refusal';$('results').hidden=refused;$('refusal').hidden=!refused;
 const actual=refused?'refused':r.normal.decision==='allow'?'both-read':r.faulty.decision==='allow'?'boundary':'both-deny',pred=$('prediction').value;
 $('prediction-result').textContent=!pred?'予想未選択。予想を選んで結果と照合する。':pred===actual?'予想と一致。decisionと実読取を照合しよう。':'予想と不一致。resource属性・権限・読取回数を読み直そう。';
 if(refused){$('reason').textContent=`${r.normal.reason} / 両版read_count=0`;$('refused-input').textContent=JSON.stringify(r.request,null,2);}
 else{$('request').textContent=`主体 ${r.request.subject} / 申告scope ${r.request.scope} / 対象 ${r.request.resource} / 操作 ${r.request.action}`;for(const mode of ['normal','faulty']){$(mode+'-result').textContent=`${r[mode].decision} / ${r[mode].reason} / read_count=${r[mode].read_count}`;$(mode+'-content').textContent=r[mode].content_ascii===null?'content=null（読取なし）':`実読取bytes: ${r[mode].content_ascii}\nhex: ${r[mode].content_hex}\nSHA256: ${r[mode].content_sha256}`;}$('trace').textContent=JSON.stringify({normal:r.normal.trace,faulty:r.faulty.trace},null,2);}
});

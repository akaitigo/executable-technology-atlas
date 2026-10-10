'use strict';
const data=window.STORE_OBSERVATION,$=id=>document.getElementById(id),pretty=x=>JSON.stringify(x,null,2);
const names={'stale-diverges':'失効漏れだけAが違う','same-halt':'全実装が同じAでHALT',illegal:'fetch / 失効ありはillegal',input:'入力を拒否（traceなし）',budget:'HALT前にstep budget終了'};
for(const r of data.rows){const o=document.createElement('option');o.value=r.id;o.textContent=r.label;$('scenario').append(o);}
function clear(message){$('results').hidden=true;$('answer').hidden=true;$('answer').open=false;$('trace-disclosure').open=false;for(const id of ['fetch','invalidate','stale','ranges','memory','trace','run','classification','answer-body'])$(id).textContent='';for(const id of ['raw','command'])$(id).removeAttribute('href');$('prediction-result').textContent=message;}
$('scenario').addEventListener('change',()=>{$('prediction').value='';clear('ケースを変更しました。予想して比較してください。');});
$('prediction').addEventListener('change',()=>clear('予想を変更しました。比較するで照合してください。'));
function category(r){const {fetch:f,stale:s}=r.variants;return f.status==='input'?'input':f.status==='illegal'?'illegal':f.status==='budget'?'budget':f.a!==s.a?'stale-diverges':'same-halt';}
$('compare').addEventListener('click',()=>{
 const r=data.rows.find(x=>x.id===$('scenario').value),cat=category(r),pred=$('prediction').value;
 clear((!pred?'予想未選択。':pred===cat?'予想と一致。':'予想と不一致。')+' 観測: '+names[cat]);$('results').hidden=false;
 $('classification').textContent=names[cat]+'。statusはguestの結果です。';
 for(const m of ['fetch','invalidate','stale']){const v=r.variants[m];$(m).textContent=pretty({status:v.status,pc:v.pc,a:v.a,steps:v.steps,diagnostic:v.diagnostic});}
 $('ranges').textContent=pretty({prewarm:r.prewarm,invalidating:r.variants.invalidate.store_events,stale:r.variants.stale.store_events,predecoded:r.variants.invalidate.decoded_blocks.filter((b,i)=>i<r.prewarm.length).map(b=>({start:b.start,addresses:b.addresses,instructions:b.instructions}))});
 const writes=r.variants.fetch.trace.flatMap(t=>t[6]);$('memory').textContent=r.variants.fetch.memory===null?'入力拒否: memoryを生成せず、traceなし。':'実STORE差分 [address, old, new]: '+JSON.stringify(writes)+'。全実装の最終memoryは一致。';
 $('trace').textContent=pretty(Object.fromEntries(['fetch','invalidate','stale'].map(m=>[m,{trace:r.variants[m].trace,cache_events:r.variants[m].cache_events,decoded_blocks:r.variants[m].decoded_blocks}])));
 $('run').textContent='run '+data.run_id+' · Python '+data.environment.python+' · '+data.environment.os+' '+data.environment.machine+' · stdlib';$('raw').setAttribute('href','observations/'+data.run_id+'/raw.json');$('command').setAttribute('href','observations/'+data.run_id+'/command.json');
 $('answer').hidden=false;
 const reasons={'stale-diverges':'STOREが事前decode済みoperandの依存addressへ重なりました。memoryは7でも古いoperand1を使うとA1。fetchと失効ありはA7。','same-halt':'書込みaddressはcode依存範囲の外。blockを保持して全実装A1でHALT。','illegal':'opcode byteの変更は命令そのものを変えます。fetchと失効ありはillegalを診断し、未commit命令はtraceへ追加しません。事前HALTを残した失効漏れはHALTします（初手illegalケースは全実装illegal）。','input':'boolはinteger byteとして受け入れません。guest命令は未実行、memoryなし・traceなし。','budget':'4stepのJZで予算終了。次のLOAD/HALTを実行していません。失効は行われていますが、このrunから最終A7は主張しません。'};
 $('answer-body').textContent=reasons[cat]+' 書込み先だけでなくopcode/operandを含む全block addressが失効判定の対象です。native JITやVM隔離の証明ではありません。';
});

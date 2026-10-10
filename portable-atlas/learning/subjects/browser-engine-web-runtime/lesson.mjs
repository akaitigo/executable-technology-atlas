import {compare} from './oracle.mjs';
const $=id=>document.getElementById(id),runs=[],actions=[];let frame=null,serial=0,sourceHashes=null;
function raw(){ $('raw').textContent=JSON.stringify({kind:'actual-browser-event-loop-ui',at:new Date().toISOString(),environment:{userAgent:navigator.userAgent,language:navigator.language,width:innerWidth,height:innerHeight},sourceHashes,runs,actions,feedback:$('feedback').textContent},null,2);}
const manifest=await fetch('sources.json').then(r=>r.json());sourceHashes=manifest.sourceHashes;raw();
$('predict').onclick=()=>{const value=$('prediction').value;actions.push({type:'prediction',value,at:new Date().toISOString()});$('prediction-status').textContent='予想を保存: '+value;raw();};
$('run').onclick=()=>{
 const caseId=$('case').value;serial++;const runId=String(serial);$('run').disabled=true;$('result').textContent='専用Documentで実行中';
 actions.push({type:'run-requested',caseId,runId,at:new Date().toISOString()});frame=document.createElement('iframe');frame.id='case-frame';frame.title='event loop '+caseId+' run '+runId;frame.src='case.html?case='+caseId+'&run='+runId;$('frame-host').replaceChildren(frame);raw();
};
addEventListener('message',event=>{
 if(event.origin!==location.origin||event.source!==frame?.contentWindow||event.data?.type!=='event-loop-result')return;
 const observation=event.data.raw,comparison=compare(observation.input.caseId,observation.trace);runs.push({receivedAt:new Date().toISOString(),observation,comparison});
 $('result').textContent=(comparison.passed?'期待順と一致':'期待順と不一致')+' / run '+observation.input.runId;
 $('expected').textContent=comparison.expected.join(' → ');$('actual').textContent=comparison.actual.join(' → ');$('wrong').textContent=comparison.wrongModel.join(' → ');
 $('model-diff').textContent='誤モデルの最初の不一致: '+(comparison.firstWrongIndex+1)+'番目 / 誤モデル一致 '+comparison.wrongModelMatches;
 $('run').disabled=false;raw();
});
$('check-answer').onclick=()=>{const value=$('answer').value;const messages={checkpoint:'適切。checkpointは追加microtaskも空になるまで処理する。このfixtureのtimerへ進む前に完了する。',precision:'不適切。delay 0は即時実行や正確な0msを保証しない。',fifo:'不適切。taskとmicrotaskを一つのFIFOへ混ぜるモデルではこの順序を説明できない。'};$('feedback').textContent=messages[value]||'候補を選んでください。';actions.push({type:'answer',value,at:new Date().toISOString()});raw();};

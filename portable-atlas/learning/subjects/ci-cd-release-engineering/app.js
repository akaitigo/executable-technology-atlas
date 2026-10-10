'use strict';
const $ = id => document.getElementById(id);
let report = null;
const labels = {build:'Build',test:'Test',candidate:'Candidate',promotion:'Promotion',rollback:'Rollback'};
function cell(row,value){ const c=document.createElement('td'); c.textContent=String(value??'—');row.append(c); }
function renderEvent(){
  if(!report)return;
  const events=report.result.events, index=Number($('step').value), e=events[index];
  $('position').textContent=`${index} / ${events.length-1}`;
  $('event').textContent=`event ${e.seq}: ${e.stage} / ${e.status} — ${e.reason}`;
  $('pipeline').replaceChildren();
  for(const [key,label] of Object.entries(labels)){
    const node=document.createElement('div'), last=events.slice(0,index+1).filter(x=>x.stage===key).at(-1);
    node.className='node'+(last?(last.status==='refused'||last.status==='failed'?' bad':' good'):'')+(e.stage===key?' current':'');
    node.textContent=label;const status=document.createElement('span');status.textContent=last?last.status:'未到達';node.append(status);$('pipeline').append(node);
  }
  $('working').textContent=e.working_digest; $('tested').textContent=e.test?.artifact_digest??'未test';
  $('candidate').textContent=e.candidate?.artifact_digest??'candidateなし';$('active').textContent=e.active??'activeなし';$('previous').textContent=e.previous??'historyなし';
  $('guards').textContent='このeventのguards: '+JSON.stringify(e.guards);
  $('objects').replaceChildren();
  for(const [digest,data] of Object.entries(e.objects)){const row=document.createElement('tr');cell(row,digest);cell(row,data.bytes);cell(row,data.hex.slice(0,48)+'…');$('objects').append(row);}
}
function render(data){
  report=data.payload; $('result').hidden=false; $('comparison').hidden=false;
  const run=report.execution,s=report.result.summary;
  $('binding').textContent=`このrun: ${report.input.case} / rollback=${report.input.rollback} / Python ${run.python} / ${run.observed_at} / source ${run.source_digest.slice(0,16)}… / 合成local state`;
  $('step').max=String(report.result.events.length-1);$('step').value=$('step').max;
  const predicted=$('prediction').value, matches=predicted==='unknown'?'予想未選択':((predicted==='yes')===s.promoted?'予想と一致':'予想と異なります');
  $('answer').textContent=`最終runの答え: test=${s.test_passed} / candidate=${s.candidate_accepted} / promoted=${s.promoted} / rollback=${s.rollback_status} / 旧bytes不変=${s.history_present_initially?s.previous_bytes_unchanged:'対象なし（初回）'}。${matches}。これは全runの答えで、上の選択eventと区別します。`;
  const o=report.oracle; $('oracle').textContent=`独立Oracle: transition=${o.transition_matches} / state=${o.state_matches} / bytes hash=${o.hashes_match} / guards=${o.guards_match} / summary=${o.summary_matches}。`;
  $('events').textContent=JSON.stringify(report.result.events,null,2);
  $('raw').href=data.raw;$('metadata').href=data.metadata;
  $('matrix').replaceChildren();
  for(const run of report.comparisons){const row=document.createElement('tr'), s=run.result.summary;for(const v of [run.input.case,s.test_passed,s.candidate_accepted,s.promoted,s.rollback_status,s.history_present_initially?s.previous_bytes_unchanged:'対象なし',run.oracle.all_match])cell(row,v);$('matrix').append(row);}
  renderEvent();
}
$('run').addEventListener('click',async()=>{
  $('run').disabled=true;$('status').textContent='Pythonで新規計算中…';
  try{const r=await fetch('/api/run',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({case:$('case').value,rollback:$('rollback').checked})});const data=await r.json();if(!r.ok)throw new Error(data.error);render(data);$('status').textContent='計算・原票追記完了。旧原票は置換していません。';}
  catch(error){$('status').textContent='拒否／失敗: '+error.message+'。直前の表示／原票は保持します。';}
  finally{$('run').disabled=false;}
});
for(const id of ['case','rollback','prediction'])$(id).addEventListener('change',()=>{$('status').textContent='条件／予想を変更。再計算前なので結果は直前runのものです。';});
$('step').addEventListener('input',renderEvent);
$('first').addEventListener('click',()=>{$('step').value='0';renderEvent();});
$('last').addEventListener('click',()=>{$('step').value=$('step').max;renderEvent();});
$('decision').addEventListener('click',()=>{const index=report.result.events.findIndex(e=>e.stage==='promotion'||e.status==='refused');$('step').value=String(index<0?report.result.events.length-1:index);renderEvent();});

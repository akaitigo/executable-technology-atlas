'use strict';
const $ = id => document.getElementById(id);
const ns = 'http://www.w3.org/2000/svg';
let current = null;
function element(tag, attrs={}, text='') { const item=document.createElementNS(ns,tag); Object.entries(attrs).forEach(([key,value])=>item.setAttribute(key,String(value))); if(text)item.textContent=text; return item; }
function draw(event) {
  const svg=$('timeline'); svg.replaceChildren();
  const result=current.result, h=result.plan.horizon;
  const x=t=>85+t*940/h;
  ['CPU','task A','task B','flag'].forEach((name,i)=>svg.append(element('text',{x:10,y:55+i*55},name)));
  for(let t=0;t<=h;t++){svg.append(element('line',{x1:x(t),x2:x(t),y1:30,y2:230,class:'axis',opacity:'.35'})); if(h<=12||t%2===0)svg.append(element('text',{x:x(t),y:18,'text-anchor':'middle'},String(t)));}
  result.segments.forEach(segment=>{
    const color=segment.job===null?'#dde6ea':segment.job[0]==='A'?'#92c5e6':'#a5d5bc';
    const block=element('rect',{x:x(segment.start),y:34,width:(segment.end-segment.start)*940/h,height:30,fill:color,stroke:'white'});
    block.append(element('title',{},`${segment.start}..${segment.end}: ${segment.job||'idle'}`)); svg.append(block);
    if(segment.end-segment.start>=h/24)svg.append(element('text',{x:(x(segment.start)+x(segment.end))/2,y:54,'text-anchor':'middle'},segment.job||'idle'));
  });
  Object.values(result.jobs).forEach(job=>{
    const y=job.task==='A'?102:157;
    svg.append(element('path',{d:`M${x(job.release)-5} ${y+7} L${x(job.release)+5} ${y+7} L${x(job.release)} ${y-4} Z`,fill:'#486f86'}));
    svg.append(element('text',{x:x(job.release)+7,y:y+18},job.id));
    if(job.deadline<=h){const mark=element('line',{x1:x(job.deadline),x2:x(job.deadline),y1:y-15,y2:y+12,class:job.missed?'deadline missed':'deadline'}); mark.append(element('title',{},`${job.id} deadline=${job.deadline} miss=${job.missed}`)); svg.append(mark);}
    if(job.finish!==null){const marker=element('circle',{cx:x(job.finish),cy:y-3,r:5,fill:'white',stroke:job.missed?'#c04449':'#287357','stroke-width':2});marker.append(element('title',{},`${job.id} finish=${job.finish} lateness=${job.lateness}`));svg.append(marker);}
  });
  if(result.summary.safe_since!==null)svg.append(element('rect',{x:x(result.summary.safe_since),y:197,width:(h-result.summary.safe_since)*940/h,height:28,fill:'#ffdea0'}));
  svg.append(element('text',{x:90,y:216},result.summary.safe_state?'model flag: latched（実機停止なし）':'model flag: not triggered'));
  svg.append(element('line',{x1:x(event.time),x2:x(event.time),y1:25,y2:236,class:'cursor'}));
  svg.append(element('text',{x:85,y:263},`全${h} tickの計算結果。黒線はevent ${event.seq} / t=${event.time}`));
}
function render() {
  if(!current)return;
  const index=Number($('step').value), event=current.result.events[index], summary=current.result.summary;
  $('position').textContent=`${index} / ${current.result.events.length-1}`;
  $('event').textContent=`event ${index} / t=${event.time}: ${event.action}${event.job?' / '+event.job:''}${event.lateness!==undefined?' / lateness '+event.lateness:''}`;
  $('flag').textContent=`表示eventのsafe-state flag: ${event.safe_state?'latched':'false'}${event.safe_since!==null?' / t='+event.safe_since+'から':''}。表示用のmodel flagだけで、CPU計算は停止しません。`;
  $('flag').className='flag'+(event.safe_state?' latched':'');
  const prediction=$('prediction').value, actual=summary.misses===0?'no-miss':'miss';
  const feedback=prediction==='unsure'?'予想は未選択。':prediction===actual?'予想と結果は一致。':'予想と結果は異なります。';
  $('answer').textContent=`全horizonの答え: U=${summary.utilization_fraction}、miss=${summary.misses}、未完了=${summary.unfinished}、flag開始=${summary.safe_since===null?'なし':summary.safe_since}、max完了tardiness=${summary.max_completed_tardiness}。${feedback} 途中eventと最終結果を区別します。`;
  $('jobs').replaceChildren();
  Object.values(event.jobs).sort((a,b)=>a.release-b.release||a.task.localeCompare(b.task)).forEach(job=>{
    const tr=document.createElement('tr'); [job.id,job.release,job.deadline,job.finish,job.remaining,job.lateness,job.deadline_checked?(job.missed?'yes':'no'):'未検査'].forEach(value=>{const td=document.createElement('td'); td.textContent=value===null?'—':String(value);tr.append(td);}); $('jobs').append(tr);
  });
  draw(event);
}
async function execute(){
  $('run').disabled=true; $('status').textContent='Pythonで計算しています…';
  try{
    const response=await fetch('/api/run',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({case:$('case').value,horizon:Number($('horizon').value)})});
    const data=await response.json(); if(!response.ok)throw new Error(data.error);
    current=data.payload; $('result').hidden=false; $('comparison').hidden=false;
    $('step').max=String(current.result.events.length-1); $('step').value=$('step').max;
    $('binding').textContent=`このrun: ${current.input.case} / horizon ${current.input.horizon} / Python ${current.execution.python} / ${current.execution.observed_at} / source ${current.execution.source_digest.slice(0,16)}… / abstract ticks`;
    $('raw').href=data.raw_path; $('metadata').href=data.metadata_path;
    $('raw-events').textContent=JSON.stringify(current.result.events,null,2);
    const oracle=current.oracle;
    $('oracle').textContent=`独立1-tick Oracle: CPU timeline=${oracle.timeline_matches}、job release/deadline/finish/lateness=${oracle.jobs_match}、flag=${oracle.safe_flag_matches}。small search（先頭${oracle.small_feasibility.horizon} tickにdueのjobsのみ）の実行可能な順の存在=${oracle.small_feasibility.feasible_schedule_exists}。`;
    $('matrix').replaceChildren(); current.comparison.forEach(report=>{const s=report.result.summary,tr=document.createElement('tr');[report.input.case,s.utilization_fraction,s.misses,s.unfinished,s.safe_since===null?'なし':s.safe_since,s.max_completed_tardiness,report.oracle.all_match].forEach(value=>{const td=document.createElement('td');td.textContent=String(value);tr.append(td);});$('matrix').append(tr);});
    $('status').textContent='計算と原票追記が完了。旧原票は置換していません。';render();
  }catch(error){$('status').textContent=`今回の操作は拒否／失敗: ${error.message}。旧結果・原票は保持。`;}
  finally{$('run').disabled=false;}
}
$('run').addEventListener('click',execute); $('step').addEventListener('input',render);
$('first').addEventListener('click',()=>{$('step').value='0';render();});
$('last').addEventListener('click',()=>{$('step').value=$('step').max;render();});
$('miss').addEventListener('click',()=>{const i=current.result.events.findIndex(e=>e.action==='safe-state-latched');$('step').value=String(i<0?0:i);render();});
$('prediction').addEventListener('change',render);
['case','horizon'].forEach(id=>$(id).addEventListener('change',()=>{$('status').textContent='入力が変わりました。表示中の結果は前のrun。計算して更新してください。';}));

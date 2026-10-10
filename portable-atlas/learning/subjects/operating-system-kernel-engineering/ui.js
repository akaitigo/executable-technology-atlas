'use strict';
const $=id=>document.getElementById(id);
const expected={close:{timeout:false,eof:true,exit:0,writers:0},'leak-release':{timeout:true,eof:true,exit:0,writers:1},'leak-signal':{timeout:true,eof:false,exit:-15,writers:1}};
let cases=[],index=0,visible=0;
function render(){
 const c=cases[index],r=c.result;$('raw').textContent=JSON.stringify(c,null,2);$('events').replaceChildren();$('fd').replaceChildren();$('identity').replaceChildren();
 if(r.status==='rejected'){$('status').textContent='入力拒否: '+r.error;$('expected').textContent='childは起動していません。';$('result').textContent='結果なし。empty payloadの正常EOFとは区別。';$('next').disabled=true;$('all').disabled=true;return;}
 const es=r.timeline,ex=expected[r.input.mode];$('status').textContent=`${c.id}: ${visible} / ${es.length} event表示（保存実観測）`;
 $('next').disabled=visible>=es.length;$('all').disabled=visible>=es.length;
 for(let [name,pid] of [['parent',r.parent_pid],['child',r.child_pid]]){let span=document.createElement('span');span.className='pill';span.textContent=`${name} PID=${pid}`;$('identity').append(span);}
 $('expected').textContent=`独立table期待: checkpoint writers=${ex.writers} / bounded timeout=${ex.timeout} / EOF=${ex.eof} / exit=${ex.exit}`;
 const observedEof=r.child_events.some(e=>e.event==='eof');
 $('result').textContent=visible===es.length?`実結果: timeout=${r.bounded_timeout} / EOF=${observedEof} / exit=${r.returncode} / child reaped=${r.cleanup.child_reaped} / owned parent FD残=${r.cleanup.parent_open_fds}`:'実結果は全event後に表示。';
 let writes=0,dup=false,read=false,childAlive=false,original=false;
 const origin={parent:r.parent_events[0]?.mono_ns,child:r.child_events[0]?.mono_ns};
 for(let e of es.slice(0,visible)){
  if(e.actor==='parent'){
   if(e.event==='pipe_created'){writes=1;original=true;}
   if(e.event==='write_duplicated'){writes++;dup=true;}
   if(e.event==='child_spawned'){read=true;childAlive=true;}
   if(e.event==='original_write_closed'){writes--;original=false;}
   if(e.event==='leak_write_closed'){writes--;dup=false;}
   if(e.event==='child_reaped'||e.event==='wait_completed'||e.event==='cleanup_complete'){childAlive=false;read=false;}
  }
  if(e.actor==='child'&&e.event==='read_end_closed')read=false;
  const tr=document.createElement('tr'); const fields=Object.fromEntries(Object.entries(e).filter(([k])=>!['actor','event','seq','pid','mono_ns','wall_ns'].includes(k)));
  const vals=[`${e.actor} / ${e.pid}`,e.event,new Date(e.wall_ns/1e6).toISOString(),((e.mono_ns-origin[e.actor])/1e6).toFixed(3),JSON.stringify(fields)];
  vals.forEach((v,j)=>{let td=document.createElement('td');td.textContent=v;if(j===1&&e.event==='bounded_timeout')td.className='bad';tr.append(td);});$('events').append(tr);
 }
 // Conceptual ownership graph reconstructed only from known FD open/close events.
 const f=r.fds,writeColor=writes?'#b34b2e':'#117b63';
 $('fd').innerHTML=`<svg viewBox="0 0 1000 215" role="img" aria-label="data pipe FD参照図"><rect x="5" y="15" width="300" height="185" rx="12" fill="#eef3f5"/><text x="25" y="45" font-size="18">parent PID ${r.parent_pid}</text><text x="25" y="80" font-size="16">write FD ${f.parent_write}: ${original?'open':'closed / 未作成'}</text><text x="25" y="112" font-size="16">dup FD ${f.parent_duplicate_write??'なし'}: ${dup?'open':'closed / なし'}</text><text x="25" y="155" font-size="18" fill="${writeColor}">writer参照 ${writes}</text><path d="M310 100H395" stroke="${writeColor}" stroke-width="4"/><rect x="400" y="55" width="190" height="90" rx="10" fill="#ddeee7"/><text x="415" y="90" font-size="17">data pipe buffer</text><text x="415" y="118" font-size="14">全writer close → EOF</text><path d="M595 100H680" stroke="#287ba0" stroke-width="4"/><rect x="690" y="15" width="300" height="185" rx="12" fill="#eef3f5"/><text x="710" y="45" font-size="18">child PID ${r.child_pid}</text><text x="710" y="80" font-size="16">read FD ${f.child_read}: ${read?'open':'closed / 未起動'}</text><text x="710" y="112" font-size="16">write FD: 継承なし</text><text x="710" y="155" font-size="16">${childAlive?'起動済 / exit未回収':'起動前 / 回収済'}</text></svg>`;
}
$('prediction').addEventListener('input',()=>{$('prediction-state').textContent=$('prediction').value?'予想を入力済み。比較してから答えへ。':'予想はブラウザ内だけに保持します。';});
$('case').addEventListener('change',()=>{index=Number($('case').value);visible=0;render();});$('next').addEventListener('click',()=>{visible++;render();});$('all').addEventListener('click',()=>{visible=cases[index].result.timeline.length;render();});$('reset').addEventListener('click',()=>{visible=0;render();});$('reveal').addEventListener('click',()=>{$('answer').hidden=!$('answer').hidden;$('reveal').textContent=$('answer').hidden?'答えを表示':'答えを隠す';});
Promise.all([fetch('evidence/raw.json').then(r=>{if(!r.ok)throw Error('raw unavailable');return r.json();}),fetch('evidence/run.json').then(r=>{if(!r.ok)throw Error('run unavailable');return r.json();})]).then(([raw,run])=>{cases=raw;raw.forEach((c,i)=>{let o=document.createElement('option');o.value=i;o.textContent=c.id;$('case').append(o);});$('case').disabled=false;$('reset').disabled=false;$('provenance').textContent=`保存観測 ${run.observed_at_utc} / ${run.environment.system} ${run.environment.machine} / Python ${run.environment.python}。現在の再実行・kernel tracing・性能測定ではありません。`;render();}).catch(e=>{$('status').textContent='読込失敗: '+e.message+'。preview.py URLから開いてください。';});

const $=id=>document.getElementById(id);let current,prediction='unsure';
const label=register=>`(${register.version.join(',')})`;
const eventName=e=>e.action==='start'?'初期状態':e.action==='local-write-and-enqueue'?`${e.node} local write ${e.value} → ${e.message_id}をqueue`:e.action==='heal-model-link'?'モデルのリンク復旧（まだ配送しない）':`${e.message_id} → ${e.target}：${e.accepted?'採用':'古い／同一versionのため保持'}`;
function diagram(event){
 const partition=event.partition;
 const delivery=event.action==='deliver';
 const from=delivery?(event.target==='A'?460:110):110,to=delivery?(event.target==='A'?110:460):460;
 return `<svg class="diagram" viewBox="0 0 570 115" role="img" aria-label="replica AとB、${partition?'partition中・配送なし':delivery?'message '+event.message_id+'を'+event.target+'へ配送':'復旧・配送待ち'}"><defs><marker id="arrow-${event.step}-${event.accepted}" markerWidth="8" markerHeight="8" refX="7" refY="4" orient="auto"><path d="M0 0L8 4L0 8" fill="#396f81"/></marker></defs><rect x="35" y="25" width="150" height="62" rx="9" fill="#e6f1f5" stroke="#85a7b4"/><rect x="385" y="25" width="150" height="62" rx="9" fill="#e6f1f5" stroke="#85a7b4"/><text x="110" y="63" text-anchor="middle" fill="#234955">replica A</text><text x="460" y="63" text-anchor="middle" fill="#234955">replica B</text>${partition?'<path d="M230 56H340" stroke="#b87655" stroke-width="2" stroke-dasharray="5 5"/><text x="285" y="40" text-anchor="middle" fill="#975337">partition</text><text x="285" y="78" text-anchor="middle" fill="#975337">配送なし</text>':delivery?`<path d="M${from<to?185:385} 56H${from<to?380:190}" stroke="#396f81" stroke-width="2" marker-end="url(#arrow-${event.step}-${event.accepted})"/><text x="285" y="42" text-anchor="middle" fill="#396f81">${event.message_id}</text>`:'<path d="M185 56H385" stroke="#85a7b4" stroke-dasharray="5 5"/><text x="285" y="40" text-anchor="middle" fill="#396f81">復旧</text>'}</svg>`;
}
function render(){
 if(!current)return;const step=Number($('step').value);
 for(const mode of ['arrival','version-max']){
  const run=current[mode],e=run.events[step],same=JSON.stringify(e.state.A.register)===JSON.stringify(e.state.B.register);
  $(mode).innerHTML=`${diagram(e)}<div class="state">${['A','B'].map(node=>`<div class="node">replica ${node}<strong>${e.state[node].register.value}</strong><small>version ${label(e.state[node].register)} / clock ${e.state[node].clock}</small></div>`).join('')}</div><p class="event">event ${step}：${eventName(e)}</p><p class="badge ${same?'good':'bad'}">この時点：${same?'同じregister':'異なるregister'}</p>`;
 }
 $('step-label').textContent=`${step} / ${current.arrival.events.length-1}`;
 const arrival=current.arrival.summary,good=current['version-max'].summary;
 const outcome=arrival.converged&&good.converged?'both':!arrival.converged&&good.converged?'max-only':'neither';
 const predicted=prediction==='unsure'?'予測を選んで再計算すると照合できます。':prediction===outcome?'予測と今回の最終結果は一致。':'予測とは違います。全配送後も到着順上書きには不一致が残りました。';
 $('answer').textContent=`全配送後の答え：到着順上書きは${arrival.converged?'一致':'不一致'}、version maxは${good.converged?'一致':'不一致'}。${predicted} 現在表示しているeventは ${step}。`;
 $('oracle').textContent=`独立Oracle（書込み集合をsortして最大labelを選択）：${good.independent_max_oracle.value} ${label(good.independent_max_oracle)}。固定3 messageの全${current['version-max'].permutation_check.count}順でmax merge ${current['version-max'].permutation_check.max_passed}/6一致、arrival 0/6一致。`;
 $('event-json').textContent=JSON.stringify({messages:current.arrival.messages,arrival_event:current.arrival.events[step],max_event:current['version-max'].events[step]},null,2);
}
async function run(){
 $('status').textContent='Pythonで比較中…';
 try{
  prediction=$('prediction').value;
  const p=new URLSearchParams({order:$('order').value,duplicate:$('duplicate').checked?'1':'0'});
  const res=await fetch('/api/run?'+p),data=await res.json();if(!res.ok)throw Error(data.error);
  current=data;$('step').max=data.arrival.events.length-1;$('step').value=$('step').max;
  $('permutations').innerHTML='<table><thead><tr><th>全配送順（duplicateなし）</th><th>arrival一致</th><th>maxと独立Oracle一致</th></tr></thead><tbody>'+data['version-max'].permutation_check.permutations.map(r=>`<tr><td>${r.order.join(' → ')}</td><td>${r.arrival_converged?'yes':'no'}</td><td>${r.version_max_matches_oracle?'yes':'no'}</td></tr>`).join('')+'</tbody></table>';
  const execution=data['version-max'].execution;
  $('execution').textContent=`実行：Python ${execution.python} / ${execution.observed_at} / source SHA256 ${execution.source_sha256.slice(0,16)}… / real network: false`;
  $('raw').href=data.raw_path;render();$('status').textContent='Python計算完了。raw events/state/deliveryを保存しました。';
 }catch(error){$('status').textContent='計算できません：'+error.message;}
}
$('controls').addEventListener('submit',event=>{event.preventDefault();run();});$('step').addEventListener('input',render);
for(const [id,step] of [['partition',3],['heal',4],['last',null]])$(id).addEventListener('click',()=>{if(current){$('step').value=step===null?current.arrival.events.length-1:step;render();}});
run();

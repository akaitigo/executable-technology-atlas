'use strict';
const $=id=>document.getElementById(id);let rows=[],visible=0;
const stages=['ABSENT','CREATED','STARTED','RESUMED','PAUSED','STOPPED','DESTROYED','DEAD','FINISHED'];
function text(tag,t,cls){const e=document.createElement(tag);e.textContent=t;if(cls)e.className=cls;return e;}
function initial(row){return {stage:'ABSENT',counter:null,saved:row.input.saved,instance:0,process:1,alive:true};}
function stateAt(row,v){return visible?v.trace[Math.min(visible,v.steps)-1]?.after||initial(row):initial(row);}
function showState(s){return `${s.stage} / count=${s.counter===null?'∅':s.counter} / I${s.instance} P${s.process}${s.alive?'':' dead'}`;}
function render(){
 const row=rows[Number($('case').value)],r=row.result;$('cards').replaceChildren();$('trace').replaceChildren();$('diagram').replaceChildren();$('raw').textContent=JSON.stringify(row,null,2);
 if(r.phase==='input'){$('progress').textContent=`${row.id}: 入力拒否 ${r.reason}（traceなし）`;$('comparison').textContent='実行前に拒否。runtime拒否の有限traceと区別。';$('next').disabled=$('all').disabled=true;return;}
 const normal=r.variants.serialized,bad=r.variants.ephemeral,oracle=row.oracle.serialized,max=Math.max(normal.steps,bad.steps);visible=Math.min(visible,max);$('progress').textContent=`${row.id}: ${visible} / ${max} event表示（保存観測）`;
 for(const [name,v,cls] of [['正常serialized',normal,''],['ephemeral保存漏れ',bad,'bad'],['独立table oracle',oracle,'oracle']]){
  const s=stateAt(row,v),card=text('div','',`card ${cls}`);card.append(text('div',name),text('div',`counter=${s.counter===null?'∅':s.counter}`,'value'),text('div',`${s.stage} / instance${s.instance} / process${s.process} ${s.alive?'alive':'dead'}`),text('div',`snapshot: ${s.saved===null?'null（未提供）':s.saved}`,'token'),text('div',visible>=v.steps?v.status+(v.fault?' / '+v.fault.reason:''):'未終了'));$('cards').append(card);
 }
 const ns=stateAt(row,normal),os=stateAt(row,oracle);$('comparison').textContent=`正常state vs 独立oracle: ${JSON.stringify(ns)===JSON.stringify(os)?'一致':'不一致'}。${visible===max?'正常 '+normal.status+' / ephemeral '+bad.status:'最終結果は全event後。'}`;
 for(const [label,v,cls] of [['正常',normal,''],['保存漏れ',bad,'bad']]){const s=stateAt(row,v),line=text('div','', 'diagram');line.append(text('strong',label));for(const st of stages)line.append(text('span',st,'node'+(s.stage===st?' active '+cls:'')));$('diagram').append(line);}
 for(let n=0;n<visible;n++){const tr=document.createElement('tr');tr.append(text('td',`${n} / ${row.input.events[n]}`));for(const [v,cls] of [[normal,''],[bad,'bad'],[oracle,'']]){const t=v.trace[n];tr.append(text('td',t?`${showState(t.before)} → ${showState(t.after)}\n${t.callback||'callbackなし'}`:'—',cls));}$('trace').append(tr);}
 $('next').disabled=$('all').disabled=visible>=max;
}
$('prediction').addEventListener('input',()=>{$('prediction-note').textContent=$('prediction').value?'予想入力済み。比較してから答えへ。':'予想はこのブラウザ内だけに保持。';});
$('case').addEventListener('change',()=>{visible=0;render();});$('next').addEventListener('click',()=>{visible++;render();});$('all').addEventListener('click',()=>{visible=32;render();});$('reset').addEventListener('click',()=>{visible=0;render();});$('reveal').addEventListener('click',()=>{$('answer').hidden=!$('answer').hidden;$('reveal').textContent=$('answer').hidden?'答えを表示':'答えを隠す';});
Promise.all([fetch('evidence/raw.json').then(r=>r.json()),fetch('evidence/run.json').then(r=>r.json())]).then(([data,meta])=>{rows=data;rows.forEach((r,i)=>{const o=text('option',r.id);o.value=String(i);$('case').append(o);});$('environment').textContent=`保存観測 ${meta.observed_at_utc} / ${meta.environment.system} ${meta.environment.machine} / Python ${meta.environment.python}。実SDK/device/emulator/Android process death未実行。`;render();}).catch(e=>{$('progress').textContent='保存原票の読込に失敗: '+e.message;$('next').disabled=$('all').disabled=true;});

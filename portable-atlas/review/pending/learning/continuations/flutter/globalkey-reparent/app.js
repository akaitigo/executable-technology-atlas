'use strict';
const $=id=>document.getElementById(id);
const titles={globalSameFrame:'GlobalKey・同frame移動',globalGap:'GlobalKey・一度除去',valueSameFrame:'ValueKey・同frame移動'};
const phases={initial:'初期',prepared:'準備 A=1',transition:'移動 または 除去',atRight:'右に置いた後'};
const rawPath='probe/observations/attempt-01/actual.json';
const sourcePath='probe/observations/attempt-01/inputs/probe/lib/reparent_probe.dart';
const locks={observation:'63c439ee8f628f22331fb034c7296fd36cd7b27a226cc7868ca79b3243b5d170',source:'a7964316ca6a8ae6e008759cbf6191665c76633e4b48f11849bc76d1e2e4bbe3'};
const state={condition:'globalSameFrame',prediction:null,phase:'prepared',played:false};
let data=null,generation=0,loadingController=null;
function node(tag,text,cls){const e=document.createElement(tag);if(text!==undefined)e.textContent=text;if(cls)e.className=cls;return e;}
function stage(condition,phase){return data.cases.find(c=>c.id===condition).stages.find(s=>s.phase===phase);}
function clearAnswer(){$('answer').replaceChildren();$('answer').removeAttribute('data-match');$('answer').hidden=true;}
function clearDisplays(){
  for(const id of ['selected-rows','comparison-rows','raw-observation','source-code','boundary','event-summary','state-summary','selected-title','phase-label','comparison-title','observation-status'])$(id).replaceChildren();
  clearAnswer();$('comparison').hidden=true;$('boundary').hidden=true;$('raw-details').open=false;$('implementation').open=false;
  for(const b of $('timeline').querySelectorAll('button')){b.disabled=true;b.setAttribute('aria-pressed','false');}
}
function reset(clearPrediction){
  if(clearPrediction){state.prediction=null;document.querySelectorAll('input[name=prediction]').forEach(e=>e.checked=false);}
  state.phase='prepared';state.played=false;clearAnswer();$('raw-details').open=false;render();
}
function drawRows(target,record){
  target.replaceChildren();
  for(const slot of ['left','right']){
    const parent=record.parents.find(p=>p.slot===slot);
    const group=node('section',undefined,'parent-group');group.dataset.slot=slot;
    group.append(node('h4',`親Slot ${slot}`),node('p',`親SlotのElement ${parent.elementId}`,'slot-identity'));
    for(const row of record.rows.filter(r=>r.slot===slot)){
      const card=node('article',undefined,'row-card');card.dataset.item=row.itemId;
      card.append(node('b',`項目 ${row.itemId}`,'item-name'));
      const count=node('div',String(row.count),'count');count.append(node('small','回'));
      card.append(count,node('div',`State ${row.stateId}`,'identity'),node('div',`Element ${row.elementId}`,'element-identity'),node('div',`直親Element ${row.parentElementId}`,'parent-identity'),node('div',row.keyKind,'key-kind'));
      group.append(card);
    }
    if(!record.rows.some(r=>r.slot===slot))group.append(node('p','この親の下にAはありません。','empty-parent'));
    target.append(group);
  }
}
function eventText(record){return record.events.length?record.events.map(e=>`${e.event}(${e.stateId})`).join(' → '):'この段階のイベントはありません。';}
function render(){
  if(!data)return;
  const record=stage(state.condition,state.phase);
  $('selected-title').textContent=titles[state.condition];$('phase-label').textContent=phases[state.phase];
  drawRows($('selected-rows'),record);$('raw-observation').textContent=JSON.stringify(record,null,2);
  $('state-summary').textContent=`生存State ${record.rows.length}個 ／ GlobalKey.currentState：${state.condition==='valueSameFrame'?'対象外（ValueKey）':record.globalCurrentStateId??'null'}`;
  $('event-summary').textContent=`原票のイベント：${eventText(record)}（この実行の記録順。一般の全callback順序は保証しません。）`;
  $('comparison').hidden=!state.played;$('comparison-rows').replaceChildren();
  if(state.played){
    $('comparison-title').textContent='ほかの2条件との対照';
    for(const other of Object.keys(titles).filter(c=>c!==state.condition)){
      const panel=node('section',undefined,'comparison-case');panel.dataset.condition=other;panel.append(node('h4',titles[other]));
      const rows=node('div',undefined,'parent-groups');drawRows(rows,stage(other,state.phase));panel.append(rows,node('p',eventText(stage(other,state.phase)),'comparison-events'));$('comparison-rows').append(panel);
    }
  }else $('comparison-title').replaceChildren();
  $('boundary').hidden=!state.played||!['transition','atRight'].includes(state.phase);$('boundary').replaceChildren();
  if(!$('boundary').hidden){
    const before=stage(state.condition,'prepared').rows[0],after=record.rows[0];
    $('boundary').textContent=!after?'元のAはdisposeされ、生存StateもGlobalKey.currentStateもありません。このframe終了を通ってから右へ追加します。'
      :after.stateId===before.stateId?`直親Elementは${before.parentElementId}から${after.parentElementId}へ変わり、State ${after.stateId}・Element ${after.elementId}・${after.count}回は同じです。deactivateはこの移動でのdisposeではありません。`
      :`元のState ${before.stateId}は破棄され、State ${after.stateId}・Element ${after.elementId}・${after.count}回に作り直されました。同じKeyは、破棄済みStateの保存先ではありません。`;
  }
  $('replay').disabled=!state.prediction;$('reveal').disabled=!(state.played&&state.phase==='atRight');
  for(const b of $('timeline').querySelectorAll('button')){b.disabled=!state.played;b.setAttribute('aria-pressed',String(b.dataset.phase===state.phase));}
  $('observation-status').textContent=state.played?'保存実測を表示しています。移動/除去を比較し、続けて「右に置いた後」を選んでください。':'予想を選んでから保存実測を再生します。現在は準備時点です。';clearAnswer();
}
function reveal(){
  if(!data||!state.played||state.phase!=='atRight'||!state.prediction)return;
  const before=stage(state.condition,'prepared').rows[0],after=stage(state.condition,'atRight').rows[0];
  const same=before.stateId===after.stateId&&before.elementId===after.elementId;
  const outcome=same&&after.count===before.count?'retained':!same&&after.stateId!==before.stateId&&after.elementId!==before.elementId&&after.count===0?'fresh':same&&after.count===0?'sameZero':'unclassified';
  const match=state.prediction===outcome;
  $('answer').replaceChildren(node('strong',match?'予想と実測は一致しました。':'予想と実測は異なりました。'));
  $('answer').append(node('p',outcome==='retained'?`AはState ${after.stateId}・Element ${after.elementId}・${after.count}回を保って右へ移りました。同frameの再挿入で同じ生存期間が続いています。`:`AはState ${after.stateId}・Element ${after.elementId}・${after.count}回に作り直されました。元のStateはdisposeされ、回数の復元は起きませんでした。`));
  $('answer').append(node('p','判断：同じtree内の再配置と、削除後に必要なデータを保存・復元する仕組みを分けます。Keyだけに保存を任せず、データの所有階層を選びます。'));
  $('answer').dataset.match=String(match);$('answer').hidden=false;
}
async function checkedText(path,expected,signal){
  const response=await fetch(path,{cache:'no-store',signal});if(!response.ok)throw new Error(`保存ファイルの読込に失敗しました (${response.status})。`);
  const bytes=await response.arrayBuffer();const hash=[...new Uint8Array(await crypto.subtle.digest('SHA-256',bytes))].map(x=>x.toString(16).padStart(2,'0')).join('');
  if(hash!==expected)throw new Error('保存ファイルのdigestが一致しません。推測値や古い結果で再生せず、原票を確認してください。');return new TextDecoder().decode(bytes);
}
async function load(){
  const token=++generation;loadingController?.abort();loadingController=new AbortController();
  data=null;state.condition='globalSameFrame';state.prediction=null;state.phase='prepared';state.played=false;
  document.querySelectorAll('input[name=condition]').forEach(e=>e.checked=e.value===state.condition);document.querySelectorAll('input[name=prediction]').forEach(e=>e.checked=false);
  clearDisplays();$('lesson-body').hidden=true;$('load-error').hidden=true;$('load-error').replaceChildren();$('load-status').textContent='実測と実行時ソースの整合性を確認しています…';$('replay').disabled=true;$('reveal').disabled=true;document.documentElement.dataset.ready='loading';
  try{
    const [observedText,source]=await Promise.all([checkedText(rawPath,locks.observation,loadingController.signal),checkedText(sourcePath,locks.source,loadingController.signal)]);
    if(token!==generation)return;
    const measured=JSON.parse(observedText);
    if(!measured.passed||measured.kind!=='actual_flutter_engine_widget_probe'||measured.caseCount!==3||measured.snapshotCount!==12)throw new Error('所定の実Widget原票ではありません。');
    for(const id of Object.keys(titles)){
      const c=measured.cases.find(c=>c.id===id);
      if(!c?.passed||Object.keys(phases).some(phase=>!c.stages.some(s=>s.phase===phase&&s.passed&&s.parents.length===2&&s.rows.every(r=>['left','right'].includes(r.slot)))))throw new Error('必要な条件・時点が不足しています。');
    }
    data=measured;$('source-code').textContent=source;render();$('lesson-body').hidden=false;$('load-status').textContent='実測と実行時ソースのdigest照合済み。2026-10-06 / 3条件・12時点。';document.documentElement.dataset.ready='true';
  }catch(error){
    if(token!==generation)return;
    data=null;clearDisplays();$('lesson-body').hidden=true;$('load-error').hidden=false;$('load-error').textContent=error.message;$('load-status').textContent='教材を再生できません。原票を確認してから「原票を読み直す」で再試行できます。';document.documentElement.dataset.ready='error';
  }
}
for(const [id,title] of Object.entries(phases)){
  const b=node('button',title);b.type='button';b.dataset.phase=id;b.disabled=true;b.addEventListener('click',()=>{if(!data||!state.played)return;state.phase=id;render();});$('timeline').append(b);
}
document.querySelectorAll('input[name=condition]').forEach(e=>e.addEventListener('change',()=>{if(!data)return;state.condition=e.value;reset(true);}));
document.querySelectorAll('input[name=prediction]').forEach(e=>e.addEventListener('change',()=>{if(!data)return;state.prediction=e.value;reset(false);}));
$('replay').addEventListener('click',()=>{if(!data||!state.prediction)return;state.phase='transition';state.played=true;render();});
$('reset').addEventListener('click',()=>reset(true));$('reveal').addEventListener('click',reveal);$('reload').addEventListener('click',load);load();

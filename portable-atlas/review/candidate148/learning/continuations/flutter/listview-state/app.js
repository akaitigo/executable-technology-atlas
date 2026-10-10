'use strict';
const $=id=>document.getElementById(id);
const titles={withLookup:'callbackあり',withoutLookup:'callbackなし'};
const phases={initial:'初期',prepared:'準備 A=1 / B=2',reordered:'入替後 B → A',far:'遠方へ 640px',returned:'先頭へ戻る'};
const observationPath='probe/observations/attempt-01/actual.json';
const sourcePath='probe/observations/attempt-01/inputs/probe/lib/listview_probe.dart';
const locks={observation:'705039f72bed7b1dc19a07b41e91971ad79ae15320065227bbc78b3d6727decb',source:'186b493dca29aec53c3898c8b159d081b27ebc660ad51dc334efe559053847b3'};
const state={condition:'withLookup',prediction:null,phase:'prepared',played:false};
let data=null, generation=0, loadingController=null;
function node(tag,text,cls){const e=document.createElement(tag);if(text!==undefined)e.textContent=text;if(cls)e.className=cls;return e;}
function stage(condition,phase){return data.cases.find(c=>c.id===condition).stages.find(s=>s.phase===phase);}
function clearAnswer(){$('answer').replaceChildren();$('answer').removeAttribute('data-match');$('answer').hidden=true;}
function clearDisplays(){
  for(const id of ['selected-rows','comparison-rows','raw-observation','source-code','boundary','event-summary','selected-title','phase-label','comparison-title','observation-status'])$(id).replaceChildren();
  clearAnswer();$('comparison').hidden=true;$('boundary').hidden=true;
  $('raw-details').open=false;$('implementation').open=false;
  for(const button of $('timeline').querySelectorAll('button')){button.disabled=true;button.setAttribute('aria-pressed','false');}
}
function reset(clearPrediction){
  if(clearPrediction){state.prediction=null;document.querySelectorAll('input[name=prediction]').forEach(e=>e.checked=false);}
  state.phase='prepared';state.played=false;clearAnswer();$('raw-details').open=false;
  render();
}
function drawRows(target,record){
  target.replaceChildren();
  for(const row of record.rows){
    const card=node('article',undefined,'row-card');
    const head=node('div',undefined,'row-heading');head.append(node('b',`項目 ${row.itemId}`),node('small',`index ${row.index}`));
    const count=node('div',String(row.count),'count');count.append(node('small','回'));
    card.dataset.item=row.itemId;
    card.append(head,count,node('div',`State ${row.stateId}`,'identity'),node('div',`生成時：${row.mountedFor}`,'origin'));target.append(card);
  }
}
function render(){
  if(!data)return;
  const record=stage(state.condition,state.phase),other=state.condition==='withLookup'?'withoutLookup':'withLookup';
  $('selected-title').textContent=titles[state.condition];$('phase-label').textContent=phases[state.phase];
  drawRows($('selected-rows'),record);$('raw-observation').textContent=JSON.stringify(record,null,2);
  $('event-summary').textContent=`この段階の原票：initState ${record.events.filter(e=>e.event==='initState').length}件 / dispose ${record.events.filter(e=>e.event==='dispose').length}件 / builder呼出 ${record.builderCalls.length}件。`;
  $('comparison').hidden=!state.played;$('comparison-rows').replaceChildren();
  if(state.played){$('comparison-title').textContent=`対照：${titles[other]}`;drawRows($('comparison-rows'),stage(other,state.phase));}
  else $('comparison-title').replaceChildren();
  $('boundary').hidden=!state.played||!['far','returned'].includes(state.phase);$('boundary').replaceChildren();
  if(!$('boundary').hidden)$('boundary').textContent=state.phase==='far'?'A/Bはこのfixtureでは破棄され、I/Jが新しく生成されています。callbackは保持中の子の対応付けを助けます。':'どちらの条件も、先頭へ戻るとB/Aは新しいState・0回です。callbackは破棄済みStateや業務データの復元機能ではありません。';
  $('replay').disabled=!state.prediction;$('reveal').disabled=!(state.played&&state.phase==='reordered');
  for(const button of $('timeline').querySelectorAll('button')){button.disabled=!state.played;button.setAttribute('aria-pressed',String(button.dataset.phase===state.phase));}
  $('observation-status').textContent=state.played?'保存した実Widgetの観測を表示しています。各時点と対照条件を比べてください。':'予想を選び、入替後の保存実測を再生してください。現在は準備時点です。';
  clearAnswer();
}
function reveal(){
  if(!data||!state.played||state.phase!=='reordered'||!state.prediction)return;
  const before=stage(state.condition,'prepared').rows,after=stage(state.condition,'reordered').rows;
  const follows=after.every(row=>before.some(old=>old.itemId===row.itemId&&old.stateId===row.stateId&&old.count===row.count));
  const fresh=after.every(row=>!before.some(old=>old.stateId===row.stateId)&&row.count===0);
  const position=after.every((row,i)=>row.stateId===before[i]?.stateId&&row.count===before[i]?.count);
  const outcome=follows?'follows':fresh?'fresh':position?'position':'unclassified';
  const match=state.prediction===outcome;
  $('answer').replaceChildren(node('strong',match?'予想と実測は一致しました。':'予想と実測は異なりました。'));
  $('answer').append(node('p',follows?'Bに元のBのStateと2、Aに元のAのStateと1が付いています。callbackで現在のindexを返し、保持中のElementを対応付けた条件です。':'この入替ではB/Aに新しいStateが生成され、どちらも0です。項目Keyがあっても、今回の遅延生成一覧ではcallbackを省いた条件でStateを失いました。'));
  $('answer').append(node('p','次は「遠方へ」「先頭へ戻る」を再生してください。生存中の入替対応と、破棄後の保存は別の問題です。'));
  $('answer').dataset.match=String(match);$('answer').hidden=false;
}
async function checkedText(path,expected,signal){
  const response=await fetch(path,{cache:'no-store',signal});
  if(!response.ok)throw new Error(`保存ファイルの読込に失敗しました (${response.status})。`);
  const bytes=await response.arrayBuffer();
  const hash=[...new Uint8Array(await crypto.subtle.digest('SHA-256',bytes))].map(x=>x.toString(16).padStart(2,'0')).join('');
  if(hash!==expected)throw new Error('保存ファイルのdigestが一致しません。推測値や古い結果で再生せず、原票を確認してください。');
  return new TextDecoder().decode(bytes);
}
async function load(){
  const token=++generation;
  loadingController?.abort();loadingController=new AbortController();
  data=null;state.condition='withLookup';state.prediction=null;state.phase='prepared';state.played=false;
  document.querySelectorAll('input[name=condition]').forEach(e=>e.checked=e.value===state.condition);
  document.querySelectorAll('input[name=prediction]').forEach(e=>e.checked=false);
  clearDisplays();$('lesson-body').hidden=true;$('load-error').hidden=true;$('load-error').replaceChildren();
  $('load-status').textContent='保存実測と実行ソースの整合性を確認しています…';
  $('replay').disabled=true;$('reveal').disabled=true;
  document.documentElement.dataset.ready='loading';
  try{
    const [observedText,source]=await Promise.all([
      checkedText(observationPath,locks.observation,loadingController.signal),
      checkedText(sourcePath,locks.source,loadingController.signal)]);
    if(token!==generation)return;
    const measured=JSON.parse(observedText);
    if(!measured.passed||measured.kind!=='actual_flutter_engine_widget_probe'||measured.caseCount!==2||measured.snapshotCount!==10)throw new Error('所定の実Widget原票ではありません。');
    for(const id of Object.keys(titles)){
      const item=measured.cases.find(c=>c.id===id);
      if(!item?.passed||Object.keys(phases).some(phase=>!item.stages.some(s=>s.phase===phase&&s.passed&&s.rows.length===2)))throw new Error('必要な条件・時点が不足しています。');
    }
    data=measured;$('source-code').textContent=source;render();$('lesson-body').hidden=false;
    $('load-status').textContent='保存実測と実行ソースのdigestを照合済み。実測：2026-10-06 / 2条件・10時点。';
    document.documentElement.dataset.ready='true';
  }catch(error){
    if(token!==generation)return;
    data=null;clearDisplays();$('lesson-body').hidden=true;$('load-error').hidden=false;$('load-error').textContent=error.message;
    $('load-status').textContent='教材を再生できません。原票を確認してから「原票を読み直す」で再試行できます。';
    document.documentElement.dataset.ready='error';
  }
}
for(const [id,title] of Object.entries(phases)){
  const button=node('button',title);button.type='button';button.dataset.phase=id;button.disabled=true;
  button.addEventListener('click',()=>{if(!data||!state.played)return;state.phase=id;render();});$('timeline').append(button);
}
document.querySelectorAll('input[name=condition]').forEach(input=>input.addEventListener('change',()=>{if(!data)return;state.condition=input.value;reset(true);}));
document.querySelectorAll('input[name=prediction]').forEach(input=>input.addEventListener('change',()=>{if(!data)return;state.prediction=input.value;reset(false);}));
$('replay').addEventListener('click',()=>{if(!data||!state.prediction)return;state.phase='reordered';state.played=true;render();});
$('reset').addEventListener('click',()=>reset(true));$('reveal').addEventListener('click',reveal);$('reload').addEventListener('click',load);
load();

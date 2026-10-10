'use strict';
const $=id=>document.getElementById(id);
const titles={requested:'保持を要求する',notRequested:'保持を要求しない'};
const phases={initial:'初期',prepared:'準備 A=1 / B=2',far:'遠方へ 640px',returned:'先頭へ戻る'};
const rawPath='probe/observations/attempt-01/actual.json';
const sourcePath='probe/observations/attempt-01/inputs/probe/lib/keepalive_probe.dart';
const locks={observation:'5f4c2f19136aeb64f0593c04b2d5081477c70b03d69cf3529ac8c1557aba7f58',source:'f3d359a78c1da53af8108ad387719a95fa3b9c211692bd55b226796e60e933b8'};
const state={condition:'requested',prediction:null,phase:'prepared',played:false};
let data=null,generation=0,loadingController=null;
function node(tag,text,cls){const e=document.createElement(tag);if(text!==undefined)e.textContent=text;if(cls)e.className=cls;return e;}
function stage(condition,phase){return data.cases.find(c=>c.id===condition).stages.find(s=>s.phase===phase);}
function clearAnswer(){$('answer').replaceChildren();$('answer').removeAttribute('data-match');$('answer').hidden=true;}
function clearDisplays(){
  for(const id of ['selected-rows','comparison-rows','raw-observation','source-code','boundary','event-summary','state-summary','selected-title','phase-label','comparison-title','observation-status'])$(id).replaceChildren();
  clearAnswer();$('comparison').hidden=true;$('boundary').hidden=true;
  $('raw-details').open=false;$('implementation').open=false;
  for(const b of $('timeline').querySelectorAll('button')){b.disabled=true;b.setAttribute('aria-pressed','false');}
}
function reset(clearPrediction){
  if(clearPrediction){state.prediction=null;document.querySelectorAll('input[name=prediction]').forEach(e=>e.checked=false);}
  state.phase='prepared';state.played=false;clearAnswer();$('raw-details').open=false;render();
}
function drawRows(target,record){
  target.replaceChildren();
  for(const storage of ['layout','cached']){
    const group=node('section',undefined,'storage-group');group.dataset.storage=storage;
    group.append(node('h4',storage==='layout'?'layout：レイアウト中':'cached：画面外で生存'));
    group.append(node('p',storage==='layout'?'保持cacheの外。本fixtureではviewport内の2項目。':'生存中のElementを読んだ値。画面に描かれた証拠ではありません。'));
    const rows=node('div',undefined,'rows');
    for(const row of record.rows.filter(r=>r.storage===storage)){
      const card=node('article',undefined,'row-card');card.dataset.item=row.itemId;
      const heading=node('div',undefined,'row-heading');heading.append(node('b',`項目 ${row.itemId}`),node('small',`index ${row.renderIndex}`));
      const count=node('div',String(row.count),'count');count.append(node('small','回'));
      card.append(heading,count,node('div',`State ${row.stateId}`,'identity'),node('div',`生成時：${row.mountedFor}`,'origin'),node('span',storage==='cached'?'cachedで生存':'layoutで生存','storage-label'));
      rows.append(card);
    }
    if(rows.childElementCount)group.append(rows);
    else group.append(node('div',storage==='cached'?'cachedの生存Stateはありません。':'layoutの項目はありません。','empty-cache'));
    target.append(group);
  }
}
function render(){
  if(!data)return;
  const record=stage(state.condition,state.phase),other=state.condition==='requested'?'notRequested':'requested';
  $('selected-title').textContent=titles[state.condition];$('phase-label').textContent=phases[state.phase];
  drawRows($('selected-rows'),record);$('raw-observation').textContent=JSON.stringify(record,null,2);
  const layout=record.rows.filter(r=>r.storage==='layout').length,cached=record.rows.filter(r=>r.storage==='cached').length;
  $('state-summary').textContent=`この原票の生存State ${record.rows.length}個：layout ${layout}個 ＋ cached ${cached}個`;
  $('event-summary').textContent=`この段階：initState ${record.events.filter(e=>e.event==='initState').length}件 / dispose ${record.events.filter(e=>e.event==='dispose').length}件。`;
  $('comparison').hidden=!state.played;$('comparison-rows').replaceChildren();
  if(state.played){$('comparison-title').textContent=`対照：${titles[other]}`;drawRows($('comparison-rows'),stage(other,state.phase));}else $('comparison-title').replaceChildren();
  $('boundary').hidden=!state.played||!['far','returned'].includes(state.phase);$('boundary').replaceChildren();
  if(!$('boundary').hidden){
    $('boundary').textContent=state.phase==='far'
      ?(state.condition==='requested'?'I/Jがlayout中でも、A/Bはcachedで生存しています。見えないことと破棄されたことを分けてください。':'A/Bは破棄され、I/Jだけが生存しています。AutomaticKeepAliveの祖先があっても、今回この子は保持を要求していません。')
      :(state.condition==='requested'?'A/Bは同じStateと回数で戻り、今度はI/Jがcachedです。生存Stateは4個のままです。':'A/Bは新しいState・0回です。I/Jは破棄されています。保持要求なしの子では、回数の復元は起きませんでした。');
  }
  $('replay').disabled=!state.prediction;$('reveal').disabled=!(state.played&&state.phase==='returned');
  for(const b of $('timeline').querySelectorAll('button')){b.disabled=!state.played;b.setAttribute('aria-pressed',String(b.dataset.phase===state.phase));}
  $('observation-status').textContent=state.played?'保存実測を表示しています。farのcachedとlayoutを比べ、続けて「先頭へ戻る」を選んでください。':'予想を選んでから、遠方へ移動した保存実測を再生します。現在は準備時点です。';
  clearAnswer();
}
function reveal(){
  if(!data||!state.played||state.phase!=='returned'||!state.prediction)return;
  const before=stage(state.condition,'prepared').rows;
  const after=stage(state.condition,'returned').rows.filter(row=>['A','B'].includes(row.itemId));
  const retained=after.every(row=>before.some(old=>old.itemId===row.itemId&&old.stateId===row.stateId&&old.count===row.count));
  const fresh=after.every(row=>!before.some(old=>old.stateId===row.stateId)&&row.count===0);
  const sameZero=after.every(row=>before.some(old=>old.itemId===row.itemId&&old.stateId===row.stateId)&&row.count===0);
  const outcome=retained?'retained':fresh?'fresh':sameZero?'sameZero':'unclassified';
  const match=state.prediction===outcome;
  $('answer').replaceChildren(node('strong',match?'予想と実測は一致しました。':'予想と実測は異なりました。'));
  $('answer').append(node('p',retained?'AはS1・1回、BはS2・2回で戻りました。遠方でcachedとして保持されていた同じStateです。戻った時点でもI/Jがcachedで生存しています。':'A/Bは新しいStateで作り直され、どちらも0回です。遠方へ移ったときに元のA/Bが破棄されていました。祖先の準備だけで、子を無条件に保持するわけではありません。'));
  $('answer').append(node('p','判断：一時的なStateの生存を保つ条件と、業務データやprocess終了後の保存・復元を分けて設計します。この実験の保持要求は一定で、動的切替は扱いません。'));
  $('answer').dataset.match=String(match);$('answer').hidden=false;
}
async function checkedText(path,expected,signal){
  const response=await fetch(path,{cache:'no-store',signal});if(!response.ok)throw new Error(`保存ファイルの読込に失敗しました (${response.status})。`);
  const bytes=await response.arrayBuffer();
  const hash=[...new Uint8Array(await crypto.subtle.digest('SHA-256',bytes))].map(x=>x.toString(16).padStart(2,'0')).join('');
  if(hash!==expected)throw new Error('保存ファイルのdigestが一致しません。推測値や古い結果で再生せず、原票を確認してください。');
  return new TextDecoder().decode(bytes);
}
async function load(){
  const token=++generation;loadingController?.abort();loadingController=new AbortController();
  data=null;state.condition='requested';state.prediction=null;state.phase='prepared';state.played=false;
  document.querySelectorAll('input[name=condition]').forEach(e=>e.checked=e.value===state.condition);
  document.querySelectorAll('input[name=prediction]').forEach(e=>e.checked=false);
  clearDisplays();$('lesson-body').hidden=true;$('load-error').hidden=true;$('load-error').replaceChildren();
  $('load-status').textContent='実測と実行時ソースの整合性を確認しています…';$('replay').disabled=true;$('reveal').disabled=true;document.documentElement.dataset.ready='loading';
  try{
    const [observedText,source]=await Promise.all([checkedText(rawPath,locks.observation,loadingController.signal),checkedText(sourcePath,locks.source,loadingController.signal)]);
    if(token!==generation)return;
    const measured=JSON.parse(observedText);
    if(!measured.passed||measured.kind!=='actual_flutter_engine_widget_probe'||measured.caseCount!==2||measured.snapshotCount!==8)throw new Error('所定の実Widget原票ではありません。');
    for(const id of Object.keys(titles)){
      const c=measured.cases.find(c=>c.id===id);
      if(!c?.passed||Object.keys(phases).some(phase=>!c.stages.some(s=>s.phase===phase&&s.passed&&s.rows.every(r=>['layout','cached'].includes(r.storage)))))throw new Error('必要な条件・時点が不足しています。');
    }
    data=measured;$('source-code').textContent=source;render();$('lesson-body').hidden=false;
    $('load-status').textContent='実測と実行時ソースのdigest照合済み。2026-10-06 / 2条件・8時点。';document.documentElement.dataset.ready='true';
  }catch(error){
    if(token!==generation)return;
    data=null;clearDisplays();$('lesson-body').hidden=true;$('load-error').hidden=false;$('load-error').textContent=error.message;
    $('load-status').textContent='教材を再生できません。原票を確認してから「原票を読み直す」で再試行できます。';document.documentElement.dataset.ready='error';
  }
}
for(const [id,title] of Object.entries(phases)){
  const b=node('button',title);b.type='button';b.dataset.phase=id;b.disabled=true;
  b.addEventListener('click',()=>{if(!data||!state.played)return;state.phase=id;render();});$('timeline').append(b);
}
document.querySelectorAll('input[name=condition]').forEach(e=>e.addEventListener('change',()=>{if(!data)return;state.condition=e.value;reset(true);}));
document.querySelectorAll('input[name=prediction]').forEach(e=>e.addEventListener('change',()=>{if(!data)return;state.prediction=e.value;reset(false);}));
$('replay').addEventListener('click',()=>{if(!data||!state.prediction)return;state.phase='far';state.played=true;render();});
$('reset').addEventListener('click',()=>reset(true));$('reveal').addEventListener('click',reveal);$('reload').addEventListener('click',load);
load();

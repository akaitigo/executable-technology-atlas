import {initialState,transition,views} from './model.mjs';
const $=id=>document.getElementById(id);let state=initialState(),sourceHashes=null;const events=[],actions=[];
function render() {
  const derived=views(state);
  for(const mode of ['duplicated','normalized']) {
    const v=derived[mode],list=$(mode+'-list');list.replaceChildren();
    for(const e of v.list){const row=document.createElement('li');row.dataset.id=e.id;row.textContent=e.id+': '+e.name;list.append(row);}
    if(!v.list.length){const row=document.createElement('li');row.textContent='entityなし';list.append(row);}
    const detail=$(mode+'-detail');detail.textContent=v.detail?v.detail.id+': '+v.detail.name:'未選択';
    $(mode+'-drift').textContent='保存データ差分ID: '+(v.driftIds.join(', ')||'なし');
    $(mode+'-selected').textContent='selectedId: '+(v.selectedId??'null');
  }
  $('owner').textContent=JSON.stringify(state,null,2);
  $('raw').textContent=JSON.stringify({kind:'actual-browser-normalized-state-ui',at:new Date().toISOString(),environment:{userAgent:navigator.userAgent,language:navigator.language,width:innerWidth,height:innerHeight},sourceHashes,state,views:derived,events,actions,feedback:$('feedback').textContent},null,2);
}
function dispatch(actionId,input) {
  const before=structuredClone(state),startedAt=new Date().toISOString(),result=transition(state,input);state=result.state;
  events.push({sequence:events.length+1,actionId,input:structuredClone(input),startedAt,completedAt:new Date().toISOString(),before,after:structuredClone(state),outcome:result.outcome});
  $('result').textContent=(result.outcome.accepted?'受理: ':'拒否: ')+result.outcome.reason;render();
}
sourceHashes=await fetch('sources.json').then(r=>r.json()).then(m=>m.sourceHashes);render();
$('predict').onclick=()=>{const value=$('prediction').value;actions.push({type:'prediction',value,at:new Date().toISOString()});$('prediction-status').textContent='予想を保存: '+value;render();};
$('select').onclick=()=>dispatch('select',{type:'select',id:$('selection').value});
$('edit').onclick=()=>dispatch('edit',{type:'edit',id:state.normalized.selectedId,name:$('name').value});
$('remove').onclick=()=>dispatch('remove',{type:'remove',id:state.normalized.selectedId});
$('unknown-edit').onclick=()=>dispatch('unknown-edit',{type:'edit',id:'ghost',name:'Ghost'});
$('unknown-remove').onclick=()=>dispatch('unknown-remove',{type:'remove',id:'ghost'});
$('reset').onclick=()=>dispatch('reset',{type:'reset'});
$('check-answer').onclick=()=>{const value=$('answer').value;const messages={normalize:'適切。entityの所有を一箇所にし、IDからlist/detailをderiveする。draftは保存データと区別する。',copies:'不十分。同じ保存データをcopyしたまま片方だけ編集すると、今回のlist/detailは不整合になる。',global:'不適切。全stateをglobalにする必要はない。共有保存データと選択/draftの所有範囲を分けて考える。'};$('feedback').textContent=messages[value]||'回答を選んでください。';actions.push({type:'answer',value,at:new Date().toISOString()});render();};

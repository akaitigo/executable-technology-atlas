import {initial,apply,IDS,validOverride} from './api.mjs';
const $=id=>document.getElementById(id),sourceHashes=(await(await fetch('sources.json')).json()).sourceHashes;
let state=initial(),events=[],actions=[],feedback='';
function metrics(){return Object.fromEntries(IDS.map(id=>{const e=$(id),c=getComputedStyle(e);return [id,{background:c.backgroundColor,color:c.color,radius:c.borderRadius,minHeight:c.minHeight,padding:c.padding,opacity:c.opacity,disabled:e.disabled,disabledAttribute:e.hasAttribute('disabled'),type:e.getAttribute('type'),variant:e.dataset.variant,text:e.textContent,instanceToken:c.getPropertyValue('--instance-bg').trim(),count:state.counts[id]}];}));}
function raw(){const m=metrics();$('raw').textContent=JSON.stringify({kind:'actual-browser-token-button-ui',at:new Date().toISOString(),environment:{ua:navigator.userAgent,language:navigator.language,viewport:{width:innerWidth,height:innerHeight},url:location.href},sourceHashes,state,metrics:m,events,actions,feedback},null,2);return m;}
function render(){
 $('lab').dataset.theme=state.theme;$('theme').value=state.theme;$('disabled').checked=state.disabled;
 for(const e of [$('bug-row'),$('safe-a')]){e.style.removeProperty('--instance-bg');e.style.removeProperty('--instance-fg');}
 if(state.override){$('bug-row').style.setProperty('--instance-bg',state.override);$('bug-row').style.setProperty('--instance-fg','#ffffff');}
 if(validOverride(state.override)){$('safe-a').style.setProperty('--instance-bg',state.override);$('safe-a').style.setProperty('--instance-fg','#ffffff');}
 for(const id of IDS)$(id).disabled=state.disabled&&id.endsWith('-a');
 const m=metrics();for(const mode of ['bug','safe'])$(mode+'-metrics').textContent=['a','b'].map(n=>{const v=m[mode+'-'+n];return n.toUpperCase()+': bg '+v.background+' / fg '+v.color+'\ndisabled='+v.disabled+' / opacity='+v.opacity;}).join('\n');
 $('status').textContent='theme='+state.theme+' / override='+(state.override||'未定義')+' / 局所API='+(validOverride(state.override)?'hex受理':'テーマfallback');$('counts').textContent='実button activation: '+IDS.map(id=>id+'='+state.counts[id]).join(' / ');raw();
}
function dispatch(input){const startedAt=new Date().toISOString(),before=structuredClone(state),r=apply(state,input);state=r.state;render();events.push({sequence:events.length+1,input,before,after:structuredClone(state),outcome:r.outcome,startedAt,completedAt:new Date().toISOString(),computed:metrics()});raw();}
for(const id of IDS)$(id).addEventListener('click',()=>dispatch({type:'activate',id}));
for(const id of IDS)for(const type of ['keydown','keyup'])$(id).addEventListener(type,e=>{actions.push({type,key:e.key,target:id,at:new Date().toISOString(),disabled:$(id).disabled});raw();});
document.addEventListener('focusin',e=>{actions.push({type:'focusin',target:e.target.id,at:new Date().toISOString()});raw();});
 $('theme').addEventListener('change',()=>dispatch({type:'theme',value:$('theme').value}));$('override').addEventListener('click',()=>dispatch({type:'override',value:$('token').value}));$('invalid').addEventListener('click',()=>dispatch({type:'override',value:'not-a-color'}));$('clear').addEventListener('click',()=>dispatch({type:'override',value:''}));$('disabled').addEventListener('change',()=>dispatch({type:'disabled',value:$('disabled').checked}));$('reset').addEventListener('click',()=>dispatch({type:'reset'}));
 $('predict').addEventListener('click',()=>{actions.push({type:'prediction',value:$('prediction').value,at:new Date().toISOString()});$('prediction-result').textContent='予想を保存: '+$('prediction').value;raw();});
 $('check-answer').addEventListener('click',()=>{const value=$('answer').value;feedback=({fallback:'不十分。定義済みの不正色はvar fallbackで色の型検証されません。',scope:'適切。上書きの所有範囲と入力検証を分け、native buttonの挙動も確認します。',global:'不適切。隣の上書き漏れを全体の強いselectorで隠すとAPI境界が曖昧になります。'})[value];actions.push({type:'answer',value,at:new Date().toISOString()});$('feedback').textContent=feedback;raw();});
render();

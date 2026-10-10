const $=id=>document.getElementById(id);
let canonical,drafts,sharedDraft,selected,mode,generation=0,lastKind='OK',reason='',failure=null,invalid=false;
const ledger=[];
function draft(){return mode==='normal'?drafts[selected]:sharedDraft;}
function url(){return new URL(location.href).search;}
function snapshot(){return {mode,selected,canonical:{...canonical},drafts:{...drafts},shared:sharedDraft,editor:$('editor').value,url:url(),kind:lastKind,reason,failure};}
function emit(action,input=null){ledger.push({seq:ledger.length,action,input,state:snapshot()});$('ledger').textContent=JSON.stringify(ledger,null,2);}
function clearComparison(){$('comparison').textContent='未比較';$('answer').textContent='';$('answer').hidden=true;}
function route(push=false){const u=new URL(location.href);u.search='';u.searchParams.set('mode',mode);u.searchParams.set('id',selected);history[push?'pushState':'replaceState']({generation},'',u);}
function render(){
 $('mode').value=mode;$('selected').textContent='選択ID: '+selected;$('editor').value=draft()??canonical[selected];$('canonical-a').textContent=canonical.a;$('canonical-b').textContent=canonical.b;$('drafts').textContent=JSON.stringify({byId:drafts,shared:sharedDraft},null,2);$('url').textContent='URL '+url();$('operation-status').textContent=lastKind+(reason?': '+reason:'');$('operation-status').className=lastKind==='OK'?'good':'bad';
}
function refused(code){const error=new Error(code);error.inputRefusal=true;throw error;}
function execute(action,fn,input=null){clearComparison();try{if(failure)throw new Error(failure);fn();lastKind='OK';reason='';render();emit(action,input);}catch(error){lastKind=error.inputRefusal?'INPUT_REFUSED':'EXECUTION_FAILURE';reason=error.message;if(!error.inputRefusal)failure=error.message;render();emit(action,input);}}
function reset(initialId='a'){mode=$('mode').value;canonical={a:'Alpha',b:'Beta'};drafts={};sharedDraft=null;selected=['a','b'].includes(initialId)?initialId:'a';invalid=false;failure=null;lastKind='OK';reason='';generation++;$('prediction-canonical').value=$('prediction-view').value='';clearComparison();route();render();emit('reset',mode);}
function select(id,push=true){execute('select',()=>{if(!['a','b'].includes(id))refused('UNKNOWN_ID');selected=id;invalid=false;route(push);},id);}
$('mode').onchange=()=>reset();$('reset').onclick=()=>reset();$('select-a').onclick=()=>select('a');$('select-b').onclick=()=>select('b');$('unknown').onclick=()=>select('c');
$('editor').oninput=()=>{const text=$('editor').value;execute('edit',()=>{const trimmed=text.trim();if(trimmed.length<1||trimmed.length>40){invalid=true;refused('INVALID_TEXT');}invalid=false;if(mode==='normal')drafts[selected]=trimmed;else sharedDraft=trimmed;},text);};
$('cancel').onclick=()=>execute('cancel',()=>{if(mode==='normal')delete drafts[selected];else sharedDraft=null;invalid=false;});
$('save').onclick=()=>execute('save',()=>{if(invalid)refused('INVALID_TEXT');const value=draft();if(value==null)refused('NO_DRAFT');canonical[selected]=value;if(mode==='normal')delete drafts[selected];else sharedDraft=null;});
window.addEventListener('popstate',event=>execute('popstate',()=>{const u=new URL(location.href),id=u.searchParams.get('id');if(event.state?.generation!==generation){route();refused('STALE_HISTORY');}if(!['a','b'].includes(id)){route();refused('UNKNOWN_ID');}selected=id;invalid=false;},new URL(location.href).searchParams.get('id')));
for(const id of ['prediction-canonical','prediction-view']){$(id).oninput=clearComparison;$(id).onchange=clearComparison;}
$('compare').onclick=()=>{clearComparison();if(failure){$('comparison').textContent='EXECUTION_FAILURE: '+failure;return;}const prediction='正本予想: '+($('prediction-canonical').value||'未記入')+' / 表示予想: '+($('prediction-view').value||'未記入');$('comparison').textContent=prediction+' / 実観測: '+lastKind+' · 選択 '+selected+' · 表示 '+$('editor').value+' · 正本 a='+canonical.a+', b='+canonical.b;$('answer').hidden=false;$('answer').textContent=lastKind==='INPUT_REFUSED'?'入力拒否 '+reason+'。正本と選択は変更せず、予想と拒否理由を比較する。':mode==='normal'?'draftはID別に保持し、cancel/saveは選択IDだけへ作用する。保存前の編集では正本が変わらない。':'共有draftはIDを持たず、別IDへの流用・他ID取消による消失・誤保存を起こす。正本とdraftの所有を分けて読む。';};
$('failure').onclick=()=>execute('inject-failure',()=>{throw new Error('injected render action failure');});
const initialMode=new URL(location.href).searchParams.get('mode');$('mode').value=initialMode==='shared'?'shared':'normal';reset(new URL(location.href).searchParams.get('id')||'a');

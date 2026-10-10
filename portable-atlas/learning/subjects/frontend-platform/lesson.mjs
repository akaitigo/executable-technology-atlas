import * as a from './importer-a.mjs';
import * as b from './importer-b.mjs';
import {journal,record,evaluated} from './journal.mjs';
evaluated('lesson');
const $=id=>document.getElementById(id);
let sourceHashes,ready=false,lastAction=null,lastAssignment=null;
function render(){
  const ar=a.read(),br=b.read(),j=journal();
  $('a-live').textContent=ar.live;$('a-copy').textContent=ar.snapshot;$('b-live').textContent=br.live;$('b-copy').textContent=br.snapshot;
  $('evaluation').textContent=`counter評価 ${j.evaluationCounts.counter}回 / importer A ${j.evaluationCounts['importer-a']}回 / B ${j.evaluationCounts['importer-b']}回`;
  $('identity').textContent=`同じnamespace object: ${a.namespace()===b.namespace()}（同じDocument・同じ解決済みURL）`;
  $('events').textContent=j.events.map(e=>`${e.sequence} ${e.at} ${e.type} ${JSON.stringify(e.detail)}`).join('\n');
  $('raw').textContent=JSON.stringify({kind:'actual-browser-native-modules',at:new Date().toISOString(),environment:{userAgent:navigator.userAgent,language:navigator.language,width:innerWidth,height:innerHeight},ready,sourceHashes,views:{a:ar,b:br},namespaceSame:a.namespace()===b.namespace(),journal:j,lastAction,lastAssignment,feedback:$('feedback').textContent});
}
function action(id,fn){$(id).addEventListener('click',async()=>{const startedAt=new Date().toISOString();try{const result=await fn();lastAction={id,startedAt,completedAt:new Date().toISOString(),result};record('ui-action',lastAction);$('action-status').textContent=`${id}: ${JSON.stringify(result)}`;}catch(error){lastAction={id,startedAt,completedAt:new Date().toISOString(),rejected:true,name:error.name,message:error.message};record('ui-rejection',lastAction);$('action-status').textContent=`${id}: ${error.name}（値は更新されない）`;}render();});}
action('a-increment',()=>a.mutate());action('b-increment',()=>b.mutate());action('zero',()=>a.mutate(0));action('minus',()=>a.mutate(-1));action('invalid',()=>a.mutate(NaN));
action('reimport',async()=>{const ns=await import('./counter.mjs');return {sameNamespace:ns===a.namespace(),live:ns.count,ordinal:ns.evaluationOrdinal};});
for(const [id,fn] of [['assign-import',a.assignImportedBinding],['assign-namespace',b.assignNamespace]])$(id).addEventListener('click',()=>{lastAssignment={id,at:new Date().toISOString(),...fn()};$('assignment-status').textContent=`${id}: ${lastAssignment.name||'成功'} / count ${a.read().live}`;render();});
for(const id of ['loading','syntax'])$('failure-'+id).addEventListener('click',()=>{const frame=$(id+'-frame');frame.hidden=false;frame.src='failed-case.html?case='+id;record('isolated-fixture-requested',{caseId:id});render();});
$('predict').addEventListener('click',()=>{$('prediction-feedback').textContent=$('prediction').value?'予想を保存。A/Bを操作して比べよう。':'先に予想を選んでください。';record('prediction',{value:$('prediction').value});render();});
$('check-answer').addEventListener('click',()=>{$('feedback').textContent=({snapshot:'不足。数値のコピーは更新されない。現在値が必要ならlive bindingを読む。',live:'適切。live bindingを読み、更新はexport元の関数で行う。importerからの代入は拒否される。',assign:'不適切。namespaceへの直接代入はTypeError。この教材ではincrement()を呼ぶ。'})[$('answer').value]||'回答を選んでください。';record('answer',{value:$('answer').value});render();});
render();
try{sourceHashes=(await (await fetch('sources.json')).json()).sourceHashes;ready=true;for(const id of ['a-increment','b-increment','zero','minus','reimport','invalid','assign-import','assign-namespace'])$(id).disabled=false;$('action-status').textContent='module初期化完了';record('source-manifest-loaded',{files:Object.keys(sourceHashes).length});render();}catch(error){$('action-status').textContent='source manifest読込失敗: '+error.name;render();}

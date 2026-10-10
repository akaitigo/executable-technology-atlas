'use strict';
const BINDINGS={results:'2eca5fa63bbe09e0a863e205dbf132cefe8c46be0a2c1ae290401cc5766c63c5',cases:'c6687c4d4aab3b150ac8e5e1b0d88c5840d8bbb5762a70f593ceda010fe50a8e',source:'9ab9ae89433f6a2609c6b1ce41e0f7627c923166ef37edb485298ccd25db4939'};
const PATHS={results:'observations/run-01/results.json',cases:'cases.json',source:'observations/run-01/inputs/scheduler.py'};
const LABELS={'dependency-wait':'依存待ち（未解放）','ready-capacity':'空き待ち（解放済み）',running:'実行中',completed:'完了'};
const $=id=>document.getElementById(id);
let saved=null,fixtures=null,sourceText='',generation=0,controller=null,step=0,playing=false;
const sha=async text=>Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256',new TextEncoder().encode(text))),x=>x.toString(16).padStart(2,'0')).join('');
function message(text,error=false){$('status').textContent=text;$('status').dataset.error=String(error);}
function clear(){
 playing=false;step=0;
 for(const id of ['result','refusal','comparison','source'])$(id).hidden=true;
 for(const id of ['rows','timeline','clock','summary','sets','meaning','events','comparison-rows','answer','source','refusal-text','refusal-json'])$(id).replaceChildren();
 for(const id of ['previous','next','source-button','answer-button'])$(id).disabled=true;
 $('event-details').open=false;
 delete document.body.dataset.case;delete document.body.dataset.time;delete document.body.dataset.response;
 document.body.dataset.state='prepared';
}
function selected(){if(!saved)return null;return [...saved.cases,...saved.refusals].find(x=>x.id===$('condition').value);}
function prepare(){clear();const s=selected();$('input').textContent=s?JSON.stringify(s.requestBefore,null,2):'';$('input-details').open=false;$('play').disabled=!s||!$('prediction').value;if(s)message('予想を選んで保存した予定を再生してください。');}
function cell(text,attrs={}){const td=document.createElement('td');td.textContent=String(text);for(const [k,v] of Object.entries(attrs))td.setAttribute(k,v);return td;}
function timeline(payload,time){
 const ns='http://www.w3.org/2000/svg',svg=document.createElementNS(ns,'svg');svg.setAttribute('viewBox','0 0 760 235');svg.setAttribute('role','img');svg.setAttribute('aria-label',`保存した全予定。選択時刻${time}。区間は開始を含み終了を含まない。`);
 const x=t=>80+t*75;
 function part(tag,attrs,text){const e=document.createElementNS(ns,tag);for(const [k,v] of Object.entries(attrs))e.setAttribute(k,v);if(text!==undefined)e.textContent=text;svg.append(e);return e;}
 for(let t=0;t<=8;t++){part('line',{x1:x(t),x2:x(t),y1:20,y2:210,stroke:'#d8e2e2'});part('text',{x:x(t),y:230,'text-anchor':'middle'},t);}
 Object.entries(payload.schedule).forEach(([task,[start,end]],i)=>{const y=30+i*44;part('text',{x:18,y:y+21},task);part('rect',{x:x(start),y,width:(end-start)*75,height:30,rx:4,fill:'#b4ddd4',stroke:'#006b63','data-task':task,'data-start':start,'data-end':end});part('text',{x:x(start)+8,y:y+21},`[${start},${end})`);});
 part('line',{x1:x(time),x2:x(time),y1:10,y2:215,stroke:'#a63827','stroke-width':3,'data-selected-time':time});
 $('timeline').replaceChildren(svg);
}
function render(){
 const observed=selected();if(!observed||!playing)return;
 const response=observed.response;document.body.dataset.case=observed.id;document.body.dataset.response=response.accepted?'accepted':'refused';document.body.dataset.state='shown';
 if(!response.accepted){$('refusal').hidden=false;$('refusal-text').textContent='入力を拒否しました：'+response.reason;$('refusal-json').textContent=JSON.stringify(response,null,2);$('answer-button').disabled=false;message('拒否の保存結果を表示しました。実行予定はありません。');return;}
 const p=response.payload,s=p.snapshots[step];$('result').hidden=false;$('comparison').hidden=false;document.body.dataset.time=String(s.time);
 $('clock').textContent=`t = ${s.time}`;$('summary').textContent=`容量 ${observed.requestBefore.capacity} ／ 実行中 ${s.occupied} ／ 空き ${s.freeSlots} ／ 仮想時刻上の完了 ${s.completed.length}/4`;
 $('rows').replaceChildren(...s.rows.map(r=>{const tr=document.createElement('tr');tr.dataset.task=r.task;tr.append(cell(r.task),cell(LABELS[r.state],{'data-state':r.state}),cell(r.unfinishedParents.join(', ')||'なし',{'data-dependencies-complete':String(r.dependenciesComplete)}),cell(r.releasedAt??'未解放'),cell(r.start??'未開始'),cell(r.end??'未設定'));return tr;}));
 $('sets').textContent=`完了通知済み: ${s.schedulerProcessed.join(', ')||'なし'} ／ 実際に完了: ${s.completed.join(', ')||'なし'} ／ graphlib.is_active(): ${s.graphlibActive}`;
 $('meaning').textContent=!s.graphlibActive&&s.running.length?'graphlibは処理済みでも、仕事はまだ実行中です。実完了まで追跡します。':observed.id==='capacity-one'&&s.time===1?'CはAが完了したので解放済みですが、Bで枠が埋まり空き待ちです。DはB/Cの完了を待っています。':observed.id==='capacity-two'&&s.time===3?'枠は1つ空いています。それでもDはBの完了を待つため始められません。':observed.id==='done-on-start'?'完了通知が早すぎます。「解放済み」の仕事でも、右の未完了の親を確認してください。':'schedulerの解放と、実際の親の完了を別々に確認します。';
 $('events').textContent=JSON.stringify(p.events.filter(e=>e.time<=s.time),null,2);timeline(p,s.time);
 $('comparison-rows').replaceChildren(...saved.cases.map(c=>{const tr=document.createElement('tr');tr.dataset.case=c.id;const label=fixtures.cases.find(x=>x.id===c.id).label;tr.append(cell(label),cell(c.response.payload.makespan),cell(c.response.payload.dependencyViolations.map(x=>x.join('→')).join('、')||'なし'));return tr;}));
 $('previous').disabled=step===0;$('next').disabled=step===p.snapshots.length-1;$('source-button').disabled=false;$('answer-button').disabled=false;message('保存した仮想時刻を表示しています。実workerは起動していません。');
}
async function load(){
 const mine=++generation;if(controller)controller.abort();controller=new AbortController();const signal=controller.signal;
 saved=null;fixtures=null;sourceText='';clear();$('condition').replaceChildren();$('condition').disabled=true;$('play').disabled=true;$('input').textContent='';$('input-details').open=false;document.body.dataset.state='loading';message('保存した計算結果と実装の内容を確認しています。');
 try{
  const texts=await Promise.all(Object.keys(PATHS).map(async key=>{const r=await fetch(PATHS[key],{cache:'no-store',signal});if(!r.ok)throw Error(`保存資料を取得できません（${r.status}）。`);const text=await r.text();if(await sha(text)!==BINDINGS[key])throw Error('保存資料の内容が固定した版と一致しません。古い結果は表示しません。');return [key,text];}));
  if(mine!==generation)return;const data=Object.fromEntries(texts);const result=JSON.parse(data.results),cases=JSON.parse(data.cases);
  if(result.cases.length!==4||result.refusals.length!==6)throw Error('保存した条件が不足しています。');
  saved=result;fixtures=cases;sourceText=data.source;
  for(const c of [...fixtures.cases,...fixtures.refusals]){const option=document.createElement('option');option.value=c.id;option.textContent=c.label||'入力拒否：'+c.id;$('condition').append(option);}
  $('condition').disabled=false;prepare();
 }catch(error){if(mine!==generation)return;saved=null;fixtures=null;sourceText='';clear();$('input').textContent='';$('condition').replaceChildren();$('condition').disabled=true;$('play').disabled=true;document.body.dataset.state='error';message('読み込みを止めました。'+error.message,true);}
}
$('condition').addEventListener('change',prepare);$('prediction').addEventListener('change',prepare);
$('reset').addEventListener('click',()=>{$('prediction').value='';prepare();});$('reload').addEventListener('click',load);
$('play').addEventListener('click',()=>{if(!selected()||!$('prediction').value)return;clear();playing=true;render();});
$('previous').addEventListener('click',()=>{if(step>0){step--;$('answer').textContent='';render();}});
$('next').addEventListener('click',()=>{const s=selected();if(s?.response.accepted&&step<s.response.payload.snapshots.length-1){step++;$('answer').textContent='';render();}});
$('source-button').addEventListener('click',()=>{if(playing&&selected()?.response.accepted){$('source').textContent=sourceText;$('source').hidden=false;}});
$('answer-button').addEventListener('click',()=>{const s=selected();if(!playing||!s)return;const truth=!s.response.accepted?'refused':s.response.payload.dependenciesRespected?'valid':'invalid';const matching=$('prediction').value===truth;const why=truth==='refused'?'入力を拒否し、payloadはnullです。':truth==='invalid'?'A→B、B→Dで親の完了前に開始します。4tickで終わっても依存を守った予定ではありません。':'全ての辺で親の終了時刻以上に開始しています。容量による待ちとは別の判断です。';$('answer').textContent=(matching?'予想と一致しました。':'予想と違いました。')+why+' 答えは全予定の開始条件についてです。';});
load();

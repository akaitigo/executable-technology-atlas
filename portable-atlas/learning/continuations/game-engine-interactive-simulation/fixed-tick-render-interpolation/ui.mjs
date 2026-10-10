import {simulate} from './producer.mjs';
const $=id=>document.getElementById(id),cases=await (await fetch('cases.json')).json();let selected=cases[0],version=0,pending=null,ignored=0;
function clear(){version++;$('status').textContent='未実行';$('raw').textContent='';$('trace').textContent='';$('answerbody').textContent='';$('answer').open=false;$('answer').hidden=true;$('canvas').getContext('2d').clearRect(0,0,880,240);}
function select(c){selected=c;for(const id of ['prediction','next','override'])$(id).value='';clear();$('condition').textContent=c.id+' / '+JSON.stringify(c.input);}
for(const c of cases){const b=document.createElement('button');b.textContent=c.label;b.onclick=()=>select(c);$('casebuttons').append(b);}
for(const id of ['prediction','next','override'])$(id).oninput=clear;
$('reset').onclick=()=>select(selected);
const number=s=>{const [n,d='1']=s.split('/');return Number(n)/Number(d)};
async function execute(hold){clear();const generation=version,started=new Date().toISOString(),caseId=selected.id,prediction={render:$('prediction').value,next:$('next').value};let result;
try{result=simulate($('override').value.trim()?JSON.parse($('override').value):selected.input);}catch(e){result={status:'REFUSED',reason:'JSON_PARSE',trace:[],ticks:[]};}
const frames=[];
if(result.status==='OK')try{
 const scale=Math.min(4,760/Math.max(1,...result.trace.flatMap(r=>[number(r.current),number(r.previous),number(r.render)])));
 for(const row of result.trace){const draw=await new Promise((resolve,reject)=>{const timer=setTimeout(()=>{cancelAnimationFrame(handle);reject(Error('RAF_UNAVAILABLE'))},3000);const handle=requestAnimationFrame(timestamp=>{clearTimeout(timer);if(generation!==version){resolve({cancelled:true,frame:row.frame});return;}
  const ctx=$('canvas').getContext('2d'),x=40+Math.round(number(row.render)*scale);ctx.clearRect(0,0,880,240);ctx.fillStyle='#18263c';ctx.font='16px system-ui';ctx.fillText(`frame ${row.frame} / 合成 ${row.syntheticMs}ms / alpha ${row.alpha}`,20,30);
  for(const [key,y,color] of [['previous',80,'#778899'],['current',140,'#2377aa'],['render',200,'#dd4400']]){const px=40+Math.round(number(row[key])*scale);ctx.fillStyle=color;ctx.fillRect(px-4,y-4,9,9);ctx.fillText(`${key} = ${row[key]}`,300,y+5);}
  const pixel=Array.from(ctx.getImageData(x,200,1,1).data);resolve({frame:row.frame,rafTimestampMs:timestamp,wallUTC:new Date().toISOString(),syntheticMs:row.syntheticMs,render:row.render,scale,markerPixelX:x,markerPixelY:200,rgba:pixel});
 });});if(draw.cancelled)break;frames.push(draw);if(generation!==version)break;}
}catch(e){result={status:'EXECUTION_FAILURE',reason:e.message,trace:[],ticks:[]};}
const record={id:caseId,started,completed:new Date().toISOString(),generation,inputPrediction:prediction,result,draws:frames,syntheticClock:'fixture integer ms; never rAF delta',renderClock:'actual rAF timestamp only; no interval or latency claim'};
if(hold&&result.status==='OK'&&generation===version){pending={generation,record};$('status').textContent='描画済み・結果保留';}else apply({generation,record});
}
function apply(p){if(p.generation!==version){ignored++;$('ignored').textContent='古い結果の無視: '+ignored;return;}
const r=p.record.result;$('raw').textContent=JSON.stringify(p.record,null,2);$('status').textContent=r.status;
if(r.status!=='OK')return;
const table=document.createElement('table');table.innerHTML='<tr><th>frame</th><th>合成ms</th><th>previous</th><th>current</th><th>余り</th><th>alpha</th><th>render</th><th>書戻し後state</th></tr>';
for(const row of r.trace){const tr=document.createElement('tr');for(const k of ['frame','syntheticMs','previous','current','remainderMs','alpha','render','stateAfterRender']){const td=document.createElement('td');td.textContent=row[k];tr.append(td)}table.append(tr);}$('trace').append(table);
$('answer').hidden=false;$('answerbody').textContent=r.trace.map(x=>`frame${x.frame}: previous ${x.previous}, current ${x.current}, alpha ${x.alpha} → 描画 ${x.render}。描画後state ${x.stateAfterRender}。`).join(' ')+' '+(r.input.mode==='NORMAL'?'正常は描画値をstateへ戻さず、次tickはcurrentから20進める。':'書戻し故障は補間値をcurrentへ代入し、後tickの始点を汚す。')+' 実務ではtick stateとrender snapshotを分離する。このtoy結果はengine物理精度・FPS・latencyを証明しない。';
}
$('run').onclick=()=>execute(false);$('hold').onclick=()=>execute(true);$('release').onclick=()=>{if(pending){const p=pending;pending=null;apply(p)}};
for(const path of ['README.md','EXPECTATIONS.md','producer.mjs','ui.mjs','oracle.json','custom-oracle.json','oracle.py','SOURCES.md','evidence/current.json','evidence/browser.json','evidence/verification.json','reference']){const a=document.createElement('a');a.textContent=path==='reference'?'元Subject E3':path;a.href='document.html?file='+encodeURIComponent(path);$('links').append(a,document.createTextNode(' / '));}
const current=await(await fetch('evidence/current.json')).json();const a=document.createElement('a');a.textContent='実行raw';a.href='document.html?file=evidence/'+current.raw;$('links').append(a);select(selected);

'use strict';
const $=s=>document.querySelector(s);
let fixtures=[],last=null,version=0;
const files=['CONTRACT.md','model.py','oracle.py','fixtures.py','verify.py','serve.py','app.js','index.html','README.md','COVERAGE.md','skills/rv32i-hazard/SKILL.md'];
for(const file of files){const a=document.createElement('a');a.textContent=file;a.href='/source.html?file='+encodeURIComponent(file);$('#sources').append(a);}
function selected(){return fixtures.find(f=>f.id===$('#fixture').value);}
function showProgram(){const f=selected();const lines=f.program.map((p,i)=>`I${i+1}: ${p.op} x${p.rd}, x${p.rs1}, ${p.op==='ADD'?'x'+p.rs2:p.imm}`);const initial=f.initial.map((v,i)=>v?'x'+i+'='+v:null).filter(Boolean).join(', ')||'すべて0';$('#program').textContent=lines.join('\n')+'\n初期register: '+initial;}
function clear(){version++;last=null;$('#summary').textContent='未実行';$('#answer').textContent='';$('#raw').textContent='';$('#peer-raw').textContent='';$('#peers').replaceChildren();$('#trace-wrap').replaceChildren();$('#status').textContent='条件が変わりました。結果を更新するため実行してください。';showProgram();}
function table(headers,rows){const t=document.createElement('table');const h=t.insertRow();headers.forEach(x=>{const th=document.createElement('th');th.textContent=x;h.append(th);});for(const row of rows){const tr=t.insertRow();for(const cell of row){tr.insertCell().textContent=cell;}}return t;}
function render(r){last=r;$('#raw').textContent=JSON.stringify(r,null,2);$('#status').textContent='実行済み：'+r.fixture+' / '+r.mode;
 const sparse=r.registers.map((v,i)=>v?'x'+i+'='+v:null).filter(Boolean).join(', ')||'すべて0';
 $('#summary').textContent=`${r.cycles} cycle / ${r.stalls} stall / ${r.retired} 命令完了。逐次oracleと${r.matches_oracle?'一致':'不一致'}。register: ${sparse}`;
 const p=$('#prediction').value;$('#answer').textContent=p?((p==='yes')===r.matches_oracle?'予測は一致しました。':'予測と結果が違います。ID-latchとEX経路を比べてください。'):'予測は未回答です。結果を踏まえ、条件を変える前に説明してください。';
 const t=table(['cycle','IF','ID','EX','MEM','WB','待つ？','EX operand','EX経路','EX結果'],r.trace.map(v=>[v.cycle,...v.stages.map(n=>n===null?'—':'I'+n),v.stalled?'stall':'—',v.ex_operands.join(', '),v.ex_paths.join(', '),v.ex_result===null?'—':v.ex_result]));
 r.trace.forEach((v,i)=>{if(v.stalled)t.rows[i+1].className='wait';});$('#trace-wrap').replaceChildren(t);
}
async function request(mode){const response=await fetch('/run',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({fixture:$('#fixture').value,mode})});const data=await response.json();if(!response.ok)throw Error(data.error);return data;}
$('#fixture').addEventListener('change',clear);$('#mode').addEventListener('change',clear);
$('#prediction').addEventListener('change',()=>{if(last)render(last);});
$('#run').onclick=async()=>{const v=version;try{const r=await request($('#mode').value);if(v===version)render(r);}catch(e){clear();$('#status').textContent='実行失敗: '+e.message;}};
$('#compare').onclick=async()=>{const v=version;try{const results=[];for(const mode of ['none','stall','forwarding'])results.push(await request(mode));if(v!==version)return;$('#peer-raw').textContent=JSON.stringify(results,null,2);$('#peers').replaceChildren(table(['対策','cycle','stall','oracle'],results.map(r=>[r.mode,r.cycles,r.stalls,r.matches_oracle?'一致':'不一致'])));$('#status').textContent='3対策比較済み：'+$('#fixture').value;}catch(e){clear();$('#status').textContent='比較失敗: '+e.message;}};
$('#reset').onclick=()=>{$('#fixture').value='chain';$('#mode').value='none';$('#prediction').value='';clear();};
fetch('/fixtures').then(r=>r.json()).then(data=>{fixtures=data;for(const f of data){const o=document.createElement('option');o.value=f.id;o.textContent=f.id;$('#fixture').append(o);}showProgram();}).catch(e=>$('#status').textContent='初期化失敗: '+e.message);

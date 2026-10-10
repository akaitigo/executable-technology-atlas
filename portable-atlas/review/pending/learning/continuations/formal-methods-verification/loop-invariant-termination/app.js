const $ = id => document.getElementById(id);
let cases=[], version=0, active=0, pending=0;
const names={observed_correct:'境界を保ち guard exit',invariant_violation:'境界の不変条件違反',budget_exhausted:'budget不足・事後条件未観測',input_refused:'入力拒否'};
function clearResult(){ $('results').hidden=true;document.querySelector('#results details').open=false;for(const id of ['answer','summary','comparison'])$(id).textContent='';$('trace').replaceChildren();$('diagram').replaceChildren();}
function stale(){version++;clearResult();$('status').textContent='入力または予測が変わりました。再実行してください。';}
function restore(){active=Number($('case').value);$('input').value=cases[active].stdin;$('prediction').value='';stale();}
$('case').addEventListener('change',restore);$('prediction').addEventListener('change',stale);$('input').addEventListener('input',stale);
$('reset').addEventListener('click',restore);
async function run(){
 const v=++version,stdin=$('input').value,pred=$('prediction').value;
 pending++;$('run').disabled=true;clearResult();$('status').textContent='独立プロセスで実行中…';
 try{
  const response=await fetch('/api/calculate',{method:'POST',body:stdin,headers:{'Content-Type':'application/json'}});
  if(!response.ok)throw Error('HTTP '+response.status);
  const data=await response.json();if(v!==version)return;
  const r=data.result;
  $('comparison').textContent=pred?('予測 '+names[pred]+' ／ 実際 '+names[r.category]+' ／ '+(pred===r.category?'一致':'不一致')):'予測未選択 ／ 実際 '+names[r.category];
  $('summary').textContent=r.category==='input_refused'?'入力拒否：'+r.error:'分類：'+names[r.category]+' ｜ 終了状態：'+r.completion+' ｜ 完了本体数：'+r.iterations+' ｜ 境界I：'+r.boundary_invariant_all+' ｜ 事後条件：'+(r.postcondition===null?'未観測':r.postcondition)+' ｜ 観測variant下降：'+r.variant_decreases;
  $('trace').replaceChildren();
  for(const row of r.trace||[]){
   const tr=document.createElement('tr');tr.dataset.boundary=row.boundary;tr.dataset.bad=row.boundary&&!row.equals_n;
   for(const value of [row.k,row.phase,row.x,row.y,row.sum,row.equals_n,row.boundary?'● 検査点':'○ 途中']){
    const td=document.createElement('td');td.textContent=value;tr.append(td);
   }$('trace').append(tr);
  }
  const ns='http://www.w3.org/2000/svg',svg=document.createElementNS(ns,'svg');svg.setAttribute('viewBox','0 0 720 210');
  const series=(r.trace||[]).filter(row=>row.boundary);
  for(const [i,row] of series.entries()){
   const cx=40+i*640/Math.max(1,series.length-1),cy=155-row.x*13;
   const c=document.createElementNS(ns,'circle');c.setAttribute('cx',cx);c.setAttribute('cy',cy);c.setAttribute('r','7');c.setAttribute('fill',row.equals_n?'#147d77':'#c34b25');c.dataset.k=row.k;c.dataset.x=row.x;svg.append(c);
   const t=document.createElementNS(ns,'text');t.setAttribute('x',cx);t.setAttribute('y',190);t.setAttribute('text-anchor','middle');t.setAttribute('font-size','12');t.textContent='k'+row.k+' x'+row.x+' y'+row.y;svg.append(t);
  }
  $('diagram').replaceChildren(svg);$('answer').textContent=JSON.stringify(data,null,2);
  $('results').hidden=false;$('status').textContent='比較しました。request '+data.receipt.request_id;
 }catch(e){if(v===version)$('status').textContent='実行失敗：'+e.message;}
 finally{pending--;$('run').disabled=pending>0;}
}
$('run').addEventListener('click',run);
$('step').addEventListener('click',()=>{try{let d=JSON.parse($('input').value);if(!Number.isInteger(d.budget)||d.budget<0||d.budget>=8)throw Error('budgetを0..7にしてください');d.budget++;$('input').value=JSON.stringify(d,null,2);stale();run();}catch(e){$('status').textContent=e.message;}});
$('toggle').addEventListener('click',()=>{try{let d=JSON.parse($('input').value);if(!['normal','double-y'].includes(d.body))throw Error('本体名を確認してください');d.body=d.body==='normal'?'double-y':'normal';$('input').value=JSON.stringify(d,null,2);stale();run();}catch(e){$('status').textContent=e.message;}});
fetch('/api/cases').then(r=>r.json()).then(rows=>{cases=rows;rows.forEach((r,i)=>{const o=document.createElement('option');o.value=i;o.textContent=r.id;$('case').append(o);});$('case').value='1';restore();});

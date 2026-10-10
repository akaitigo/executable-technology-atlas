const $=id=>document.getElementById(id);
const names={accepted:'受入（意味一致は別確認）',rejected:'CSV契約で拒否',input_refused:'入力形式で拒否'};
let cases=[],version=0,pending=0;
function clear(){ $('results').hidden=true;$('answer-panel').open=false;for(const id of ['comparison','summary','raw','typed','answer'])$(id).textContent='';$('records').replaceChildren();$('mapping').replaceChildren();}
function stale(){version++;clear();$('status').textContent='条件または予想が変わりました。再実行してください。';}
function restore(){ $('input').value=cases[Number($('case').value)].stdin;$('prediction').value='';stale();}
$('case').addEventListener('change',restore);$('prediction').addEventListener('change',stale);$('input').addEventListener('input',stale);$('reset').addEventListener('click',restore);
for(const cell of document.querySelectorAll('[data-case]'))cell.addEventListener('click',()=>{$('case').value=cell.dataset.case;restore();});
async function run(){
 const v=++version,stdin=$('input').value,pred=$('prediction').value;
 pending++;$('run').disabled=true;clear();$('status').textContent='実CSV writer/readerを子プロセスで実行中…';
 try{
  const response=await fetch('/api/calculate',{method:'POST',body:stdin,headers:{'Content-Type':'application/json'}});
  if(!response.ok)throw Error('HTTP '+response.status);
  const data=await response.json();if(v!==version)return;
  const r=data.result;
  $('comparison').textContent=pred?'予想 '+names[pred]+' ／ 実際 '+names[r.category]+' ／ '+(pred===r.category?'一致':'不一致'):'予想未選択 ／ 実際 '+names[r.category];
  $('summary').textContent=r.category==='input_refused'?'入力拒否：'+r.error:'分類：'+names[r.category]+' ｜ reason：'+(r.reason||'なし')+' ｜ reader：'+r.reader+' ｜ mode：'+r.mode+' ｜ runtime：'+r.runtime;
  $('raw').textContent=(r.csv||'').split('\n').map((line,i,all)=>(i+1)+': '+(i===all.length-1&&line===''?'（最終改行の終端）':line)).join('\n');
  const ns='http://www.w3.org/2000/svg',svg=document.createElementNS(ns,'svg');
  svg.setAttribute('viewBox','0 0 700 '+Math.max(70,(r.mapping||[]).length*52));
  for(const [i,m] of (r.mapping||[]).entries()){
   const t=document.createElementNS(ns,'text');t.setAttribute('x','15');t.setAttribute('y',String(35+i*52));t.setAttribute('font-size','17');t.dataset.field=m.field;t.dataset.column=m.column===null?'default':m.column;t.textContent=(m.column===null?'列なし：'+m.default:'列'+m.column+' '+r.header[m.column-1])+' → '+m.field;svg.append(t);
  }$('mapping').replaceChildren(svg);
  for(const row of r.records||[]){
   const tr=document.createElement('tr');tr.dataset.record=row.record;tr.dataset.endLine=row.end_line;
   for(const value of [row.record,row.end_line,JSON.stringify(row.cells),JSON.stringify(row.mapped),JSON.stringify(row.typed||null)]){
    const td=document.createElement('td');td.textContent=value;tr.append(td);
   }$('records').append(tr);
  }
  $('typed').textContent=JSON.stringify(r.typed_rows||[],null,2);
  $('answer').textContent=JSON.stringify(data,null,2);
  $('results').hidden=false;$('status').textContent='比較しました。request '+data.receipt.request_id;
 }catch(e){if(v===version)$('status').textContent='実行失敗：'+e.message;}
 finally{pending--;$('run').disabled=pending>0;}
}
$('run').addEventListener('click',run);
$('fault').addEventListener('click',()=>{try{const d=JSON.parse($('input').value);if(!['name','position-fault'].includes(d.mode))throw Error('modeを確認してください');d.mode=d.mode==='name'?'position-fault':'name';$('input').value=JSON.stringify(d,null,2);stale();run();}catch(e){$('status').textContent=e.message;}});
fetch('/api/cases').then(r=>r.json()).then(rows=>{cases=rows;rows.forEach((c,i)=>{const o=document.createElement('option');o.value=i;o.textContent=c.id;$('case').append(o);});$('case').value='0';restore();});

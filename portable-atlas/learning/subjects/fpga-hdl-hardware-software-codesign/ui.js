'use strict';
const $=id=>document.getElementById(id);
let cases=[], index=0, visible=0;
const oracleNext=[1,2,3,0]; // UI specification table, never derived from saved outputs
function expected(events,asyncMode){let q=0,p=0;return events.map(e=>{if(e.rst&&(e.edge||asyncMode)){q=0;p=0;}else if(e.edge){const old=q;q=e.en?oracleNext[q]:q;p=old;}return [q,p];});}
function line(label,rows,key,y,color){let path='',lastY=y;let text='';rows.slice(0,visible).forEach((r,i)=>{let x=160+i*85,yy=y-r[key]*6;path+=(i?'L':'M')+x+' '+lastY+' L'+x+' '+yy+' L'+(x+80)+' '+yy;lastY=yy;text+=`<text x="${x+30}" y="${yy-7}" font-size="13">${r[key]}</text>`;});return `<text x="8" y="${y}" font-size="13">${label}</text><path d="${path}" stroke="${color}" fill="none" stroke-width="3"/>${text}`;}
function render(){
 const c=cases[index],r=c.result; $('raw').textContent=JSON.stringify(c,null,2);$('rows').replaceChildren();$('wave').replaceChildren();
 if(r.status==='rejected'){ $('status').textContent='入力拒否: '+r.error; $('counts').textContent='結果なし（正常な空traceとは区別）';$('next').disabled=true;$('all').disabled=true;return; }
 const events=c.input.events, sync=r.traces.sync,bug=r.traces['next-state-bug'],as=r.traces.async,os=expected(events,false),oa=expected(events,true);
 $('next').disabled=visible>=events.length;$('all').disabled=visible>=events.length;
 $('status').textContent=events.length?`${c.id}: ${visible} / ${events.length} eventを表示`:'正常な空trace: 0 event / 初期 q=0,prev=0';
 let mismatches=0;
 for(let i=0;i<visible;i++){
  let e=events[i], tr=document.createElement('tr');const mismatch=bug[i].q!==os[i][0]||bug[i].prev!==os[i][1];mismatches+=Number(mismatch);
  const vals=[`${e.t} / ${e.edge}`,`${e.en} / ${e.rst}`,`${sync[i].q}, ${sync[i].prev}`,`${bug[i].q}, ${bug[i].prev}${mismatch?' ≠ oracle':''}`,`${as[i].q}, ${as[i].prev}`,`${os[i].join(',')} / ${oa[i].join(',')}`];
  vals.forEach((v,j)=>{let td=document.createElement('td');td.textContent=v;if(j===3&&mismatch)td.className='bad';tr.append(td);});$('rows').append(tr);
 }
 $('counts').textContent=`表示範囲の異常版 vs sync oracle不一致: ${mismatches}。asyncは別契約のoracleで比較。`;
 let width=Math.max(800,160+85*visible);let svg=`<svg viewBox="0 0 ${width} 310" role="img" aria-label="表示eventのモデル波形"><rect width="100%" height="100%" fill="white"/>`;
 [[sync,'sync','#117a65'],[bug,'bug','#b03a2e'],[as,'async','#2471a3']].forEach(([rows,name,color],i)=>{svg+=line(name+' q',rows,'q',55+i*80,color)+line(name+' prev',rows,'prev',90+i*80,color);});
 events.slice(0,visible).forEach((e,i)=>{svg+=`<text x="${160+i*85}" y="290" font-size="12">t=${e.t}${e.edge?' ↑':''}</text>`;});$('wave').innerHTML=svg+'</svg>';
}
$('prediction').addEventListener('input',()=>{$('prediction-state').textContent=$('prediction').value?'予想を入力済み。比較してから答えへ。':'予想はこのブラウザ内だけに保持します。';});
$('case').addEventListener('change',()=>{index=Number($('case').value);visible=0;render();});
$('next').addEventListener('click',()=>{visible++;render();});$('all').addEventListener('click',()=>{visible=cases[index].input.events.length;render();});$('reset').addEventListener('click',()=>{visible=0;render();});
$('reveal').addEventListener('click',()=>{$('answer').hidden=!$('answer').hidden;$('reveal').textContent=$('answer').hidden?'答えを表示':'答えを隠す';});
Promise.all([fetch('evidence/raw.json').then(r=>{if(!r.ok)throw Error('raw unavailable');return r.json();}),fetch('evidence/run.json').then(r=>{if(!r.ok)throw Error('run unavailable');return r.json();})]).then(([raw,run])=>{cases=raw;for(let i=0;i<raw.length;i++){let o=document.createElement('option');o.value=i;o.textContent=raw[i].id;$('case').append(o);}$('case').disabled=false;$('reset').disabled=false;$('provenance').textContent=`保存観測 ${run.observed_at_utc} / ${run.environment.system} ${run.environment.machine} / Python ${run.environment.python}。現在の再実行を意味しません。`;render();}).catch(e=>{$('status').textContent='観測読込失敗: '+e.message+'。preview.pyのURLから開いてください。';});

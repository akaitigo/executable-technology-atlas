'use strict';
const BUNDLE_SHA = '8513423eca07281630ee8b6926b9947ed62060a28bfcffa73ffe7ee00bc2879b';
const $ = id => document.getElementById(id);
const ids = ['causal-r1','causal-r2','scalar-inverse','display-edges'];
const names = ['入力の因果辺 · R1','同じ辺 · 再生R2','誤モデル：時計から逆推論','誤モデル：表示順を辺に追加'];
const words = {before:'左が先',after:'右が先',concurrent:'並行'};
let generation=0, aborter=null, result=null, pairIndex=0;
const hash = async text => Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256',new TextEncoder().encode(text)))).map(v=>v.toString(16).padStart(2,'0')).join('');
function selected(){return document.querySelector('input[name=case]:checked').value;}
function caseButtons(){const i=ids.indexOf(selected());$('previous-case').disabled=i===0;$('next-case').disabled=i===3;}
function invalidate(message='条件・予想が変わりました。保存した計算を読み直してください。'){
  generation++; if(aborter) aborter.abort(); aborter=null;result=null;pairIndex=0;
  $('result').hidden=true;$('answer').hidden=true;$('answer').textContent='';$('answer-button').disabled=true;
  $('comparison').querySelector('tbody').replaceChildren();$('raw').textContent='';$('raw-details').open=false;
  $('diagram').replaceChildren();$('path-evidence').replaceChildren();$('message').className='';$('message').textContent=message;$('read-button').disabled=false;caseButtons();
}
function choose(index){document.querySelector(`input[value="${ids[index]}"]`).checked=true;$('prediction').value='';invalidate();}
function element(name,attrs={},text=''){const e=document.createElementNS('http://www.w3.org/2000/svg',name);for(const[k,v]of Object.entries(attrs))e.setAttribute(k,v);if(text)e.textContent=text;return e;}
function draw(){
  if(!result)return;const svg=$('diagram');svg.replaceChildren();const w=window.innerWidth<640?300:520;const h=360;
  svg.setAttribute('viewBox',`0 0 ${w} ${h}`);const x={P:w*.27,Q:w*.73};const positions={};
  for(const[e,i]of result.replay.map((v,i)=>[v,i])){const ev=result.events.find(v=>v.id===e);positions[e]={x:x[ev.process],y:52+i*50};}
  svg.append(element('text',{x:x.P,y:22,'text-anchor':'middle','font-size':16},'P'),element('text',{x:x.Q,y:22,'text-anchor':'middle','font-size':16},'Q'));
  const defs=element('defs');const marker=element('marker',{id:'arrow',markerWidth:8,markerHeight:8,refX:7,refY:3,orient:'auto'});marker.append(element('path',{d:'M0,0 L7,3 L0,6',fill:'#426775'}));defs.append(marker);svg.append(defs);
  for(const edge of result.base_edges){const a=positions[edge.from],b=positions[edge.to];svg.append(element('line',{x1:a.x,y1:a.y+11,x2:b.x,y2:b.y-15,stroke:'#426775','stroke-width':2,'stroke-dasharray':edge.kind==='message'?'6 4':'','marker-end':'url(#arrow)','data-from':edge.from,'data-to':edge.to,'data-kind':edge.kind}));}
  const row=result.pair_rows[pairIndex];
  for(const edge of row.rule_path_edges){if(!result.base_edges.some(e=>e.from===edge.from&&e.to===edge.to)){const a=positions[edge.from],b=positions[edge.to];svg.append(element('line',{x1:a.x+9,y1:a.y+8,x2:b.x+9,y2:b.y-12,stroke:'#b66b05','stroke-width':3,'stroke-dasharray':'4 3','data-inference':`${edge.from}->${edge.to}`}));}}
  for(const event of result.events){const p=positions[event.id];svg.append(element('circle',{cx:p.x,cy:p.y,r:14,fill:row.left===event.id||row.right===event.id?'#168a74':'#e0edf2',stroke:'#315d6e'}));svg.append(element('text',{x:p.x,y:p.y+5,'text-anchor':'middle','font-size':17,fill:row.left===event.id||row.right===event.id?'white':'#173848'},event.id));svg.append(element('text',{x:p.x+21,y:p.y+5,'font-size':15},`C=${event.clock}`));}
}
function showPair(){
  if(!result)return;const row=result.pair_rows[pairIndex];$('pair-title').textContent=`${pairIndex+1}/15 · ${row.left} と ${row.right}`;
  $('previous-pair').disabled=pairIndex===0;$('next-pair').disabled=pairIndex===14;
  const box=$('path-evidence');box.replaceChildren();
  for(const[prefix,label]of [['causal','入力の因果辺'],['rule','比較規則']]){
    const p=document.createElement('p');const path=row[prefix+'_path'];p.textContent=`${label}：${path.length?path.join(' → '):'両方向に経路なし'}`;box.append(p);
    for(const e of row[prefix+'_path_edges']){const line=document.createElement('p');line.className='small';line.textContent=`${e.from} → ${e.to}：`+e.sources.map(s=>`${s.kind} (${s.source})`).join(' / ');box.append(line);}
  }
  [...$('comparison').querySelectorAll('tbody tr')].forEach((tr,i)=>tr.classList.toggle('selected',i===pairIndex));draw();
}
function show(){
  $('result').hidden=false;$('result-title').textContent=names[ids.indexOf(result.case_id)];
  $('result-summary').textContent=`比較規則の判定：因果 ${result.predicted_causal_count} 組 / 並行 ${result.predicted_concurrent_count} 組。入力の因果関係は11組・並行4組。誤って加えた向き ${result.false_positive_pairs.length} 組。`;
  $('replay').textContent=`再生 ${result.replay_id}：${result.replay.join(' → ')} / 時計：${result.replay_clock_labels.join(' → ')}。これは固定時計の昇順ではなく、入力の因果辺を保つ表示順です。`;
  const body=$('comparison').querySelector('tbody');body.replaceChildren();for(const row of result.pair_rows){const tr=document.createElement('tr');tr.className=row.matches?'':'mismatch';for(const value of [`${row.left} / ${row.right}`,words[row.causal_relation],words[row.predicted_relation],row.matches?'一致':'誤認']){const td=document.createElement('td');td.textContent=value;tr.append(td);}body.append(tr);}
  $('raw').textContent=JSON.stringify(result,null,2);$('answer-button').disabled=false;showPair();
}
async function read(){
  if(!$('prediction').value.trim()){$('message').textContent='先に予想を書いてください。';return;}
  invalidate('保存した計算結果を確認しています…');const token=generation;const choice=selected();aborter=new AbortController();$('read-button').disabled=true;
  try{
    const response=await fetch('bundle.json',{signal:aborter.signal,cache:'no-store'});if(!response.ok)throw Error(`資料取得 HTTP ${response.status}`);
    const text=await response.text();if(await hash(text)!==BUNDLE_SHA)throw Error('保存資料のdigestが一致しません');const bundle=JSON.parse(text);
    if(bundle.run_text===null)throw Error('表示できる完了済みの測定結果がありません。状態記録と手表を確認してください');
    for(const key of ['run','expected','fixture'])if(await hash(bundle[key+'_text'])!==bundle.hashes[key])throw Error(`${key}のdigest不一致`);
    const run=JSON.parse(bundle.run_text);if(run.collection_complete!==true||run.errors.length||run.target_count!==1)throw Error('完了した計算結果ではありません');
    const rows=run.records.filter(x=>x.kind==='case-result').map(x=>x.result);if(rows.length!==4)throw Error('4条件の記録が揃っていません');const chosen=rows.find(x=>x.case_id===choice);
    if(!chosen||chosen.pair_rows.length!==15||chosen.clock_labels.c!==4)throw Error('固定記録の形が不正です');
    if(token!==generation)return;result=chosen;pairIndex=0;show();$('message').textContent='保存した合成計算を表示しました。新たな実通信・再計算はしていません。';
  }catch(error){if(token!==generation)return;result=null;$('result').hidden=true;$('answer').hidden=true;$('answer-button').disabled=true;$('message').className='error';$('message').textContent=`資料を表示できません：${error.message}。この取得失敗は因果の誤モデルや計算成功を意味しません。`;}
  finally{if(token===generation){$('read-button').disabled=false;aborter=null;}}
}
$('read-button').addEventListener('click',read);$('prediction').addEventListener('input',()=>invalidate());
document.querySelectorAll('input[name=case]').forEach(r=>r.addEventListener('change',()=>{$('prediction').value='';invalidate();}));
$('previous-case').addEventListener('click',()=>choose(ids.indexOf(selected())-1));$('next-case').addEventListener('click',()=>choose(ids.indexOf(selected())+1));
$('reset-button').addEventListener('click',()=>{document.querySelector('input[value="causal-r1"]').checked=true;$('prediction').value='';invalidate('初期状態に戻しました。');});
for(const[id,delta]of [['previous-pair',-1],['next-pair',1]])$(id).addEventListener('click',()=>{if(!result)return;pairIndex+=delta;$('answer').hidden=true;$('answer').textContent='';showPair();});
$('answer-button').addEventListener('click',()=>{if(!result)return;const errors=result.false_positive_pairs.map(p=>p.join(' → ')).join('、')||'なし';$('answer').hidden=false;$('answer').textContent=`${names[ids.indexOf(result.case_id)]}：因果11組と並行4組が固定入力の手期待です。今回の規則が誤って加えた向きは ${errors}。${result.classification==='matches-causal-relation'?'表示用の合法な再生順を変えても、この関係は変わりません。':'計算は正常に終了していますが、この推論規則は因果関係を正しく分類しません。'} R1のb2→d1、R2のf3→b2という表示上の減少も合法です。同じ時計は同じ物理時刻を意味しません。`;});
window.addEventListener('resize',()=>{if(result)draw();});caseButtons();

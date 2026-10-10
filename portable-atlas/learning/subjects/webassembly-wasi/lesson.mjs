import {runCase} from './experiment.mjs';import {stackModel} from './oracle.mjs';
const $=id=>document.getElementById(id);
try{
  const [cases,binding]=await Promise.all([fetch('cases.json').then(r=>r.json()),fetch('sources.json').then(r=>r.json())]);
  for(const c of cases){const o=document.createElement('option');o.value=c.id;o.textContent=c.label;$('case').append(o);}$('case').value='max-wrap';
  const show=()=>{$('input').textContent=JSON.stringify(cases.find(c=>c.id===$('case').value));};show();$('case').addEventListener('change',show);
  async function run(all){
    $('run').disabled=$('all').disabled=true;const started=new Date().toISOString(),selected=all?cases:cases.filter(c=>c.id===$('case').value),prediction=$('prediction').value;
    try{
      const results=[];for(const c of selected)results.push(await runCase(c));$('rows').replaceChildren();
      for(const r of results){const tr=document.createElement('tr');if(r.error||r.result!==r.jsNumberSum)tr.className='difference';for(const value of [r.id,r.byteLength,r.validated?'許可':'拒否',r.stage,r.result??'—',r.jsNumberSum??'—',r.error?.name??'なし']){const td=document.createElement('td');td.textContent=String(value);tr.append(td);}$('rows').append(tr);}
      const rejected=results.filter(r=>r.error).length,different=results.filter(r=>!r.error&&r.result!==r.jsNumberSum).length;
      $('answer').textContent=all?`${results.length}件：成功${results.length-rejected}、拒否${rejected}、成功中のJS Number差${different}。`:`予想「${{same:'同じ',different:'異なる',reject:'拒否'}[prediction]}」／観測「${results[0].error?'拒否 '+results[0].error.name:different?'異なる':'同じ'}」。`;
      const model=selected.length===1?stackModel(selected[0]):null;$('stack').replaceChildren();if(model)for(const step of model.steps){const box=document.createElement('div'),label=document.createElement('b'),values=document.createElement('span');label.textContent=step.instruction;values.textContent='['+step.stack.join(', ')+']';box.append(label,values);$('stack').append(box);}else $('stack').textContent=all?'説明図は正常入力を1件選ぶと表示します。':'この異常入力は正常加算stackの説明対象ではありません。';
      $('bytes').textContent=selected.length===1?`実byte SHA-256 ${results[0].bytesDigest} / ${results[0].byteLength}byte`:'byte digestは各実行のrawへ保存。';
      $('raw').textContent=JSON.stringify({kind:'actual-browser-webassembly',started,completed:new Date().toISOString(),action:all?'all':'selected',prediction,attempt:1,retries:0,environment:{userAgent:navigator.userAgent,language:navigator.language,viewport:{width:innerWidth,height:innerHeight}},sourceHashes:binding.sourceHashes,inputDigest:binding.sourceHashes['cases.json'],results,stackModel:model},null,2);$('status').textContent=`実行完了：${results.length}入力`;
    }catch(e){$('status').textContent='教材の実行失敗：'+e.message;}
    finally{$('run').disabled=$('all').disabled=false;}
  }
  $('run').addEventListener('click',()=>run(false));$('all').addEventListener('click',()=>run(true));$('run').disabled=$('all').disabled=false;$('status').textContent='準備完了：入力を選んで実行してください';
}catch(e){$('status').textContent='読み込み失敗：'+e.message;}

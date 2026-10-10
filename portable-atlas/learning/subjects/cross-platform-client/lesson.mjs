import {validate} from './validator.mjs';
const $=id=>document.getElementById(id),hex=async bytes=>Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256',bytes)),b=>b.toString(16).padStart(2,'0')).join('');
try {
  const [vectors,binding,pythonText]=await Promise.all([fetch('vectors.json').then(r=>r.json()),fetch('sources.json').then(r=>r.json()),fetch('python.json').then(r=>r.text())]);
  const python=JSON.parse(pythonText),pythonDigest=await hex(new TextEncoder().encode(pythonText));
  if(JSON.stringify(python.sourceHashes)!==JSON.stringify(binding.sourceHashes)||python.inputDigest!==binding.sourceHashes['vectors.json']) throw Error('Python Source binding is stale');
  for(const v of vectors){const o=document.createElement('option');o.value=v.id;o.textContent=v.label;$('vector').append(o);}
  const showInput=()=>{$('input').textContent=JSON.stringify(vectors.find(v=>v.id===$('vector').value).input);};
  $('vector').value='emoji-three';showInput();$('vector').addEventListener('change',showInput);
  $('runtime').textContent=`Python ${python.environment.version} (${python.environment.system}) 実run ${python.started}。画面でPythonを再実行していません。`;
  function run(all){
    const started=new Date().toISOString(),selected=all?vectors:vectors.filter(v=>v.id===$('vector').value),prediction=$('prediction').value;
    const results=selected.map(v=>({id:v.id,input:v.input,result:validate(v.input),pythonResult:python.results.find(p=>p.id===v.id).result}));
    $('rows').replaceChildren();
    for(const v of results){const r=v.result,p=v.pythonResult,tr=document.createElement('tr');if(r.legacyAccepted!==p.legacyAccepted)tr.className='difference';for(const value of [v.id,r.utf16Units??'拒否',r.codePoints??'拒否',r.utf8Bytes??'拒否',r.legacyAccepted?'許可':'拒否',p.legacyAccepted?'許可':'拒否',`${r.codePointAccepted?'許可':'拒否'} / ${p.codePointAccepted?'許可':'拒否'}`,r.byteAccepted?'許可':'拒否']){const td=document.createElement('td');td.textContent=value;tr.append(td);}$('rows').append(tr);}
    const mismatches=results.filter(v=>v.result.legacyAccepted!==v.pythonResult.legacyAccepted).length;
    $('answer').textContent=all?`旧判定の差は${mismatches}件。共有コードポイント契約とbyte契約は別々に比較してください。`:`予想「${prediction==='same'?'一致':'食い違う'}」／観測「${mismatches?'食い違う':'一致'}」。${results[0].result.error?'契約入力として拒否：'+results[0].result.error:'数える単位を選び直すことで共有契約は一致します。'}`;
    const raw={kind:'actual-browser-js-vs-saved-python',started,completed:new Date().toISOString(),environment:{userAgent:navigator.userAgent,language:navigator.language,viewport:{width:innerWidth,height:innerHeight}},action:all?'all':'selected',prediction,sourceHashes:binding.sourceHashes,inputDigest:binding.sourceHashes['vectors.json'],pythonArtifactDigest:pythonDigest,results};
    $('raw').textContent=JSON.stringify(raw,null,2);$('status').textContent=`比較完了：${results.length}入力 / 旧判定差${mismatches}件`;
  }
  $('run').addEventListener('click',()=>run(false));$('all').addEventListener('click',()=>run(true));$('run').disabled=$('all').disabled=false;$('status').textContent='準備完了：固定入力を選んで比較してください';
}catch(e){$('status').textContent='読み込み拒否：'+e.message;}

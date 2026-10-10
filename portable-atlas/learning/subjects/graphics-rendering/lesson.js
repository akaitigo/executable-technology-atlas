'use strict';
(() => {
  const $=id=>document.getElementById(id);
  let run, runSha256, ready=false, loading=false, current, lastSample=null;
  const canvases={depth:document.createElement('canvas'),painter:document.createElement('canvas')};
  const sha=async bytes=>Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256',bytes))).map(n=>n.toString(16).padStart(2,'0')).join('');
  function raw(){ $('raw').textContent=JSON.stringify({at:new Date().toISOString(),kind:'actual-browser-png-decode',environment:{userAgent:navigator.userAgent,width:innerWidth,height:innerHeight,language:navigator.language},ready,loading,caseId:current?.id,runSha256,sourceHashes:run?.sourceHashes,sample:lastSample,feedback:$('feedback').textContent}); }
  function inspect(){
    if(!ready||loading){$('sample-status').textContent='画像の読込完了を待ってください。';return;}
    const x=Number($('x').value),y=Number($('y').value);
    if($('x').value===''||$('y').value===''||!Number.isInteger(x)||!Number.isInteger(y)||x<0||x>=16||y<0||y>=12){$('sample-status').textContent='範囲外: 整数x=0–15、y=0–11を指定してください。';lastSample={rejected:true,input:[$('x').value,$('y').value]};raw();return;}
    lastSample={x,y,caseId:current.id}; let matched=true;
    for(const mode of ['depth','painter']){
      const pixel=current[mode].pixels[y*16+x];
      const rgba=Array.from(canvases[mode].getContext('2d').getImageData(x,y,1,1).data);
      const ok=rgba[3]===255&&pixel.rgb.every((c,i)=>c===rgba[i]); matched=matched&&ok;
      $(mode+'-owner').textContent=pixel.owner||'背景'; $(mode+'-value').textContent=pixel.depthExact||'未設定（∞）'; $(mode+'-rgb').textContent=`${pixel.rgb.join(',')} / ${rgba.slice(0,3).join(',')}`;
      lastSample[mode]={owner:pixel.owner,depthExact:pixel.depthExact,pythonRgb:pixel.rgb,decodedRgba:rgba,matched:ok,fragments:pixel.fragments};
    }
    $('sample-status').textContent=`(${x},${y}) 中心(${x+0.5},${y+0.5}): Python出力とBrowser decodeは${matched?'一致':'不一致'}`;
    $('trace').textContent=JSON.stringify(lastSample,null,2);raw();
  }
  async function select(){
    current=run.results.find(r=>r.id===$('scene').value); loading=true;lastSample=null;raw();
    await Promise.all(['depth','painter'].map(async mode=>{
      const url=`observations/cpu-attempt-01/${current.id}-${mode}.png`;
      const bytes=await (await fetch(url)).arrayBuffer();
      if(await sha(bytes)!==run.artifacts[`${current.id}-${mode}.png`].sha256)throw Error('PNG digest不一致');
      const image=$(mode+'-image');await new Promise((resolve,reject)=>{image.onload=resolve;image.onerror=reject;image.src=url;});
      const canvas=canvases[mode];canvas.width=16;canvas.height=12;canvas.getContext('2d').drawImage(image,0,0);
    }));
    loading=false;$('status').textContent=`Python実行原票: ${run.environment.implementation} ${run.environment.python} / ${current.label}`;
    $('comparison').textContent=`所属面が異なるpixel: ${current.differenceCount} / 192。退化triangle: ${current.depth.degenerateTriangles.join(',')||'なし'}。`;
    inspect();
  }
  async function init(){
    const bytes=await (await fetch('observations/cpu-attempt-01/run.json')).arrayBuffer();runSha256=await sha(bytes);run=JSON.parse(new TextDecoder().decode(bytes));
    for(const file of ['index.html','lesson.js','raster.py']){const source=await (await fetch(file)).arrayBuffer();if(await sha(source)!==run.sourceHashes[file])throw Error(`Source digest不一致: ${file}`);}
    $('implementation').textContent=await (await fetch('raster.py')).text();
    $('scene').replaceChildren(...run.results.map(r=>{const o=document.createElement('option');o.value=r.id;o.textContent=r.label;return o;}));
    $('scene').disabled=false;ready=true;await select();
  }
  $('scene').addEventListener('change',()=>select().catch(fail)); $('sample').addEventListener('click',inspect);
  $('predict').addEventListener('click',()=>{$('prediction-feedback').textContent=$('prediction').value?'予想を保存。描画順を切り替えて比べよう。':'先に予想を選んでください。';raw();});
  $('check-answer').addEventListener('click',()=>{$('feedback').textContent=({order:'不足。面が交差すると、場所によって手前が変わる。一つの順序では両方を表せない。',depth:'適切。pixelごとの比較で手前を選ぶ。同depthは別のtie規則が必要。',gpu:'未検証。これはCPU screen-space教材で、GPU/clip/照明の保証にはならない。'})[$('answer').value]||'回答を選んでください。';raw();});
  function fail(e){ready=false;loading=false;$('status').textContent='読込失敗: '+String(e);raw();}
  init().catch(fail);
})();

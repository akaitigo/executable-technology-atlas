(function(){
  'use strict';
  const S=globalThis.ATLAS_STATE, D=globalThis.ATLAS_DATA, E=globalThis.ATLAS_EXPECTED;
  const $=id=>document.getElementById(id), ns='http://www.w3.org/2000/svg';
  let state=S.initial();
  const names={'edge-low':'斜辺 x+y=2','edge-high':'斜辺 x+y=5/2','overlap-ab':'手前A → 奥B','overlap-ba':'奥B → 手前A','shared-edge':'共有辺 A → C'};
  const notes={'edge-low':'Aは赤、深度1/2。斜辺上はAに含めません。',
    'edge-high':'Aの斜辺だけを移動します。赤、深度1/2は同じです。',
    'overlap-ab':'Aは赤・深度1/4、Bは青・深度3/4。Bは固定sampleを全て覆います。',
    'overlap-ba':'同じAとBの描画順だけを反転します。',
    'shared-edge':'AとCは赤と青、深度は両方1/2。共有辺上はCだけに含めます。'};
  const modeNames={normal:'正常な記録',missing:'欠落',altered:'改変',old:'別条件の記録'};
  const layoutNames={center:'中心1点',four:'固定4点'};
  function element(tag,text,cls){const n=document.createElement(tag);if(text!==undefined)n.textContent=text;if(cls)n.className=cls;return n;}
  function vector(v){return '('+v.join(', ')+')';}
  function fraction(v){const [a,b]=v.split('/').map(Number);return a/(b===undefined?1:b);}
  function cssColor(rgb){return 'rgb('+rgb.map(v=>Math.round(255*fraction(v))).join(',')+')';}
  function winner(v){return v===null?'背景':v;}
  function supplied(){
    if(state.mode==='missing')return null;
    if(!D)return D;
    if(state.mode==='normal')return D;
    const copy=JSON.parse(JSON.stringify(D));
    if(state.mode==='altered')copy.result.results[0].pixels[0].stages[0].resolved_rgb=['1','0','0'];
    if(state.mode==='old')copy.result.results[0].scene_id='previous-condition';
    return copy;
  }
  function send(event){state=S.transition(state,event,supplied(),E);render();}
  for(const id of S.scenes){const b=element('button',names[id]);b.dataset.scene=id;b.addEventListener('click',()=>send({type:'scene',value:id}));$('scenes').append(b);}
  [[0,0],[1,0],[0,1],[1,1]].forEach((p,i)=>{const b=element('button',vector(p));b.dataset.pixel=String(i);b.addEventListener('click',()=>send({type:'pixel',value:i}));$('pixels').append(b);});
  for(const [layout,count,key] of [['center',1,'centerPrediction'],['four',4,'fourPrediction']]){
    for(let i=0;i<=count;i++){const label=element('label');const input=document.createElement('input');input.type='radio';input.name=key;input.value=String(i);input.addEventListener('change',()=>send({type:'prediction',key,value:input.value}));label.append(input,document.createTextNode(i+'点'));$('prediction-'+layout).append(label);}
  }
  for(const mode of S.modes){const label=element('label');const input=document.createElement('input');input.type='radio';input.name='record-mode';input.value=mode;input.addEventListener('change',()=>send({type:'mode',value:mode}));label.append(input,document.createTextNode(modeNames[mode]));$('modes').append(label);}
  $('load').addEventListener('click',()=>send({type:'load'}));
  $('reset').addEventListener('click',()=>send({type:'reset'}));
  $('previous').addEventListener('click',()=>send({type:'step',value:state.step-1}));
  $('next').addEventListener('click',()=>send({type:'step',value:state.step+1}));
  $('answer-button').addEventListener('click',()=>send({type:'answer'}));
  function cells(body,values,attributes){const tr=document.createElement('tr');values.forEach(v=>tr.append(element('td',v)));for(const [k,v] of Object.entries(attributes||{}))tr.dataset[k]=String(v);$(body).append(tr);}
  function stat(dl,label,value){$(dl).append(element('dt',label),element('dd',value));}
  function svgEl(tag,attrs,text){const n=document.createElementNS(ns,tag);for(const [k,v] of Object.entries(attrs))n.setAttribute(k,v);if(text!==undefined)n.textContent=text;return n;}
  function plot(layout,result,scene){
    const svg=$(layout+'-diagram'), clip='clip-'+layout, scale=120, x0=30,y0=25;
    const defs=svgEl('defs',{}), cp=svgEl('clipPath',{id:clip});cp.append(svgEl('rect',{x:x0,y:y0,width:240,height:240}));defs.append(cp);svg.append(defs);
    svg.append(svgEl('rect',{x:x0,y:y0,width:240,height:240,fill:'#f5f6f3',stroke:'#687d83'}));
    const group=svgEl('g',{'clip-path':'url(#'+clip+')'});
    for(const face of scene.triangles){group.append(svgEl('polygon',{points:face.vertices.map(p=>(x0+scale*fraction(p[0]))+','+(y0+scale*fraction(p[1]))).join(' '),fill:face.id==='A'?'#cf4b45':'#3074bd','fill-opacity':'.07',stroke:face.id==='A'?'#ba3b32':'#1e5c9f','stroke-width':'2','data-face':face.id}));}
    svg.append(group);
    svg.append(svgEl('line',{x1:x0+120,y1:y0,x2:x0+120,y2:y0+240,stroke:'#a5b4b8'}),svgEl('line',{x1:x0,y1:y0+120,x2:x0+240,y2:y0+120,stroke:'#a5b4b8'}));
    result.pixels.forEach((p,pi)=>{
      const [x,y]=p.pixel, snapshot=p.stages[state.step];
      if(pi===state.pixel)svg.append(svgEl('rect',{x:x0+x*120+2,y:y0+y*120+2,width:116,height:116,fill:'none',stroke:'#238454','stroke-width':3}));
      svg.append(svgEl('text',{x:x0+x*120+60,y:y0+y*120+17,'text-anchor':'middle',class:'grid-label'},vector(p.pixel)));
      snapshot.samples.forEach(s=>{
        const cx=x0+scale*fraction(s.position[0]),cy=y0+scale*fraction(s.position[1]);
        svg.append(svgEl('circle',{cx,cy,r:7,fill:s.winner==='A'?'#bd3d32':s.winner===null?'#d0dbdf':'#245e9d',stroke:'#243d46','data-sample-key':pi+':'+s.sample_index,'data-winner':s.winner===null?'background':s.winner,'data-depth':s.depth}));
        svg.append(svgEl('text',{x:cx+10,y:cy+4,class:'sample-label'},String(s.sample_index+1)));
      });
    });
    svg.append(svgEl('text',{x:30,y:284,class:'grid-label'},'緑枠：選択pixel　点：その段階の可視面'));
  }
  function render(){
    for(const id of ['provenance','stage-label','center-stats','four-stats','center-diagram','four-diagram','center-swatches','four-swatches','sample-rows','pixel-rows','trace-rows','raw','answer','error'])$(id).replaceChildren();
    $('raw-details').open=false;$('result').hidden=true;
    for(const name of ['scene','pixel','step'])delete $('result').dataset[name];
    $('condition-note').textContent=notes[state.scene];
    document.querySelectorAll('#scenes button').forEach(b=>b.setAttribute('aria-pressed',String(b.dataset.scene===state.scene)));
    document.querySelectorAll('#pixels button').forEach(b=>b.setAttribute('aria-pressed',String(Number(b.dataset.pixel)===state.pixel)));
    for(const key of ['centerPrediction','fourPrediction'])document.querySelectorAll('input[name='+key+']').forEach(i=>i.checked=i.value===state[key]);
    document.querySelectorAll('input[name=record-mode]').forEach(i=>i.checked=i.value===state.mode);
    $('error').textContent=state.error;
    if(!state.shown)return;
    $('result').hidden=false;Object.assign($('result').dataset,{scene:state.scene,pixel:String(state.pixel),step:String(state.step)});
    $('provenance').textContent='保存計算 '+D.observed_at_utc+' / '+D.run_id+' / SHA-256 '+D.result_sha256;
    const scene=D.fixture.scenes.find(s=>s.id===state.scene), last=scene.triangles.length;
    $('stage-label').textContent=state.step===0?'描画前':state.step+' / '+last+'：'+scene.triangles[state.step-1].id+'の描画後';
    $('previous').disabled=state.step===0;$('next').disabled=state.step===last;
    for(const result of state.shown){
      const layout=result.layout_id, p=result.pixels[state.pixel], snapshot=p.stages[state.step];
      const draw=state.step===0?null:p.draws[state.step-1];
      stat(layout+'-stats','選択pixel',vector(p.pixel));stat(layout+'-stats','描画段階',String(state.step));
      stat(layout+'-stats','今回の所属mask',draw?draw.coverage_mask:'描画前');stat(layout+'-stats','今回の採用mask',draw?draw.accepted_mask:'描画前');
      stat(layout+'-stats','集約RGB',vector(snapshot.resolved_rgb));stat(layout+'-stats','平均の分母',String(snapshot.samples.length));
      plot(layout,result,scene);
      snapshot.samples.forEach((sample,i)=>{
        const event=draw?draw.events[i]:null;
        cells('sample-rows',[layoutNames[layout]+' / '+(i+1),vector(sample.position),event?(event.covered?'所属':'非所属'):'描画前',event&&event.tested_depth!==null?event.tested_depth:'未到達',!event||event.accepted===null?'未到達':event.accepted?'採用':'拒否',winner(sample.winner),sample.depth,vector(sample.rgb)],{layout,sample:i});
      });
      for(const full of result.pixels){
        const snap=full.stages[state.step];
        cells('pixel-rows',[layoutNames[layout],vector(full.pixel),snap.samples.map(s=>winner(s.winner)).join(' / '),snap.samples.map(s=>s.depth).join(' / '),vector(snap.resolved_rgb)],{layout,pixel:full.pixel.join(',')});
        const box=element('div',undefined,'swatch'), chip=element('div',undefined,'color-chip');chip.style.backgroundColor=cssColor(snap.resolved_rgb);box.append(chip,element('div',vector(full.pixel)+' '+vector(snap.resolved_rgb)));$(layout+'-swatches').append(box);
      }
      for(const d of p.draws)cells('trace-rows',[layoutNames[layout],String(d.step),d.triangle_id,d.coverage_mask,d.accepted_mask,d.events.map(e=>e.accepted===null?'未到達':e.accepted?'採用':'拒否').join(' / ')],{layout,step:d.step});
    }
    $('raw').textContent=JSON.stringify({scene:state.scene,pixel:state.pixel,step:state.step,selected:state.shown.map(r=>({layout:r.layout_id,pixel:r.pixels[state.pixel]}))},null,2);
    if(state.answer){
      const counts=state.shown.map(r=>r.pixels[state.pixel].stages.at(-1).samples.filter(s=>s.winner==='A').length);
      const correct=String(counts[0])===state.centerPrediction&&String(counts[1])===state.fourPrediction;
      $('answer').append(element('strong',correct?'両方の予想が一致しました。':'予想と違う配置があります。'));
      $('answer').append(element('p','最終的にAが残るのは、中心1点で'+counts[0]+'点、固定4点で'+counts[1]+'点です。ここでは選択中の途中段階ではなく、全描画後と比べています。'));
      $('answer').append(element('p',state.scene==='shared-edge'?'共有辺ではAとCの所属を分けます。同じ最終色の重なり条件でも、深度で拒否する経路とは異なります。':state.scene.startsWith('overlap')?'各sampleで手前のAを残すので、この固定2面の最終結果は描画順を変えても一致します。色を平均しても、深度を平均したわけではありません。':'背景も分母に含めます。この点の所属率は、幾何学的な面積率や実GPUの品質を表すものではありません。'));
    }
  }
  render();
})();

(function () {
  'use strict';
  const S=window.AtlasMeasurementState,D=window.ATLAS_MEASUREMENT_DATA,E=window.ATLAS_MEASUREMENT_EXPECTED;
  let state=S.initial();
  const $=id=>document.getElementById(id);
  const descriptions={
    'current-exact':'現在値をそのまま測定に使います。雑音0、丸めなし。',
    'delayed-one':'1標本前の状態を使います。初期履歴x[−1]=0、雑音0、丸めなし。',
    'fixed-noise':'現在値へ +1/4,−1/4,… の固定雑音を加えます。状態そのものへ加える外乱とは別です。',
    'quantized-unit':'現在値を最寄り整数へ丸めます。+1/2→1、−1/2→−1。雑音0。'
  };
  const labels=[['true_state','真の状態x'],['source_index','参照する標本番号'],['source_value','参照する状態の値'],['noise','測定へ加える雑音'],['before_quantization','丸める前の値'],['measurement','制御器が見た測定m'],['measurement_error','測定と現在の差 m−x'],['true_error','目標と真の状態の偏差 1−x'],['control_error','制御器の偏差 1−m'],['control_input','計算した入力u'],['input_applied','この入力を適用したか'],['next_state','この入力による次の状態']];
  const display=(v,key)=>key==='source_index'&&v===-1?'-1（初期履歴）':v===null?'未適用・次の状態なし':typeof v==='boolean'?(v?'適用済み':'未適用'):String(v);
  const text=(tag,value)=>{const e=document.createElement(tag);e.textContent=value;return e;};
  const numeric=v=>{const [a,b]=String(v).split('/').map(Number);return a/(b||1);};
  function svg(tag,attrs,value){const e=document.createElementNS('http://www.w3.org/2000/svg',tag);for(const[k,v]of Object.entries(attrs))e.setAttribute(k,v);if(value!==undefined)e.textContent=value;$('timeline').append(e);return e;}
  function draw(rows){
    const px=k=>70+k*100,py=v=>220-160*numeric(v);
    for(const v of ['0','1/2','1']){svg('line',{x1:70,x2:670,y1:py(v),y2:py(v),stroke:'#d5ddd8'});svg('text',{x:22,y:py(v)+5,'font-size':16,fill:'#324650'},v);}
    for(let k=0;k<=6;k++)svg('text',{x:px(k)-5,y:245,'font-size':16,fill:'#324650'},String(k));
    svg('text',{x:70,y:270,'font-size':15,fill:'#324650'},'標本番号 k / 架空の無次元値');
    svg('line',{x1:px(state.step),x2:px(state.step),y1:40,y2:223,stroke:'#b34726','stroke-width':2,'data-selected':state.step});
    for(const [field,color,label] of [['true_state','#267493','x'],['measurement','#b16419','m'],['control_input','#387247','u']]){
      for(let k=0;k<6;k++)svg('line',{x1:px(k),x2:px(k+1),y1:py(rows[k][field]),y2:py(rows[k+1][field]),stroke:color,'stroke-width':2,'stroke-dasharray':field==='control_input'&&k===5?'6 4':'none','data-series':field,'data-from':k,'data-to':k+1});
      for(const row of rows)svg('circle',{cx:px(row.k),cy:py(row[field]),r:4,fill:field==='control_input'&&row.k===6?'white':color,stroke:color,'stroke-width':2,'data-series':field,'data-k':row.k,'data-value':row[field],'data-input-applied':row.input_applied});
      svg('text',{x:90+['x','m','u'].indexOf(label)*150,y:26,fill:color,'font-size':18},label+(label==='u'?'（最後は未適用）':''));
    }
  }
  function render(){
    for(const id of ['cards','rows','quantization','timeline','raw','answer-text','provenance','boundary-note','step-value'])$(id).textContent='';
    $('raw-details').open=false;$('result').hidden=!state.shown;$('result').dataset.caseId=state.shown?state.caseId:'';$('answer-text').hidden=true;$('answer').disabled=!state.shown;
    $('error').textContent=state.error;$('case-description').textContent=descriptions[state.caseId];
    document.querySelectorAll('[data-case]').forEach(b=>b.setAttribute('aria-pressed',String(b.dataset.case===state.caseId)));
    document.querySelectorAll('[data-mode]').forEach(b=>b.setAttribute('aria-pressed',String(b.dataset.mode===state.mode)));
    document.querySelectorAll('[name=prediction]').forEach(e=>e.checked=e.value===state.prediction);
    document.querySelectorAll('[name=terminal]').forEach(e=>e.checked=e.value===state.terminalPrediction);
    $('prev').disabled=!state.shown||state.step===0;$('next').disabled=!state.shown||state.step===6;$('step').value=state.step;
    if(!state.shown)return;
    $('step-value').textContent='k='+state.step;
    const point=state.shown.boundaries[state.step];
    $('provenance').textContent='保存した計算：'+D.result.observed_at_utc+' / 実行識別：'+D.run_id+' / 結果SHA-256：'+D.result_sha256;
    $('boundary-note').textContent=point.input_applied?'この境界で測定から入力を決め、次の状態へ適用しました。参照番号と現在のkを比べてください。':'終端k=6です。測定と入力は計算しましたが、新しい区間へ適用していません。次の状態はnullです。';
    for(const[field,label]of labels){const card=text('div','');card.className='card';card.dataset.field=field;card.dataset.value=JSON.stringify(point[field]);card.append(text('span',label),text('b',display(point[field],field)));$('cards').append(card);}
    const fields=['k',...labels.map(x=>x[0])];
    for(const row of state.shown.boundaries){const tr=document.createElement('tr');tr.dataset.k=row.k;for(const f of fields){const td=text('td',display(row[f],f));td.dataset.field=f;td.dataset.value=JSON.stringify(row[f]);tr.append(td);}$('rows').append(tr);}
    for(const q of D.result.quantization_cases){const tr=document.createElement('tr');tr.append(text('td',q.input),text('td',q.output));$('quantization').append(tr);}
    draw(state.shown.boundaries);
    $('raw').textContent=JSON.stringify({run_id:D.run_id,selected_boundary:point,whole_case:state.shown,quantization_cases:D.result.quantization_cases},null,2);
    if(state.answer){
      const relation={'current-exact':'equal','delayed-one':'below','fixed-noise':'below','quantized-unit':'above'}[state.caseId],name={equal:'同じ',below:'小さい',above:'大きい'}[relation];
      const agrees=state.prediction===relation&&state.terminalPrediction==='unapplied';
      const p=state.shown.boundaries[1];
      const notes={'current-exact':'雑音がなくても、真の状態は1/2で目標1への偏差1/2が残ります。','delayed-one':'k=1でも参照するのはk=0の状態です。雑音0と測定誤差0は同じではありません。','fixed-noise':'k=1では雑音−1/4を測定だけへ加えます。真の状態を上書きせず、変わった入力が次の状態へ効きます。','quantized-unit':'k=1の真の状態1/2を1へ丸め、入力が0になります。真の状態の次値は1/4です。'};
      $('answer-text').textContent=(agrees?'予想は2つとも一致しました。':'予想と比べ直してください。')+' k=1の測定'+p.measurement+'は真の状態'+p.true_state+(relation==='equal'?'と同じ':'より'+name)+'です。入力は'+p.control_input+'、次の状態は'+p.next_state+'。'+notes[state.caseId]+' 終端k=6の入力は未適用で、7回目の更新はありません。現在選んだ境界はk='+state.step+'です。';$('answer-text').hidden=false;
    }
  }
  function send(type,value){state=S.transition(state,{type,value},D,E);render();}
  document.querySelectorAll('[data-case]').forEach(b=>b.addEventListener('click',()=>send('case',b.dataset.case)));
  document.querySelectorAll('[data-mode]').forEach(b=>b.addEventListener('click',()=>send('mode',b.dataset.mode)));
  document.querySelectorAll('[name=prediction]').forEach(e=>e.addEventListener('change',()=>send('prediction',e.value)));
  document.querySelectorAll('[name=terminal]').forEach(e=>e.addEventListener('change',()=>send('terminalPrediction',e.value)));
  $('load').addEventListener('click',()=>send('load'));$('reset').addEventListener('click',()=>send('reset'));$('answer').addEventListener('click',()=>send('answer'));
  $('prev').addEventListener('click',()=>send('step',state.step-1));$('next').addEventListener('click',()=>send('step',state.step+1));$('step').addEventListener('input',e=>send('step',Number(e.target.value)));render();
})();

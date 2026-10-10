/* Atlas: display saved values; this file never runs the receiver. */
(function(){'use strict';
const S=window.ATLAS_PHASE_STATE,D=window.ATLAS_PHASE_DATA,E=window.ATLAS_PHASE_EXPECTED,$=id=>document.getElementById(id);
let state=S.initial();
const labels={'constant-phase':'位相が一定','constant-rate':'同じ回転が続く','rate-reversal':'途中で回転が反転','first-pilot-missing':'最初のpilotが欠落'};
const descriptions={'constant-phase':'6時点で同じ向き。回転を予測しても、位相を保持しても合う基準条件です。','constant-rate':'毎回 r=(3+4i)/5 だけ回転します。最新の向きをそのまま使ってよいでしょうか。','rate-reversal':'n=3までは同じ回転。その後は逆方向へ変わります。受信側はこの変化を先には知りません。','first-pilot-missing':'n=0の受信pilotだけ0です。n=1の最新pilotとpayloadは同じ回転の条件と同じです。'};
const fmt=x=>x===null?'未推定':Array.isArray(x)?'['+x.join(', ')+']':String(x);
const num=s=>{const v=s.split('/').map(Number);return v.length===1?v[0]:v[0]/v[1];};
function node(tag,text,attrs={}){const x=document.createElement(tag);if(text!==undefined)x.textContent=text;Object.entries(attrs).forEach(([k,v])=>x.setAttribute(k,v));return x;}
function svgNode(tag,attrs={}){const x=document.createElementNS('http://www.w3.org/2000/svg',tag);Object.entries(attrs).forEach(([k,v])=>x.setAttribute(k,v));return x;}
function card(title,value,key){const c=node('div',undefined,{class:'card','data-key':key});c.append(node('span',title),node('b',value));return c;}
function plot(row,method){
 const svg=svgNode('svg',{viewBox:'0 0 280 250',role:'img','aria-label':method+'の選択symbol I/Q','data-plot':method});
 svg.append(svgNode('circle',{cx:140,cy:125,r:85,fill:'none',stroke:'#bac7c0'}),svgNode('line',{x1:35,y1:125,x2:245,y2:125,stroke:'#84998e'}),svgNode('line',{x1:140,y1:20,x2:140,y2:230,stroke:'#84998e'}));
 for(const [text,x,y] of [['I',251,130],['Q',147,20],['−1',36,144],['1',224,144]]){const t=svgNode('text',{x,y,'font-size':14,fill:'#31473c'});t.textContent=text;svg.append(t);}
 for(const [kind,value,color] of [['received',row.received,'#667078'],['corrected',row.corrected,'#187447']]){
  if(value===null)continue;const x=140+num(value[0])*85,y=125-num(value[1])*85;
  svg.append(svgNode('line',{x1:140,y1:125,x2:x,y2:y,stroke:color,'stroke-width':2,'stroke-dasharray':kind==='received'?'4 3':'none'}),svgNode('circle',{cx:x,cy:y,r:kind==='received'?7:4,fill:color,'data-kind':kind,'data-i':value[0],'data-q':value[1]}));
 }
 if(row.corrected===null){const t=svgNode('text',{x:12,y:242,'font-size':14,fill:'#983135'});t.textContent='補正点なし：推定できません';svg.append(t);}return svg;
}
function render(){
 $('case-description').textContent=descriptions[state.id];
 for(const b of document.querySelectorAll('[data-case]'))b.setAttribute('aria-pressed',String(b.dataset.case===state.id));
 for(const i of document.querySelectorAll('input[name=prediction]'))i.checked=i.value===state.prediction;
 for(const b of document.querySelectorAll('[data-mode]'))b.setAttribute('aria-pressed',String(b.dataset.mode===state.mode));
 $('error').textContent=state.error;$('results').hidden=!state.shown;
 for(const id of ['provenance','pilot-cards','selected-label','methods','raw','answer'])$(id).replaceChildren();
 $('raw-details').open=false;$('answer').hidden=true;
 if(!state.shown)return;
 const c=state.shown;$('provenance').textContent='保存日時 '+D.result.observed_at_utc+' · '+D.run_id+' · 計算結果 SHA-256 '+D.result_sha256;
 $('pilot-cards').append(card('n=0 受信pilot I/Q',fmt(c.pilot_z[0]),'pilot-0'),card('n=1 受信pilot I/Q',fmt(c.pilot_z[1]),'pilot-1'));
 $('selected-label').textContent='選択した時点 n='+state.n;$('prev').disabled=state.n===2;$('next').disabled=state.n===5;
 for(const m of c.methods){
  const r=m.receiver,j=state.n-2,row=r.rows[j],a=node('article',undefined,{'data-method':r.method,class:'method'});
  a.append(node('h3',r.method==='hold-latest'?'直近の位相を保持':'2 pilotから外挿'));
  const cards=node('div',undefined,{class:'cards'});
  cards.append(card('処理状態',r.status==='decoded'?'復調した':'推定できない','status'),card('誤り / 比較bit',m.comparison.errors===null?'未比較 / 0':m.comparison.errors+' / '+m.comparison.compared_bits,'error-count'),card('必要なpilot番号',r.required_pilot_indices.join(', '),'required'),card('1区間の回転推定',r.uses_rate?fmt(r.rotation_estimate):'使わない','rotation'));
  a.append(cards,plot(row,r.method));
  const selected=node('dl',undefined,{class:'selected','data-selected':r.method});
  for(const [key,title,value] of [['received','受信 I/Q',fmt(row.received)],['predicted_channel','予測channel',fmt(row.predicted_channel)],['correction_factor','逆回転の係数',fmt(row.correction_factor)],['corrected','補正 I/Q',fmt(row.corrected)],['bit','判定bit',row.bit===null?'未判定':row.bit],['truth','検査用正解bit',m.comparison.truth_bits[j]]])selected.append(node('dt',title),node('dd',String(value),{'data-key':key}));
  a.append(selected,node('p','全4時点の保存結果。表は横にスクロールできます。',{class:'small'}));
  const wrap=node('div',undefined,{class:'table-wrap',tabindex:'0','aria-label':'全時点 '+r.method}),table=node('table',undefined,{'data-table':r.method});
  const head=node('thead'),tr=node('tr');for(const t of ['n','受信 I/Q','予測channel','逆回転係数','補正 I/Q','判定bit','検査用正解','誤り'])tr.append(node('th',t));head.append(tr);table.append(head);
  const body=node('tbody');for(const [k,x] of r.rows.entries()){const tr=node('tr',undefined,{'data-n':x.n});const values=[x.n,fmt(x.received),fmt(x.predicted_channel),fmt(x.correction_factor),fmt(x.corrected),x.bit===null?'未判定':x.bit,m.comparison.truth_bits[k],x.bit===null?'未比較':x.bit===m.comparison.truth_bits[k]?'なし':'あり'];values.forEach(v=>tr.append(node('td',String(v))));body.append(tr);}table.append(body);wrap.append(table);a.append(wrap);$('methods').append(a);
 }
 $('raw').textContent=JSON.stringify(c,null,2);
 if(state.answer){
  const a=c.methods[0].comparison,b=c.methods[1].comparison;const expected=b.errors===null?'unavailable':a.errors===b.errors?'equal':a.errors<b.errors?'hold':'extrapolate';
  const lead=state.prediction===expected?'予想と一致しました。':'予想と違う結果でした。';
  const text=state.id==='constant-phase'?'両方0誤りです。向きが一定なので保持でも外挿でも合います。':state.id==='constant-rate'?'保持は3誤り、外挿は0誤り。一定の回転が続くという前提が、この4時点では合っています。':state.id==='rate-reversal'?'保持は1誤り、外挿は2誤り。2点で見えた回転方向が変わり、外挿が悪化しました。':'保持は3誤り。外挿には最初のpilotが足りず、判定/誤り数はnull、比較0です。0誤りの成功ではありません。';
  $('answer').textContent=lead+' '+text;$('answer').hidden=false;
 }
}
function send(type,value){state=S.transition(state,{type,value},D,E);render();}
for(const b of document.querySelectorAll('[data-case]'))b.addEventListener('click',()=>send('case',b.dataset.case));
for(const b of document.querySelectorAll('[data-mode]'))b.addEventListener('click',()=>send('mode',b.dataset.mode));
for(const i of document.querySelectorAll('input[name=prediction]'))i.addEventListener('change',()=>send('prediction',i.value));
$('load').addEventListener('click',()=>send('load'));$('reset').addEventListener('click',()=>send('reset'));$('answer-button').addEventListener('click',()=>send('answer'));$('prev').addEventListener('click',()=>send('step',state.n-1));$('next').addEventListener('click',()=>send('step',state.n+1));render();
})();

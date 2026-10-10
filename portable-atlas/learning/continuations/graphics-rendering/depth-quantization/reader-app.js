(function(){
 'use strict';
 const S=globalThis.ATLAS_STATE,D=globalThis.ATLAS_DATA,E=globalThis.ATLAS_EXPECTED,$=id=>document.getElementById(id);let state=S.initial();
 const labels={'same-bin-ab':'3bit A→B','same-bin-ba':'3bit B→A','separated-ab':'4bit A→B','separated-ba':'4bit B→A','exact-tie-ab':'3bit 真の同値 A→B','exact-tie-ba':'3bit 真の同値 B→A'};
 const boundaryNames={'zero':'0','half-before':'49/100','half':'1/2','half-after':'51/100','clear-bin':'31/32','one':'1'};
 const name=id=>labels[id]||id.slice(1,2)+'bit z='+boundaryNames[id.slice(3)];
 const face=x=>x===null?'背景':x,number=s=>{const [a,b='1']=s.split('/');return Number(a)/Number(b);};
 const text=(tag,content)=>{const el=document.createElement(tag);el.textContent=content;return el;};
 function act(event){state=S.transition(state,event,D,E);render();}
 function radios(container,name,options,callback){for(const [value,label] of options){const l=document.createElement('label'),i=document.createElement('input');i.type='radio';i.name=name;i.value=value;i.addEventListener('change',()=>callback(value));l.append(i,document.createTextNode(label));$(container).append(l);}}
 for(const group of ['central','boundaries'])for(const id of S[group]){const b=text('button',name(id));b.dataset.caseId=id;b.onclick=()=>act({type:'case',value:id});$(group==='central'?'central-options':'boundary-options').append(b);}
 const opts=[['A','A'],['B','B'],['F','境界の面F'],['background','背景']];
 radios('exact-prediction','exact',opts,v=>act({type:'prediction',key:'exactPrediction',value:v}));radios('quantized-prediction','quantized',opts,v=>act({type:'prediction',key:'quantizedPrediction',value:v}));
 radios('record-options','record',[['normal','正常記録'],['missing','欠落'],['altered','保存値を変更'],['old','別の由来']],v=>act({type:'mode',value:v}));
 $('load').onclick=()=>{let value=D===null?null:JSON.parse(JSON.stringify(D));if(state.mode==='missing')value=null;if(value&&state.mode==='altered')value.result.central[0].trace[0].code=2;if(value&&state.mode==='old')value.run_id='another-saved-run';state=S.transition(state,{type:'load'},value,E);render();};
 $('reset').onclick=()=>act({type:'reset'});$('previous').onclick=()=>act({type:'step',value:state.step-1});$('next').onclick=()=>act({type:'step',value:state.step+1});$('answer-button').onclick=()=>act({type:'answer'});
 function table(body,rows){for(const values of rows){const tr=document.createElement('tr');for(const value of values)tr.append(text('td',String(value)));$(body).append(tr);}}
 function svg(tag,attrs,content){const el=document.createElementNS('http://www.w3.org/2000/svg',tag);for(const [k,v] of Object.entries(attrs))el.setAttribute(k,v);if(content!==undefined)el.textContent=content;$('diagram').append(el);return el;}
 function diagram(c){
  for(const [y,title] of [[70,'元の奥行き z'],[160,'再構成値 Q/M']]){svg('text',{x:18,y:y-34},title);svg('line',{x1:150,x2:710,y1:y,y2:y,stroke:'#4b655b','stroke-width':2});for(const [z,label] of [[0,'0'],[.5,'1/2'],[1,'1']]){const x=150+560*z;svg('line',{x1:x,x2:x,y1:y-5,y2:y+5,stroke:'#4b655b'});svg('text',{x,y:y+28,'text-anchor':'middle'},label);}}
  for(let q=0;q<=c.maximum;q++){const x=150+560*q/c.maximum;svg('line',{x1:x,x2:x,y1:153,y2:167,stroke:'#9cb3a4'});}
  c.trace.slice(0,state.step).forEach((r,i)=>{const color={A:'#1f5e91',B:'#a74f1d',F:'#226b4c'}[r.fragment_id];for(const [key,y] of [['z',70],['reconstructed',160]]){const x=150+560*number(r[key]);svg('circle',{cx:x,cy:y,r:7,fill:color,'data-step':r.step,'data-kind':key,'data-value':r[key]});svg('text',{x:x+(i===0?-8:8),y:y-14-i*20,'text-anchor':i===0?'end':'start'},r.fragment_id+' '+r[key]);}});
 }
 function render(){
  for(const id of ['cards','trace-rows','boundary-rows','diagram','raw-json','provenance','step-label','answer','error'])$(id).textContent='';$('raw').open=false;$('results').hidden=!state.shown;$('answer-button').disabled=!state.shown;$('error').textContent=state.error;
  document.querySelectorAll('[data-case-id]').forEach(b=>b.setAttribute('aria-pressed',String(b.dataset.caseId===state.caseId)));
  for(const [n,k] of [['exact','exactPrediction'],['quantized','quantizedPrediction'],['record','mode']])document.querySelectorAll('input[name='+n+']').forEach(i=>i.checked=i.value===state[k]);
  const inputDescription=state.caseId.startsWith('b')?'単一面Fのz='+boundaryNames[state.caseId.slice(3)]:state.caseId.startsWith('exact-tie')?'Aのz=2/5、Bのz=2/5':'Aのz=2/5、Bのz=7/15';
  $('condition-description').textContent='選択：'+name(state.caseId)+'。'+inputDescription+'。予想は全描画が終わった時点について選びます。';
  if(!state.shown)return;
  const c=state.shown,v=S.snapshot(state);$('results').dataset.caseId=c.id;$('results').dataset.step=String(state.step);
  $('provenance').textContent='保存計算 '+D.observed_at_utc+' / '+D.run_id+' / SHA256 '+D.result_sha256;
  $('step-label').textContent=state.step===0?'描画前（背景）':'描画 '+state.step+' 後';$('previous').disabled=state.step===0;$('next').disabled=state.step===c.trace.length;
  for(const [key,title,depth,winner] of [['exact','厳密な奥行き',v.exact.depth,v.exact.winner],['quantized','保存した整数',String(v.quantized.code)+' / 最大 '+c.maximum,v.quantized.winner]]){const card=text('div','');card.className='card';card.dataset.method=key;card.append(text('span',title),text('strong',depth),text('p','残る面：'+face(winner)));$('cards').append(card);}
  diagram(c);
  table('trace-rows',c.trace.map(r=>[r.step,r.fragment_id,r.z,r.scaled,r.code,r.reconstructed,r.rounding_error,r.exact_before.depth+' '+face(r.exact_before.winner)+' → '+r.exact_after.depth+' '+face(r.exact_after.winner),r.exact_pass?'採用':'不採用',r.quantized_before.code+' '+face(r.quantized_before.winner)+' → '+r.quantized_after.code+' '+face(r.quantized_after.winner),r.quantized_pass?'採用':'不採用']));
  table('boundary-rows',D.result.boundaries.map(c=>{const r=c.trace[0];return [c.bits,r.z,r.scaled,r.code,r.reconstructed,r.rounding_error,r.exact_pass?'採用':'不採用',r.quantized_pass?'採用':'不採用',face(c.quantized_final.winner)];}));
  $('raw-json').textContent=JSON.stringify({case:c,selected_step:state.step,selected_state:v,boundaries:D.result.boundaries},null,2);
  if(state.answer){const e=c.exact_final.winner,q=c.quantized_final.winner,correct=state.exactPrediction===(e??'background')&&state.quantizedPrediction===(q??'background');let reason='';if(c.id.startsWith('same-bin'))reason='元の奥行きは異なりますが、3bitではどちらも3です。等しい保存値は更新しないので、先に描いた面が残ります。';else if(c.id.startsWith('separated'))reason='この入力では4bitの保存値が6と7に分かれ、順序によらずAが残ります。';else if(c.id.startsWith('exact-tie'))reason='元の奥行きが真に同じです。両方式とも等しい値は更新せず、先に描いた面が残ります。';else if(c.id.endsWith('clear-bin'))reason='31/32は1未満なので厳密方式は採用しますが、整数では最大値へ丸まり背景と同値になるため不採用です。';else if(c.id.endsWith('one'))reason='z=1は初期値と同じです。両方式とも厳密な小なり比較を満たしません。';else reason='丸めた整数を決めてから、背景の最大値より小さいかを別に判定します。';$('answer').append(text('strong',correct?'予想と一致しました。':'予想と異なりました。'),text('p','最後は厳密方式：'+face(e)+'、整数保存方式：'+face(q)+'。'+reason));}
 }
 render();
})();

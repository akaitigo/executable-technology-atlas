(function(){
  'use strict';
  const S=globalThis.DeviceSnapshotState,D=globalThis.DeviceSnapshotData,E=globalThis.DeviceSnapshotExpected;
  const $=id=>document.getElementById(id);
  const V=['continuation','full-restore','omit-device'];
  const labels={'continuation':'そのまま継続','full-restore':'完全復元','omit-device':'装置欠落の比較版'};
  const titles={'initial':'初期：tick0','before-expiry':'発火直前：tick2','pending-latched':'発火済み：tick3','after-ack':'ACK後：tick6'};
  const fmt=v=>v===null?'—':Array.isArray(v)?'['+v.join(',')+']':String(v);
  const write=v=>v===null?'—':`M${v.address}:${v.previous}→${v.value}`;
  let state=S.initial();
  function element(tag,text,cls){const e=document.createElement(tag);if(text!==undefined)e.textContent=text;if(cls)e.className=cls;return e;}
  function svg(tag,attrs,text){const e=document.createElementNS('http://www.w3.org/2000/svg',tag);for(const [k,v] of Object.entries(attrs))e.setAttribute(k,String(v));if(text!==undefined)e.textContent=text;return e;}
  function fields(s,e){return {pc:s.pc,a:s.a,memory:s.memory,tick:s.tick,counter:s.device.counter,pending:s.device.pending,
    op:e?e.op:null,timer_pending:e?e.timer_after.pending:null,timer_fired:e?e.timer_after.fired:null,
    read_value:e?e.read_value:null,write:e?write(e.write):'—',ack:e?e.ack:null};}
  const names={pc:'次のpc',a:'A',memory:'memory',tick:'仮想tick',counter:'counter',pending:'境界pending',op:'直前の命令',timer_pending:'命令前pending',timer_fired:'このtickで発火',read_value:'この命令のREAD',write:'この命令の書込み',ack:'この命令はACK'};
  function render(){
    for(const id of ['provenance','case-note','snapshots','position','cards','diagram','trace','raw','answer','error'])$(id).textContent='';
    $('raw-details').open=false;$('results').hidden=true;
    document.querySelectorAll('[data-case]').forEach(b=>b.setAttribute('aria-pressed',String(b.dataset.case===state.case_id)));
    document.querySelectorAll('[data-prediction]').forEach(b=>b.setAttribute('aria-pressed',String(b.dataset.prediction===state.prediction)));
    document.querySelectorAll('[data-mode]').forEach(b=>b.setAttribute('aria-pressed',String(b.dataset.mode===state.mode)));
    $('error').textContent=state.error;
    if(!state.shown)return;
    const c=state.shown.payload,i=state.index,t=c.cut+i;
    $('results').hidden=false;
    $('provenance').textContent=`保存計算 ${state.shown.observed_at_utc} / ${state.shown.run_id} / SHA256 ${state.shown.result_sha256}`;
    $('case-note').textContent=titles[c.id]+'。完全復元は同じprefixからの継続と比較します。装置欠落は別schemaの意図故障です。';
    for(const [name,s] of [['完全snapshotの状態',c.snapshot.state],['欠落版の復元直後',c.variants['omit-device'].boundary_states[0]]]){
      const box=element('div',undefined,'snapshot');box.append(element('strong',name));
      for(const [key,v] of Object.entries({pc:s.pc,a:s.a,memory:s.memory,tick:s.tick,counter:s.device.counter,pending:s.device.pending})){
        const line=element('p',`${names[key]} = ${fmt(v)}`);line.dataset.key=key;line.dataset.value=fmt(v);box.append(line);
      }$('snapshots').append(box);
    }
    $('position').textContent=`選択境界 tick ${t} / 最終 tick 10`;
    $('previous').disabled=i===0;$('next').disabled=i===c.variants.continuation.boundary_states.length-1;
    V.forEach((name,vi)=>{
      const v=c.variants[name],s=v.boundary_states[i],event=i?v.steps[i-1]:null;
      const card=element('article',undefined,'card');card.dataset.variant=name;card.append(element('h3',labels[name]));
      const dl=element('dl');
      for(const [key,value] of Object.entries(fields(s,event))){
        const line=element('div');line.dataset.key=key;line.append(element('dt',names[key]),element('dd',fmt(value)));dl.append(line);
      }card.append(dl);$('cards').append(card);
      v.boundary_states.forEach((row,j)=>{
        const e=j?v.steps[j-1]:null;const tr=element('tr');tr.dataset.variant=name;tr.dataset.tick=row.tick;
        if(j===i)tr.className='selected';
        [labels[name],row.tick,row.pc,row.a,fmt(row.memory),row.device.counter,row.device.pending,
         e?e.timer_after.fired:null,e?e.read_value:null,e?write(e.write):'—'].forEach(value=>tr.append(element('td',fmt(value))));
        $('trace').append(tr);
      });
      const y=50+60*vi,color=vi===2?'#aa5724':'#216b60';
      $('diagram').append(svg('text',{x:8,y:y+5,'font-size':16,fill:color},labels[name]));
      $('diagram').append(svg('line',{x1:150+55*c.cut,x2:700,y1:y,y2:y,stroke:'#8ca69a','stroke-width':1}));
      v.boundary_states.forEach(row=>{
        const x=150+55*row.tick,py=y+(row.device.pending?-12:12);
        $('diagram').append(svg('circle',{cx:x,cy:py,r:row.tick===t?7:5,fill:color,'data-variant':name,'data-tick':row.tick,'data-counter':row.device.counter,'data-pending':row.device.pending}));
        $('diagram').append(svg('text',{x,y:py+(row.device.pending?-10:20),'text-anchor':'middle','font-size':14,fill:color},String(row.device.counter)));
      });
    });
    for(let tick=c.cut;tick<=10;tick++)$('diagram').append(svg('text',{x:150+55*tick,y:226,'text-anchor':'middle','font-size':14,fill:'#314d45'},'t'+tick));
    $('raw').textContent=JSON.stringify(c,null,2);
    if(state.answer){
      const same=c.comparison.fault_suffix_equal;
      const right=state.prediction===(same?'same':'different');
      let text=(right?'予想は一致しました。':'今回の保存結果は予想と異なります。')+' 完全復元のsuffixは継続と全値一致です。';
      if(same)text+=' この切断点ではdeviceが元から0,falseなので、欠落版も一致します。他の切断点や任意の装置で十分とは判断できません。';
      else text+=` 欠落版は復元直後のtick${c.comparison.first_state_difference_tick}で状態が変わり、tick${c.comparison.first_read_difference_tick}のREADが1から0へ変わります。最終memoryは[0,0,1,0]で、完全復元の[1,0,1,0]と異なります。`;
      if(c.id==='pending-latched')text+=' tick6でpendingが再び一致しても、先にSTOREした差は残ります。';
      if(c.id==='before-expiry')text+=' 発火はsuffixのtick3,6,9からtick5,8へずれます。';
      $('answer').textContent=text;
    }
  }
  function act(action){state=S.transition(state,action,D,E);render();}
  document.querySelectorAll('[data-case]').forEach(b=>b.addEventListener('click',()=>act({type:'case',value:b.dataset.case})));
  document.querySelectorAll('[data-prediction]').forEach(b=>b.addEventListener('click',()=>act({type:'prediction',value:b.dataset.prediction})));
  document.querySelectorAll('[data-mode]').forEach(b=>b.addEventListener('click',()=>act({type:'mode',value:b.dataset.mode})));
  $('load').addEventListener('click',()=>act({type:'load'}));$('reset').addEventListener('click',()=>act({type:'reset'}));
  $('previous').addEventListener('click',()=>act({type:'step',delta:-1}));$('next').addEventListener('click',()=>act({type:'step',delta:1}));
  $('answer-button').addEventListener('click',()=>act({type:'answer'}));
  globalThis.DeviceSnapshotReader={getState:()=>JSON.parse(JSON.stringify(state))};render();
})();

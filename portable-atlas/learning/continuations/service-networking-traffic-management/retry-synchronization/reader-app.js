(function(){
  'use strict';
  const S=globalThis.RetryConcentrationState,D=globalThis.RetryConcentrationData,E=globalThis.RetryConcentrationExpected;
  const $=id=>document.getElementById(id);
  const titles={synchronized:'同期',staggered:'分散',skewed:'偏り','budget-five':'同期・予算5'};
  const statuses={WAITING:'再開待ち',RUNNING:'結果待ち',SUCCEEDED:'成功',RETRY_EXHAUSTED:'追加回数を使い切った',CALL_BUDGET:'共有予算で開始拒否'};
  const names={status:'状態',attempts:'開始attempt数',retries_used:'使った追加retry',retries_remaining:'残る追加retry',next_due:'次の最早開始',in_flight_finish:'結果が届くtick',completion_tick:'成功完了tick',terminal_tick:'終端tick',effects:'合成効果'};
  const metrics={candidates:'到来候補',started:'開始したclient',accepted:'受理したclient',budget_denied:'予算で開始拒否',calls_used:'累積call',budget_remaining:'残る共有予算',retries_used:'累積追加retry',effects:'累積合成効果'};
  const summaryNames={calls:'全call',retries:'追加retry',effects:'合成効果',duplicate_effects:'重複効果',succeeded:'成功client',not_succeeded:'成功していないclient',unfinished:'未終端client',retry_exhausted:'追加回数で終端',call_budget:'共有予算で終端',budget_remaining:'残る共有予算',peak_all_starts:'全attemptピーク',peak_retry_starts:'retryだけのピーク',last_terminal_tick:'最後の終端tick'};
  const fmt=v=>v===null?'—':Array.isArray(v)?(v.length?v.join(','):'—'):String(v);
  let state=S.initial();
  function element(tag,text,cls){const e=document.createElement(tag);if(text!==undefined)e.textContent=text;if(cls)e.className=cls;return e;}
  function svg(tag,attrs,text){const e=document.createElementNS('http://www.w3.org/2000/svg',tag);for(const [k,v] of Object.entries(attrs))e.setAttribute(k,String(v));if(text!==undefined)e.textContent=text;return e;}
  function metric(parent,key,label,value){const d=element('div',undefined,'metric');d.dataset.key=key;d.append(element('span',label),element('strong',fmt(value)));parent.append(d);}
  function render(){
    for(const id of ['provenance','case-note','schedule','position','metrics','cards','diagram','trace','summary','raw','answer','error'])$(id).textContent='';
    $('raw-details').open=false;$('results').hidden=true;
    document.querySelectorAll('[data-case]').forEach(b=>b.setAttribute('aria-pressed',String(b.dataset.case===state.case_id)));
    document.querySelectorAll('[data-prediction]').forEach(b=>b.setAttribute('aria-pressed',String(b.dataset.prediction===state.prediction)));
    document.querySelectorAll('[data-mode]').forEach(b=>b.setAttribute('aria-pressed',String(b.dataset.mode===state.mode)));
    $('error').textContent=state.error;
    if(!state.shown)return;
    const c=state.shown.payload,row=c.ticks[state.index],f=state.shown.fixture;
    $('results').hidden=false;
    $('provenance').textContent=`保存計算 ${state.shown.observed_at_utc} / ${state.shown.run_id} / SHA256 ${state.shown.result_sha256}`;
    $('case-note').textContent=titles[c.id]+'。完了→ID順の候補→共有予算→容量の順で、このtickを処理しました。';
    $('schedule').textContent=`固定delay A/B/C/D = ${f.delays.map(v=>'['+v.join(',')+']').join(' / ')}、初回込み共有call予算 ${f.call_budget}。`;
    $('position').textContent=`選択 tick ${row.tick} / 最終 tick 7`;
    $('previous').disabled=state.index===0;$('next').disabled=state.index===7;
    for(const [key,label] of Object.entries(metrics))metric($('metrics'),key,label,row[key]);
    for(const client of row.clients){
      const card=element('article',undefined,'card');card.dataset.client=client.client;card.append(element('h3','client '+client.client));
      const dl=element('dl');
      for(const [key,label] of Object.entries(names)){
        const d=element('div');d.dataset.key=key;d.append(element('dt',label),element('dd',key==='status'?statuses[client[key]]:fmt(client[key])));dl.append(d);
      }card.append(dl);$('cards').append(card);
    }
    for(let count=0;count<=4;count++){
      const y=185-count*30;$('diagram').append(svg('line',{x1:45,x2:740,y1:y,y2:y,stroke:'#d7e1db'}));
      $('diagram').append(svg('text',{x:28,y:y+5,'font-size':14,fill:'#314d45'},String(count)));
    }
    const kinds=[['candidates','#707a80'],['started','#24678c'],['accepted','#247658']];
    for(const t of c.ticks){
      const x=62+t.tick*84;
      if(t.tick===row.tick)$('diagram').append(svg('rect',{x:x-6,y:40,width:68,height:165,fill:'none',stroke:'#b27a0b','stroke-width':2,'data-selected-tick':t.tick}));
      kinds.forEach(([kind,color],i)=>{
        const value=t[kind].length,px=x+i*20,py=185-value*30;
        $('diagram').append(svg('rect',{x:px,y:py,width:16,height:value*30,fill:color,'data-kind':kind,'data-tick':t.tick,'data-count':value}));
        $('diagram').append(svg('text',{x:px+8,y:py-6,'text-anchor':'middle','font-size':14,fill:color},String(value)));
      });
      $('diagram').append(svg('text',{x:x+26,y:226,'text-anchor':'middle','font-size':16,fill:'#314d45'},'t'+t.tick));
    }
    for(const e of c.attempts){
      const tr=element('tr');tr.dataset.client=e.client;tr.dataset.ordinal=e.ordinal;
      if(e.start<=row.tick&&row.tick<e.finish)tr.className='selected';
      [e.client,e.ordinal,e.start,e.finish,e.ordinal>1?'はい':'初回',e.accepted?'受理':'非受理',e.outcome,e.accepted?1:0].forEach(v=>tr.append(element('td',fmt(v))));
      $('trace').append(tr);
    }
    for(const [key,label] of Object.entries(summaryNames))metric($('summary'),key,label,c.summary[key]);
    $('raw').textContent=JSON.stringify(c,null,2);
    if(state.answer){
      const all=c.summary.succeeded===4,right=state.prediction===(all?'all':'not-all');
      let text=(right?'予想は一致しました。':'今回の保存結果は予想と異なります。')+` 成功${c.summary.succeeded}、成功していない${c.summary.not_succeeded}。全call${c.summary.calls}、追加retry${c.summary.retries}、合成効果${c.summary.effects}です。`;
      if(c.id==='synchronized')text+=' t2とt4に再び重なり、Dはt5に追加回数を使い切ります。';
      if(c.id==='staggered')text+=' retryだけのピークは1ですが、初回を含むピークは4のままです。';
      if(c.id==='skewed')text+=' 全員成功でも、Dはt6まで待って開始しt7に完了。分散より2call多く、終わりも遅くなります。';
      if(c.id==='budget-five')text+=' t2でBが最後のcall枠を使います。C/Dは追加retry残数2でも開始できず、attempt1・効果0のまま終端です。';
      $('answer').textContent=text+' 応答欠落は含めず、重複効果0は一般の冪等性を証明しません。';
    }
  }
  function act(action){state=S.transition(state,action,D,E);render();}
  document.querySelectorAll('[data-case]').forEach(b=>b.addEventListener('click',()=>act({type:'case',value:b.dataset.case})));
  document.querySelectorAll('[data-prediction]').forEach(b=>b.addEventListener('click',()=>act({type:'prediction',value:b.dataset.prediction})));
  document.querySelectorAll('[data-mode]').forEach(b=>b.addEventListener('click',()=>act({type:'mode',value:b.dataset.mode})));
  $('load').addEventListener('click',()=>act({type:'load'}));$('reset').addEventListener('click',()=>act({type:'reset'}));
  $('previous').addEventListener('click',()=>act({type:'step',delta:-1}));$('next').addEventListener('click',()=>act({type:'step',delta:1}));
  $('answer-button').addEventListener('click',()=>act({type:'answer'}));
  globalThis.RetryConcentrationReader={getState:()=>JSON.parse(JSON.stringify(state))};render();
})();

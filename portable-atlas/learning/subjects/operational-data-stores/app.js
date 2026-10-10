// SPDX-License-Identifier: Apache-2.0
(() => {
  const {raw, run} = window.KV_LESSON;
  const cases = Object.fromEntries(raw.scenarios.map(x=>[x.id,x]));
  const text = {
    blind:['Blind write：+1が1つ失われる','AとBが両方0を読み、1を順番に上書き。最終valueは？','2回ともrowcount=1ですが、最終値は1。versionが増えても、古いvalueを無条件で書けばlost updateは残ります。'],
    cas:['Version CAS：古いversionを拒否','同じversionでAの後にBが更新。再読込み後も+1した最終値は？','Bの古いv1はrowcount=0。Bがv2を読み直して再計算した更新は通り、最終値2です。自動retryではなく、固定scheduleの明示再読込みです。'],
    'invalid-types':['型・versionの入力境界','文字列version、bool、負version、非整数valueを渡すと？','6入力はPython APIで拒否。更新SQLは発行されず、既存の値0/version1を保持します。'],
    'unknown-key':['未知keyと古いversion','missingへの更新とcounterのv0更新。既存valueは変わる？','どちらも実UPDATEのrowcount=0。未知keyを勝手に作成せず、既存counterも変えません。0行はSQL例外ではありません。'],
    aba:['値が戻るABA','0→5→0、versionは1→2→3。古いv1は通る？','値は0へ戻りましたがversionは3。古いv1の更新は拒否されます。'],
    'aba-reset':['削除・再作成のABA限界','delete後に0/version1を作り直す。古いv1は通る？','古いv1の更新が通りました。versionを再利用するkey recreationは保護できません。generation token等は未実装です。'],
  };
  let selected='blind', step=0;
  document.getElementById('version').textContent=run.runtime.sqlite_version;
  document.getElementById('comparisonRows').innerHTML=raw.scenarios.map(x=>'<tr><td>'+x.id+'</td><td>'+x.final[0][1]+'</td><td>'+x.final[0][2]+'</td><td>'+text[x.id][0]+'</td></tr>').join('');
  function renderStep(){
    const x=cases[selected], event=step?x.trace[step-1]:null;
    const state=event?event.state_after:x.initial, entry=state.find(row=>row[0]==='counter');
    document.getElementById('stepNumber').textContent=step+' / '+x.trace.length+' steps';
    document.getElementById('previous').disabled=step===0;
    document.getElementById('next').disabled=step===x.trace.length;
    document.getElementById('stateValue').textContent=entry?entry[1]:'∅';
    document.getElementById('stateVersion').textContent=entry?'version '+entry[2]:'key deleted';
    ['A','B'].forEach(name=>document.getElementById('session'+name).classList.toggle('active',Boolean(event&&event.session===name)));
    document.getElementById('stepMeaning').textContent=event?('Session '+event.session+' · '+event.operation):'初期値0、version1。2つの接続が同じDBを参照。';
    document.getElementById('stepSql').textContent=event?(event.sql||'更新SQLなし · API type guard')+'\nparameters: '+JSON.stringify(event.parameters)+(event.reason?'\nreason: '+event.reason:''):'初期setup: '+raw.setup.seed_sql+'\n'+JSON.stringify(raw.setup.seed_parameters);
    document.getElementById('rowcount').textContent=event?'rowcount: '+event.rowcount:'';
    document.getElementById('readRows').textContent=event?'rows: '+JSON.stringify(event.rows):'';
  }
  function choose(id){
    selected=id;step=0;
    document.querySelectorAll('[data-case]').forEach(button=>button.setAttribute('aria-pressed',String(button.dataset.case===id)));
    document.getElementById('caseTitle').textContent=text[id][0];
    document.getElementById('caseQuestion').textContent=text[id][1];
    document.getElementById('answer').hidden=true;
    renderStep();
  }
  document.querySelectorAll('[data-case]').forEach(button=>button.addEventListener('click',()=>choose(button.dataset.case)));
  document.getElementById('reveal').addEventListener('click',()=>{
    const final=cases[selected].final[0];
    document.getElementById('answer').hidden=false;
    document.getElementById('finalValue').textContent='final '+final[1]+' / v'+final[2];
    document.getElementById('verdict').textContent=String(final[1])===document.getElementById('prediction').value?'予想と一致':'予想と異なる結果';
    document.getElementById('explanation').textContent=text[selected][2];
    renderStep();
  });
  document.getElementById('previous').addEventListener('click',()=>{if(step>0)step--;renderStep();});
  document.getElementById('next').addEventListener('click',()=>{if(step<cases[selected].trace.length)step++;renderStep();});
  choose('blind');
})();

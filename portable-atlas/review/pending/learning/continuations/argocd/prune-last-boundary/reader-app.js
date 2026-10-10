(function(){
  'use strict';const R=window.PruneLastReader,$=id=>document.getElementById(id);let state=R.initial();
  const selectionLabel=value=>value==='none'?'対象なし':value.split(',').join(' と ');
  const description={ordinary:'全体指定なし・資源単位指定なし。候補waveは計算しても、使う対象があるかを考えます。',global:'全体PruneLastあり。app-a / app-b はapply、old-low / old-high はpruneです。','resource-only':'全体指定なし。old-lowの資源単位PruneLastだけあり。old-highには指定がありません。','all-negative':'全体PruneLastあり。Sync側の元waveはすべて負です。探索を始める値に注目します。','presync-excluded':'全体PruneLastあり。PreSyncのJobはwave 20、Syncのapplyは0、pruneは−2です。'};
  const explain={ordinary:'候補は9でも、PruneLastを指定したpruneはないため上書きしません。通常の逆waveの計画を保ちます。',global:'通常逆wave後のold-lowの8もSync最大値に入ります。候補は6ではなく9。両pruneは同じSync / wave 9へ配置します。','resource-only':'old-lowだけをwave 9へ上書きします。指定のないold-highは通常の有効wave −3のままです。','all-negative':'通常逆wave後のSync waveは−7・−4・−2でも、探索の初期値0が残ります。候補は−1ではなく1です。','presync-excluded':'PreSyncのwave 20をSync最大値へ含めません。候補は1。oldのphaseはSyncのままで、PreSyncは数値20でも先のphaseとして配置します。'};
  const groupHTML=groups=>groups.map(g=>`<div class="group-row"><span class="phase-pill">${g.phase}</span><b>wave ${g.wave}</b><span>{${g.ids.join(', ')}}</span></div>`).join('');
  function render(){const v=R.view(state);document.querySelectorAll('[data-case]').forEach(b=>b.setAttribute('aria-pressed',String(b.dataset.case===state.id)));
    $('case-title').textContent=v.item.title;$('scope-description').textContent=description[state.id];
    $('input-tasks').innerHTML=v.item.tasks.map(t=>`<div class="task-seed"><strong>${t.id}</strong><span>${t.phase} / ${t.action}</span><span>元wave ${t.wave}${t.prune_last?' / 資源指定あり':''}</span></div>`).join('');
    if($('selection-options').dataset.case!==state.id){$('selection-options').innerHTML=R.choices[state.id].map(value=>`<label class="choice"><input type="radio" name="selection" value="${value}">${selectionLabel(value)}</label>`).join('');$('selection-options').dataset.case=state.id;}
    document.querySelectorAll('input[name=selection]').forEach(r=>{r.checked=r.value===state.selection;});if($('wave-prediction').value!==state.wave)$('wave-prediction').value=state.wave;
    $('next').disabled=!R.ready(state)||state.step===3;$('answer-button').disabled=state.step!==3||!!state.error;
    $('progress').textContent=`段階 ${state.step} / 3 · 予想変更で段階と答えを初期化します。`;
    $('input-error').hidden=!state.error;$('input-error').textContent=state.error||'';
    $('stage-status').textContent=['比較前 · 保存結果をまだ表示していません。','段階1 · 通常の逆waveを確認します。','段階2 · Sync最大値と上書き候補を確認します。','段階3 · 対象pruneのwaveを上書き。phaseは保持します。'][state.step];
    $('maximum').hidden=!v.maximumVisible;$('sync-max').textContent=v.maximumVisible?v.outcome.sync_max:'';$('candidate').textContent=v.maximumVisible?v.outcome.last_wave_candidate:'';
    $('resources').innerHTML=v.item.tasks.map(t=>{const selected=v.finalVisible&&v.outcome.selected.includes(t.id);return`<article class="resource${selected?' selected-resource':''}" data-resource="${t.id}"><strong>${t.id}</strong> <small>${t.action}</small><p class="phase-label">phase: ${t.phase}</p><div class="numbers"><span class="number-cell"><small>元wave</small><b>${t.wave}</b></span>→<span class="number-cell"><small>通常逆wave後</small><b class="ordinary-wave">${v.ordinaryVisible?v.outcome.ordinary_waves[t.id]:'?'}</b></span>→<span class="number-cell final"><small>指定後</small><b class="final-wave">${v.finalVisible?v.outcome.final_waves[t.id]:'?'}</b></span></div><p class="resource-state">${v.finalVisible?(selected?'PruneLastで上書き':'PruneLastでの変更なし'):'上書き結果は未表示'}</p></article>`;}).join('');
    $('ordinary-plan').hidden=!v.ordinaryVisible;$('final-plan').hidden=!v.finalVisible;$('ordinary-groups').innerHTML=v.ordinaryVisible?groupHTML(v.outcome.before_groups):'';$('final-groups').innerHTML=v.finalVisible?groupHTML(v.outcome.after_groups):'';
    $('answer').hidden=!state.answer;$('answer').innerHTML=state.answer?`<p><span class="${v.score.wave?'score-yes':'score-no'}">候補waveの予想は${v.score.wave?'一致':'不一致'}</span>。答え：${v.outcome.last_wave_candidate}</p><p><span class="${v.score.selection?'score-yes':'score-no'}">対象の予想は${v.score.selection?'一致':'不一致'}</span>。答え：${selectionLabel(v.outcome.selected.join(',')||'none')}</p><p>${explain[state.id]}</p><p>配置の比較であり、Health・削除完了・資源の完了順は未観測です。</p>`:'';
    $('provenance').textContent=`元の模型原票：${R.data.recorded_at_utc}。画面は保存結果を読み、原票を書き換えません。`;
  }
  document.querySelectorAll('[data-case]').forEach(b=>b.addEventListener('click',()=>{state=R.initial(b.dataset.case);render();}));
  $('wave-prediction').addEventListener('input',e=>{state=R.setWave(state,e.target.value);render();});
  $('selection-options').addEventListener('change',e=>{if(e.target.name==='selection'){state=R.setSelection(state,e.target.value);render();}});
  $('next').addEventListener('click',()=>{state=R.advance(state);render();});$('reset').addEventListener('click',()=>{state=R.initial(state.id);render();});$('answer-button').addEventListener('click',()=>{state=R.reveal(state);render();});render();
})();

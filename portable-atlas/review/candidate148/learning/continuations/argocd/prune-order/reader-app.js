(function () {
  'use strict';
  const R = window.PruneReader;
  let state = R.initial();
  const $ = id => document.getElementById(id);
  const orderText = list => (Array.isArray(list) ? list : list.split(',')).join(' → ');
  const observations = {ready: '別の仮定：次waveへ進める状態', absent: '別の観測：liveなし', terminating: '別の観測：liveあり・削除中', unobserved: 'その後のlive / Healthは未観測'};
  const stopText = {'plan-consumed': '計画を最後まで読んだ。全資源の消滅・Healthyは未保証。', 'next-reconciliation-waits-for-deletion': '削除待ち。次のreconciliationは後続waveへ進まない。', 'runTasks-prune-failed': '現在waveのpruneが失敗。同waveのapply・後続waveは未着手。'};
  const inputText = {
    'apply-ascending': 'low・midは次へ進める状態、highの適用後のHealthは未観測、と仮定します。',
    'prune-descending': 'high・midの消滅を別に観測。最後のlowはPruned後のlive状態を与えません。',
    'prune-waiting': 'highがPruned。その後もliveがあり、deletionTimestampがある観測を与えます。',
    'prune-failed': 'highの消滅を別に観測し、midの結果コードをSyncFailedと仮定します。',
    'mixed-same-wave-failed': 'wave 0にoldのpruneとnewのapply。oldの結果コードをSyncFailedと仮定します。'
  };
  const answerText = {
    'apply-ascending': '通常applyは元waveを保ち、小さい−3から1、8へ進みます。最後のhighがHealthyかは、この例では観測していません。',
    'prune-descending': 'pruneだけのwaveの両端を交換します。highの有効waveは−3、midは1、lowは8です。Prunedになった最後のlowの消滅は未観測です。',
    'prune-waiting': 'Prunedという結果でも、liveが削除中なら後続を待ちます。midとlowの結果欄は未着手のままです。最終waveでの待機を一般化する例ではありません。',
    'prune-failed': 'highは開始済みですが、midでpruneの失敗を返します。lowへ進まず、失敗後のretryやSyncFail hookはこの模型に含めません。',
    'mixed-same-wave-failed': '同じwaveでも、まずprune側を処理します。oldの失敗でapply側へ進まないため、newもlaterも未着手です。'
  };
  function render() {
    const v = R.view(state);
    document.querySelectorAll('[data-case]').forEach(b => b.setAttribute('aria-pressed', String(b.dataset.case === state.id)));
    $('question').textContent = v.item.question;
    $('scenario-input').textContent = inputText[state.id];
    $('input-tasks').innerHTML = v.item.tasks.slice().sort((a,b) => a.wave-b.wave || a.id.localeCompare(b.id)).map(t => `<div class="task-seed"><strong>${t.id}</strong><span>${t.action} / 元wave ${t.wave}</span></div>`).join('');
    if ($('order-options').dataset.case !== state.id) {
      $('order-options').innerHTML = R.choices[state.id].map(value => `<label class="choice"><input type="radio" name="order" value="${value}">${orderText(value)}</label>`).join('');
      $('order-options').dataset.case = state.id;
    }
    document.querySelectorAll('input[name=order]').forEach(radio => { radio.checked = radio.value === state.prediction; });
    document.querySelectorAll('input[name=stop]').forEach(radio => { radio.checked = radio.value === state.stopPrediction; });
    $('next').disabled = !R.ready(state) || v.complete;
    $('answer-button').disabled = !v.complete;
    $('progress').textContent = R.ready(state) ? `段階 ${state.step} / ${v.totalSteps} · 予想変更で段階と答えを初期化します。` : '開始順と終端の予想を2つ選んでください。';
    $('stage-status').className = 'phase-status' + (v.complete ? ' ' + ({'plan-consumed':'consumed','next-reconciliation-waits-for-deletion':'wait','runTasks-prune-failed':'failed'}[v.stop]) : '');
    $('stage-status').textContent = v.complete ? stopText[v.stop] : state.step === 0 ? '比較前 · まだ結果を表示していません。' : state.step === 1 ? '初期計画 · 元waveと有効waveを比べます。' : `${v.started.at(-1)} の保存結果を表示しました。停止境界は最後に確認します。`;
    $('resource-grid').innerHTML = v.resources.map(t => {
      const failed = t.result?.result === 'SyncFailed', waiting = t.result?.observation === 'terminating';
      return `<article class="resource${t.attempted?' attempted':''}${failed?' failed':''}${waiting?' waiting':''}" data-resource="${t.id}"><strong>${t.id}</strong> <small>${t.action}</small><div class="wave-map">元 <span class="wave-value">${t.wave}</span> → 有効 <span class="wave-value">${v.planned ? v.outcome.effective_waves[t.id] : '?'}</span></div><div class="resource-state">${t.result ? t.result.result : '未着手'}</div><div class="observation">${t.result ? observations[t.result.observation] : '結果・live観測はまだ表示していません。'}</div></article>`;
    }).join('');
    $('plan').hidden = !v.planned;
    $('batches').innerHTML = v.planned ? v.outcome.batches.map(b => `<div class="batch"><b>有効wave ${b.wave}</b><span class="lane prune">prune: ${b.prune.join(', ') || 'なし'}</span><span class="lane">apply: ${b.apply.join(', ') || 'なし'}</span></div>`).join('') : '';
    $('answer').hidden = !state.answer;
    $('answer').innerHTML = state.answer ? `<p><span class="${v.score.order?'score-yes':'score-no'}">開始順の予想は${v.score.order?'一致':'不一致'}</span>。答え：${orderText(v.outcome.started)}</p><p><span class="${v.score.stop?'score-yes':'score-no'}">終端の予想は${v.score.stop?'一致':'不一致'}</span>。</p><p>${answerText[state.id]}</p><p>未着手：${v.outcome.unstarted.join('、') || 'なし'}。${stopText[v.stop]}</p>` : '';
    $('provenance').textContent = `元の模型原票：${R.data.recorded_at_utc}。画面は保存結果のreaderで、原票を上書きしません。`;
  }
  document.querySelectorAll('[data-case]').forEach(button => button.addEventListener('click', () => {state=R.initial(button.dataset.case);render();}));
  $('order-options').addEventListener('change', e => {if(e.target.name==='order'){state=R.selectStart(state,e.target.value);render();}});
  document.querySelectorAll('input[name=stop]').forEach(radio => radio.addEventListener('change', () => {state=R.selectStop(state,radio.value);render();}));
  $('next').addEventListener('click', () => {state=R.advance(state);render();});
  $('reset').addEventListener('click', () => {state=R.initial(state.id);render();});
  $('answer-button').addEventListener('click', () => {state=R.reveal(state);render();});
  render();
})();

(function () {
  'use strict';
  const S = window.AtlasRetryState;
  const D = window.ATLAS_RETRY_DATA;
  const E = window.ATLAS_RETRY_EXPECTED;
  let state = S.initial();
  const $ = id => document.getElementById(id);
  const descriptions = {
    'retryable-resume': 'Bの結果列：再試行可能な失敗 → 成功。DはBの成功を待ちます。',
    'nonretryable-stop': 'Bの結果列：再試行しない失敗 → 成功。後の成功は入力にありますが、到達するとは限りません。',
    'retry-budget-exhausted': 'Bの結果列：再試行可能な失敗が3回。追加開始の予算は2回です。',
    'premature-downstream-block': '故障比較：Bの結果列は最初の条件と同じ。最初の失敗でDを最終的な実行不可へ固定してしまいます。'
  };
  const labels = {pending: '依存待ち', running: '実行中', 'retry-wait': '再試行待ち', succeeded: '成功', failed: '終端失敗', blocked: '最終的な実行不可', 'policy-violation': '方針違反'};
  const shown = value => value === null ? '未到達・対象なし' : typeof value === 'boolean' ? (value ? 'はい' : 'いいえ') : String(value);
  const outcome = value => ({TRANSIENT: '再試行可能な失敗', PERMANENT: '再試行しない失敗', SUCCESS: '成功'}[value] || value);
  const reason = value => value === null ? 'まだ終端にしない' : ({nonretryable: '再試行しない分類', 'budget-exhausted': '追加予算がない'}[value] || value);
  function element(tag, text, attrs = {}) {
    const node = document.createElement(tag);
    if (text !== null) node.textContent = text;
    Object.entries(attrs).forEach(([key, value]) => node.setAttribute(key, value));
    return node;
  }
  function table(id, rows) {
    const body = $(id).querySelector('tbody');
    body.replaceChildren();
    for (const row of rows) {
      const tr = element('tr', null);
      for (const value of row) tr.appendChild(element('td', String(value)));
      body.appendChild(tr);
    }
  }
  function svg(tag, attrs, text = null) {
    const node = document.createElementNS('http://www.w3.org/2000/svg', tag);
    Object.entries(attrs).forEach(([key, value]) => node.setAttribute(key, value));
    if (text !== null) node.textContent = text;
    return node;
  }
  function timeline(row, point) {
    const canvas = $('timeline'); canvas.replaceChildren();
    const x = t => 70 + 90 * t;
    canvas.appendChild(svg('text', {x: 12, y: 37, fill: '#20343d', 'font-size': 18}, 'B'));
    canvas.appendChild(svg('text', {x: 12, y: 89, fill: '#20343d', 'font-size': 18}, 'D'));
    for (let t = 0; t <= 7; t++) {
      canvas.appendChild(svg('line', {x1: x(t), x2: x(t), y1: 8, y2: 106, stroke: '#d1ded6'}));
      canvas.appendChild(svg('text', {x: x(t), y: 130, 'text-anchor': 'middle', fill: '#314e40', 'font-size': 16}, String(t)));
    }
    for (const [task, attempts, y, fill] of [['B', row.b_attempts, 14, '#377f9d'], ['D', row.d_attempts, 66, '#397848']]) {
      for (const a of attempts) {
        canvas.appendChild(svg('rect', {x: x(a.start), y, width: (a.end - a.start) * 90, height: 32, fill,
          'data-task': task, 'data-attempt': a.attempt, 'data-start': a.start, 'data-end': a.end}));
        canvas.appendChild(svg('text', {x: x(a.start) + 45, y: y + 22, 'text-anchor': 'middle', fill: 'white', 'font-size': 16}, `${task}${a.attempt}`));
      }
    }
    for (const f of row.failure_decisions.filter(f => f.retry_planned)) {
      canvas.appendChild(svg('line', {x1: x(f.at), x2: x(f.next_due), y1: 55, y2: 55, stroke: '#896a1c', 'stroke-width': 4,
        'stroke-dasharray': '6 4', 'data-wait-from': f.at, 'data-wait-due': f.next_due}));
    }
    canvas.appendChild(svg('line', {x1: x(point.t), x2: x(point.t), y1: 5, y2: 108, stroke: '#bd4627', 'stroke-width': 3, 'data-selected-t': point.t}));
    canvas.appendChild(svg('text', {x: 70, y: 156, fill: '#4e626d', 'font-size': 15}, '点線：再試行までの待機 / 赤線：選択した境界 / 単位：仮想tick'));
  }
  function clearRendered() {
    $('result').hidden = true;
    $('provenance').textContent = '';
    $('cards').replaceChildren(); $('boundary-note').textContent = ''; $('timeline').replaceChildren();
    ['attempts', 'failures', 'checks'].forEach(id => table(id, []));
    $('raw').textContent = ''; $('raw-details').open = false;
    $('answer-text').replaceChildren(); $('answer').disabled = true;
    $('error').textContent = '';
    $('step').value = '0'; $('step').max = '0'; $('step-value').textContent = '';
    $('prev').disabled = true; $('next').disabled = true;
    delete $('result').dataset.caseId;
  }
  function render() {
    clearRendered();
    $('case-description').textContent = descriptions[state.caseId];
    document.querySelectorAll('[data-case]').forEach(button => button.setAttribute('aria-pressed', String(button.dataset.case === state.caseId)));
    document.querySelectorAll('[data-mode]').forEach(button => button.setAttribute('aria-pressed', String(button.dataset.mode === state.mode)));
    document.querySelectorAll('[name=prediction]').forEach(radio => { radio.checked = radio.value === state.prediction; });
    document.querySelectorAll('[name=due]').forEach(radio => { radio.checked = radio.value === state.duePrediction; });
    $('error').textContent = state.error;
    if (!state.shown) return;
    const row = state.shown, point = row.boundaries[state.step];
    $('result').hidden = false; $('result').dataset.caseId = row.id;
    $('provenance').textContent = `保存した計算：${D.result.observed_at_utc} / 実行識別：${D.run_id} / 結果SHA-256：${D.result_sha256}`;
    $('step').max = String(row.boundaries.length - 1); $('step').value = String(state.step); $('step-value').textContent = `t=${point.t}`;
    $('prev').disabled = state.step === 0; $('next').disabled = state.step === row.boundaries.length - 1;
    const cards = [['Bの状態', labels[point.b_state], 'b_state', point.b_state], ['Dの状態', labels[point.d_state], 'd_state', point.d_state],
      ['開始済みB試行', point.attempts_started, 'attempts_started', point.attempts_started], ['追加できる残り回数', point.retries_left, 'retries_left', point.retries_left],
      ['今待っている再開時刻', shown(point.waiting_until), 'waiting_until', point.waiting_until], ['この境界で判定した時刻', shown(point.retry_due_checked), 'retry_due_checked', point.retry_due_checked],
      ['時刻条件を満たしたか', shown(point.retry_time_met), 'retry_time_met', point.retry_time_met], ['この時点で観測済みのB値', shown(point.b_value), 'b_value', point.b_value],
      ['この時点で観測済みのD値', shown(point.d_value), 'd_value', point.d_value], ['方針違反が発生済みか', shown(point.policy_violation), 'policy_violation', point.policy_violation]];
    for (const [label, value, key, raw] of cards) {
      const card = element('div', null, {class: 'card', 'data-field': key, 'data-value': JSON.stringify(raw)});
      card.appendChild(element('span', label)); card.appendChild(element('b', String(value))); $('cards').appendChild(card);
    }
    $('boundary-note').textContent = point.retry_time_met === true ? '再開時刻ちょうどで追加試行を開始しました。この境界の判定は「はい」、待機中の時刻は対象なしに変わっています。' : point.b_state === 'retry-wait' ? '再試行は予定済みですが、時刻条件はまだ満たしていません。追加予算は待機中には減りません。' : '上のカードは選択した境界までの状態です。未到達の値を、後の成功値で埋めません。';
    timeline(row, point);
    table('attempts', [...row.b_attempts.map(a => ['B', a.attempt, a.start, a.end, outcome(a.outcome), shown(a.value)]), ...row.d_attempts.map(a => ['D', a.attempt, a.start, a.end, '成功', shown(a.value)])]);
    table('failures', row.failure_decisions.map(f => [f.at, outcome(f.error), shown(f.retryable), f.remaining_retries, shown(f.retry_planned), shown(f.next_due), reason(f.terminal_reason)]));
    table('checks', row.retry_checks.map(c => [c.at, c.due, shown(c.eligible)]));
    $('raw').textContent = JSON.stringify({run_id: D.run_id, selected_boundary: point, whole_case: row}, null, 2);
    $('answer').disabled = false;
    if (state.answer) {
      const first = row.b_attempts.length > 1 ? String(row.b_attempts[1].start) : 'none';
      const match = state.prediction === row.workflow_status && state.duePrediction === first;
      const answer = element('div', null, {class: 'answer'});
      answer.appendChild(element('p', `${match ? '予想は2つとも一致しました。' : '予想と違う箇所を確認しましょう。'} 全体は「${labels[row.workflow_status]}」、最初の追加試行は${first === 'none' ? 'ありません' : `t=${first}です`}。`));
      answer.appendChild(element('p', row.id === 'nonretryable-stop' ? '残予算2でも、PERMANENTなら終端です。入力表にある後のSUCCESSは未到達で、Bの成功値もありません。' : row.id === 'retry-budget-exhausted' ? '失敗完了がt=1、4なので、再開はt=3、6です。3回目の失敗では残り0のため新しい再開時刻を作りません。' : row.id === 'premature-downstream-block' ? 'Bは正常条件と同じ時刻に再開して成功しました。しかしDをt=1で最終的な実行不可に固定したため、Dの開始は0です。Bの成功だけでは全体の成功と判断できません。' : 't=2は待機、t=3で追加開始して残予算は2→1。t=4にBが成功するとDを開始し、t=5に14を得ます。'));
      answer.appendChild(element('p', `全試行の開始数：B ${row.b_calls}回 / D ${row.d_calls}回。現在選んだ時点はt=${point.t}で、全体の最後とは分けて読みます。`));
      $('answer-text').appendChild(answer);
    }
  }
  function dispatch(type, value) { state = S.transition(state, {type, value}, D, E); render(); }
  document.querySelectorAll('[data-case]').forEach(button => button.addEventListener('click', () => dispatch('case', button.dataset.case)));
  document.querySelectorAll('[data-mode]').forEach(button => button.addEventListener('click', () => dispatch('mode', button.dataset.mode)));
  document.querySelectorAll('[name=prediction]').forEach(radio => radio.addEventListener('change', () => dispatch('prediction', radio.value)));
  document.querySelectorAll('[name=due]').forEach(radio => radio.addEventListener('change', () => dispatch('duePrediction', radio.value)));
  $('load').addEventListener('click', () => dispatch('load'));
  $('reset').addEventListener('click', () => dispatch('reset'));
  $('answer').addEventListener('click', () => dispatch('answer'));
  $('prev').addEventListener('click', () => dispatch('step', state.step - 1));
  $('next').addEventListener('click', () => dispatch('step', state.step + 1));
  $('step').addEventListener('input', event => dispatch('step', Number(event.target.value)));
  render();
})();

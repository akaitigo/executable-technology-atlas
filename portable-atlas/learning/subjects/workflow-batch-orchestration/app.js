'use strict';
const $ = (id) => document.getElementById(id);
let current = null;
let currentId = null;
function selected() { return {case: $('case').value, retries: Number($('retries').value), seed: Number($('seed').value), previous_id: $('mode').value === 'reuse' ? currentId : null}; }
function renderStep() {
  if (!current) return;
  const result = current.result;
  const index = Number($('step').value);
  const event = result.events[index];
  $('position').textContent = `${index} / ${result.events.length - 1}`;
  $('event').textContent = `event ${index}: ${event.action}${event.task ? ' / ' + event.task : ''}${event.attempt ? ' / attempt ' + event.attempt : ''}${event.reason ? ' / ' + event.reason : ''}${event.error ? ' / ' + event.error : ''}`;
  $('cycle-edge').hidden = current.input.case !== 'cycle';
  $('node-A').querySelector('text').textContent = current.input.case === 'cycle' ? 'A : D (cycle)' : 'A : seed';
  $('tasks').replaceChildren();
  for (const [name, item] of Object.entries(event.state)) {
    const group = $('node-' + name);
    group.setAttribute('class', item.state);
    group.querySelector('.state').textContent = item.state;
    group.querySelector('.value').textContent = `value ${item.value === null ? '—' : item.value} / attempt ${item.attempts}`;
    const tr = document.createElement('tr');
    [name, item.state, String(item.attempts), item.value === null ? '—' : String(item.value), item.reused ? 'yes' : 'no'].forEach(value => {
      const td = document.createElement('td'); td.textContent = value; tr.append(td);
    });
    $('tasks').append(tr);
  }
  const expected = result.status === 'rejected' ? 'rejected' : result.tasks.D.state === 'blocked' ? 'blocked' : 'succeeded';
  const prediction = $('prediction').value;
  const feedback = prediction === 'unsure' ? '予想は未選択。' : prediction === expected ? '予想と最終結果は一致。' : '予想と最終結果は異なります。';
  $('answer').textContent = `全event終了後の答え: run=${result.status}、D=${result.tasks.D.state}、今回task呼出し=${result.invocations.length}。${feedback} いま表示しているのはevent ${index}です。`;
}
async function execute() {
  const input = selected();
  if ($('mode').value === 'reuse' && !currentId) { $('status').textContent = '再利用するrunがありません。最初は新規runを実行してください。'; return; }
  $('run').disabled = true;
  $('status').textContent = 'Pythonを実行しています…';
  try {
    const response = await fetch('/api/run', {method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify(input)});
    const data = await response.json();
    if (!response.ok) throw new Error(data.error);
    current = data.payload;
    currentId = data.run_id;
    $('result').hidden = false;
    $('comparison').hidden = false;
    $('step').max = String(current.result.events.length - 1);
    $('step').value = $('step').max;
    $('binding').textContent = `このrun: ${current.input.case} / seed ${current.input.seed} / retries ${current.input.retries} / reuse ${current.input.reuse_successes} / Python ${current.execution.python} / ${current.execution.observed_at} / source ${current.result.source_digest.slice(0, 16)}…`;
    $('raw').href = data.raw_path;
    $('metadata').href = data.metadata_path;
    $('raw-events').textContent = JSON.stringify(current.result.events, null, 2);
    $('oracle').textContent = `独立Oracle: ${current.oracle.permutations_examined} permutationを列挙、依存を満たす順は${current.oracle.valid_orders.length}。state/value/attempt期待値との一致=${current.oracle_matches}。${current.oracle.cycle ? 'cycleなので有効順は0、実行前拒否。' : '有効順: ' + current.oracle.valid_orders.map(order => order.join('→')).join(' / ')}`;
    $('matrix').replaceChildren();
    current.comparison.forEach(report => {
      const tr = document.createElement('tr');
      [report.input.case, report.result.status, report.result.tasks.B.attempts, `${report.result.tasks.D.state} / value ${report.result.tasks.D.value === null ? '—' : report.result.tasks.D.value}`, report.oracle_matches].forEach(value => {
        const td = document.createElement('td'); td.textContent = String(value); tr.append(td);
      });
      $('matrix').append(tr);
    });
    $('status').textContent = '実行と原票の追記が完了。以前の原票は置換していません。';
    renderStep();
  } catch (error) {
    $('status').textContent = `今回の操作は拒否／失敗: ${error.message}。直前の画面・原票は保持しています。`;
  } finally { $('run').disabled = false; }
}
$('run').addEventListener('click', execute);
$('step').addEventListener('input', renderStep);
$('first').addEventListener('click', () => { $('step').value = '0'; renderStep(); });
$('last').addEventListener('click', () => { $('step').value = $('step').max; renderStep(); });
$('failure').addEventListener('click', () => {
  const index = current.result.events.findIndex(event => ['attempt-failed', 'rejected'].includes(event.action));
  $('step').value = String(index < 0 ? 0 : index); renderStep();
});
['case', 'retries', 'seed', 'mode'].forEach(id => $(id).addEventListener('change', () => { $('status').textContent = '入力が変わりました。表示中の結果は前回runです。実行して更新してください。'; }));
$('prediction').addEventListener('change', renderStep);

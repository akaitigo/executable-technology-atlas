(function (root) {
  'use strict';
  const data = typeof module !== 'undefined' && module.exports ? require('./reader-data.js') : root.PruneLessonData;
  const choices = {
    'apply-ascending': ['low,mid,high', 'high,mid,low', 'low'],
    'prune-descending': ['high,mid,low', 'low,mid,high', 'high'],
    'prune-waiting': ['high', 'high,mid', 'high,mid,low'],
    'prune-failed': ['high,mid', 'high,mid,low', 'mid'],
    'mixed-same-wave-failed': ['old', 'old,new', 'new,old,later']
  };
  const stopValues = {'consumed': 'plan-consumed', 'wait': 'next-reconciliation-waits-for-deletion', 'failed': 'runTasks-prune-failed'};
  function lookup(id) {
    const item = data.cases.find(c => c.id === id);
    if (!item) throw new Error('保存済みのケースを選んでください');
    return item;
  }
  function initial(id = 'apply-ascending') {
    lookup(id);
    return {id, prediction: null, stopPrediction: null, step: 0, answer: false};
  }
  function selectStart(state, prediction) {
    if (!choices[state.id].includes(prediction)) throw new Error('開始順の予想が範囲外です');
    return {...state, prediction, step: 0, answer: false};
  }
  function selectStop(state, stopPrediction) {
    if (!Object.hasOwn(stopValues, stopPrediction)) throw new Error('終端の予想が範囲外です');
    return {...state, stopPrediction, step: 0, answer: false};
  }
  const maximum = state => data.outcomes[state.id].started.length + 2;
  const ready = state => state.prediction !== null && state.stopPrediction !== null;
  function advance(state) {
    if (!ready(state)) throw new Error('2つの予想を選んでください');
    return {...state, step: Math.min(state.step + 1, maximum(state)), answer: false};
  }
  function reveal(state) {
    if (!ready(state) || state.step !== maximum(state)) throw new Error('対照を最後まで進めてください');
    return {...state, answer: true};
  }
  function view(state) {
    const item = lookup(state.id), outcome = data.outcomes[state.id];
    const started = outcome.started.slice(0, Math.max(0, state.step - 1));
    const complete = state.step === maximum(state);
    return {
      item, outcome, started, complete, planned: state.step > 0,
      totalSteps: maximum(state),
      resources: item.tasks.map(task => ({...task, attempted: started.includes(task.id),
        result: started.includes(task.id) ? outcome.results[task.id] : null})),
      stop: complete ? outcome.stop.reason : null,
      score: state.answer ? {
        order: state.prediction === outcome.started.join(','),
        stop: stopValues[state.stopPrediction] === outcome.stop.reason
      } : null
    };
  }
  const api = {data, choices, stopValues, initial, selectStart, selectStop, maximum, ready, advance, reveal, view};
  if (typeof module !== 'undefined' && module.exports) module.exports = api;
  else root.PruneReader = api;
})(typeof globalThis !== 'undefined' ? globalThis : this);

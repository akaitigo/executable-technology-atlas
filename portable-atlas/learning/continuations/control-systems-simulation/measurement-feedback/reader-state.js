(function (root) {
  'use strict';
  const ids = ['current-exact', 'delayed-one', 'fixed-noise', 'quantized-unit'];
  const stable = v => Array.isArray(v) ? '[' + v.map(stable).join(',') + ']' : v && typeof v === 'object' ? '{' + Object.keys(v).sort().map(k => JSON.stringify(k) + ':' + stable(v[k])).join(',') + '}' : JSON.stringify(v);
  const initial = (caseId = ids[0]) => ({caseId, prediction: null, terminalPrediction: null, mode: 'normal', shown: null, step: 0, answer: false, error: ''});
  const clear = s => ({...s, shown: null, step: 0, answer: false, error: ''});
  function transition(s, event, data, expected) {
    if (event.type === 'case') return ids.includes(event.value) ? initial(event.value) : s;
    if (event.type === 'prediction') return ['equal', 'below', 'above'].includes(event.value) ? {...clear(s), prediction: event.value} : s;
    if (event.type === 'terminalPrediction') return ['applied', 'unapplied'].includes(event.value) ? {...clear(s), terminalPrediction: event.value} : s;
    if (event.type === 'mode') return ['normal', 'missing', 'altered', 'old'].includes(event.value) ? {...clear(s), mode: event.value} : s;
    if (event.type === 'reset') return initial(s.caseId);
    if (event.type === 'step') return s.shown && Number.isInteger(event.value) && event.value >= 0 && event.value < s.shown.boundaries.length ? {...s, step: event.value, answer: false} : s;
    if (event.type === 'answer') return s.shown ? {...s, answer: true} : s;
    if (event.type !== 'load') return s;
    const next = clear(s);
    if (!s.prediction || !s.terminalPrediction) return {...next, error: 'k=1の測定値と、終端入力の扱いを先に予想してください。'};
    try {
      if (!data || !expected) throw Error('not connected');
      const candidate = JSON.parse(JSON.stringify(data));
      if (s.mode === 'missing') candidate.result.cases.pop();
      if (s.mode === 'altered') candidate.result.cases[3].boundaries[1].measurement = '0';
      if (s.mode === 'old') candidate.run_id = 'previous-run';
      if (stable(candidate) !== stable(expected)) throw Error('record mismatch');
      const row = candidate.result.cases.find(c => c.id === s.caseId);
      if (!row) throw Error('missing case');
      return {...next, shown: row};
    } catch (_) {
      return {...next, error: '保存した計算が未接続、または記録の欠落・変更・由来の不一致があります。古い図・答え・詳細は表示しません。'};
    }
  }
  const api = {ids, stable, initial, transition};
  root.AtlasMeasurementState = api;
  if (typeof module !== 'undefined') module.exports = api;
})(typeof window !== 'undefined' ? window : globalThis);

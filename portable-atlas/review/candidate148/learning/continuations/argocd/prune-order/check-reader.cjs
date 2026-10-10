'use strict';
const fs = require('node:fs'), path = require('node:path'), crypto = require('node:crypto'), assert = require('node:assert/strict');
const R = require('./reader-state.js');
const root = __dirname;
const hash = name => crypto.createHash('sha256').update(fs.readFileSync(path.join(root,name))).digest('hex');
const report = {kind:'saved-model-reader-state-check', started_at_utc:new Date().toISOString(), checks:[], expected_refusals:[],
  prior_model_record_sha256:hash('observations/model-check.json'), browser_executed:false, live_executed:false, numerical_model_rerun:false,
  artifact_sha256:Object.fromEntries(['index.html','reader-app.js','reader-state.js','reader-data.js','check-reader.cjs'].map(n=>[n,hash(n)]))};
const note = (name, details) => report.checks.push({name,details,pass:true});
const frozen = () => ({step:0,answer:false});
function verifyCleared(state, label, clearedPredictions=false) {
  assert.equal(state.step,0);assert.equal(state.answer,false);
  const view=R.view(state);assert.deepEqual(view.started,[]);assert.equal(view.stop,null);assert.equal(view.score,null);
  assert.equal(view.planned,false);assert.ok(view.resources.every(t=>t.result===null&&!t.attempted));
  if(clearedPredictions){assert.equal(state.prediction,null);assert.equal(state.stopPrediction,null);}
  note(label,'段階・答え・結果・live観測を初期化');
}
function completed(id) {
  const outcome=R.data.outcomes[id];let state=R.initial(id);
  state=R.selectStart(state,outcome.started.join(','));
  state=R.selectStop(state,Object.keys(R.stopValues).find(k=>R.stopValues[k]===outcome.stop.reason));
  for(let i=0;i<R.maximum(state);i++) state=R.advance(state);
  return R.reveal(state);
}
function refusal(label, fn) {assert.throws(fn);report.expected_refusals.push(label);}
try {
  const oracle=JSON.parse(fs.readFileSync(path.join(root,'hand-oracle.json'))).cases;
  const prior=JSON.parse(fs.readFileSync(path.join(root,'observations/model-check.json')));
  for(const [name,digest] of Object.entries(R.data.bindings))assert.equal(hash(name),digest,name);
  assert.deepEqual(R.data.outcomes,oracle);assert.deepEqual(R.data.outcomes,prior.outcomes);
  note('保存原票・手計算・readerデータの同一性','5ケースの全結果が一致');
  for(const item of R.data.cases) {
    const state=completed(item.id), v=R.view(state);
    assert.deepEqual(v.started,oracle[item.id].started);assert.equal(v.stop,oracle[item.id].stop.reason);
    assert.deepEqual(v.score,{order:true,stop:true});
    for(const resource of v.resources) assert.deepEqual(resource.result,oracle[item.id].results[resource.id]??null);
    note(item.id+' 完了段階','startedだけの結果、終端、予想一致');
    const changedOrder=R.choices[item.id].find(c=>c!==state.prediction);
    verifyCleared(R.selectStart(state,changedOrder),item.id+' 開始順予想変更');
    verifyCleared(R.selectStop(state,Object.keys(R.stopValues).find(k=>k!==state.stopPrediction)),item.id+' 終端予想変更');
    verifyCleared(R.initial(state.id),item.id+' reset',true);
    let wrong=R.initial(item.id);wrong=R.selectStart(wrong,changedOrder);wrong=R.selectStop(wrong,'consumed');
    for(let i=0;i<R.maximum(wrong);i++)wrong=R.advance(wrong);
    wrong=R.reveal(wrong);assert.equal(R.view(wrong).score.order,false);
    note(item.id+' 誤った開始順','一致と表示しない');
  }
  const mixed=completed('mixed-same-wave-failed');
  assert.deepEqual(R.view(mixed).resources.filter(t=>!t.attempted).map(t=>t.id),['new','later']);
  verifyCleared(R.initial('apply-ascending'),'失敗後の正常ケースへ切替',true);
  refusal('未選択では進めない',()=>R.advance(R.initial()));
  refusal('途中では答えを開けない',()=>R.reveal(R.initial()));
  refusal('未保存ケースを拒否',()=>R.initial('unknown'));
  refusal('未知の開始順を拒否',()=>R.selectStart(R.initial(),'ghost'));
  refusal('未知の終端を拒否',()=>R.selectStop(R.initial(),'healthy'));
  assert.equal(hash('observations/model-check.json'),report.prior_model_record_sha256);
  report.status='pass';
} catch(error) {report.status='fail';report.error=String(error.stack||error);process.exitCode=1;}
report.finished_at_utc=new Date().toISOString();
const destination=path.join(root,'observations/reader-state-check.json');
if(process.argv.includes('--record')) fs.writeFileSync(destination,JSON.stringify(report,null,2)+'\n',{flag:'wx'});
console.log(JSON.stringify({status:report.status,checks:report.checks.length,refusals:report.expected_refusals.length,error:report.error},null,2));

"use strict";
// DOMや実ブラウザを代用した検証ではない。UIが使う純粋計算・状態遷移だけを実行する。
const fs = require("node:fs");
const assert = require("node:assert/strict");
const app = require("./app.js");
const hand = JSON.parse(fs.readFileSync(__dirname + "/hand-oracle.json", "utf8"));
const cases = [];
let frames = 0;
for (const row of hand.cases) {
  const actual = app.schedule(row.order);
  for (const [i, name] of ["A", "B", "C"].entries()) {
    assert.equal(actual.jobs[name].start, row.start_by_ABC[i]);
    assert.equal(actual.jobs[name].finish, row.finish_by_ABC[i]);
  }
  for (const key of ["sum_completion", "mean_completion", "mean_wait", "max_completion", "makespan", "throughput"]) assert.equal(actual[key], row[key]);
  const seenFrames = [];
  for (let tick = 0; tick <= 7; tick++) {
    // 期待状態は実装前の手計算区間から作る。アプリのschedule値からは作らない。
    const expected = Object.fromEntries(["A", "B", "C"].map((name, i) => [name,
      tick >= row.finish_by_ABC[i] ? "完了" : tick >= row.start_by_ABC[i] ? "実行中" : "待ち"]));
    const actualFrame = app.frame(actual, tick);
    assert.deepEqual(actualFrame, expected);
    seenFrames.push({tick, jobs: actualFrame}); frames++;
  }
  cases.push({result: actual, frames: seenFrames});
}
const refused = [];
for (const value of [null, false, 0, [], {}, "", "AB", "ABA", "ABCD", "abc"]) {
  assert.throws(() => app.schedule(value), /REFUSED_INPUT/);
  refused.push({input: value, expected: "REFUSED_INPUT"});
}
for (const tick of [-1, 8, 1.5, true, "1"]) assert.throws(() => app.frame(app.schedule("ABC"), tick), /REFUSED_TICK/);
const transitions = [];
let state = app.initial();
assert.throws(() => app.transition(state, {type: "reveal"}), /PREDICTION_REQUIRED/);
state = app.transition(state, {type: "predict", value: "later"});
state = app.transition(state, {type: "reveal"});
assert.equal(state.revealed, true); transitions.push({action: "予想後に答えを表示", state});
state = app.transition(state, {type: "tick", value: 7});
assert.equal(state.revealed, true); transitions.push({action: "時刻を進めても同一条件の予想を保持", state});
state = app.transition(state, {type: "order", value: "ABC"});
assert.deepEqual(state, {order: "ABC", tick: 0, prediction: "", revealed: false});
transitions.push({action: "順序変更で予想・答え・時刻を初期化", state});
state = app.transition(state, {type: "predict", value: "same"});
state = app.transition(state, {type: "reveal"});
state = app.transition(state, {type: "predict", value: "earlier"});
assert.equal(state.revealed, false); transitions.push({action: "予想変更で古い答えを閉じる", state});
state = app.transition(state, {type: "reset"});
assert.deepEqual(state, app.initial()); transitions.push({action: "初期状態へ戻る", state});
console.log(JSON.stringify({passed: true, cases, frame_count: frames,
  refused_orders: refused, refused_ticks: 5, prediction_required: true, transitions,
  scope: "純粋関数と状態遷移。DOMイベント・描画・実ブラウザは未検証。"}));

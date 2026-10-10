// SPDX-License-Identifier: Apache-2.0
"use strict";
const observation = window.MODEL_OBSERVATION;
const byId = (id) => document.getElementById(id);
let variant = "atomic";
let current = 0;
let replay = false;
let step = 0;
const descriptions = {request: "入室を要求", "check-and-enter": "空き確認と入室を原子的に実行", "check-free": "空きを確認、readyへ", "claim-without-recheck": "空きを再確認せず入室", release: "退室、ownerを解放"};
const stateLabel = (state) => `${state.pc.join(" / ")} · owner=${state.owner === null ? "∅" : `P${state.owner}`}`;
function model() { return observation.models[variant]; }
function displayCounts(id, result) {
  const box = byId(id);
  for (const [number, label] of [[result.state_count,"到達状態"],[result.transition_count,"遷移"],[result.violation_count,"違反状態"]]) {
    const entry = document.createElement("div");
    const strong = document.createElement("strong"); strong.textContent = number;
    const small = document.createElement("small"); small.textContent = label;
    entry.append(strong, small); box.append(entry);
  }
}
function selectState(id) { current = id; replay = false; render(); }
function enterReplay(index) {
  variant = "split-guard"; byId("variant").value = variant;
  replay = true; step = index;
  current = index === 0 ? 0 : model().shortest_counterexample[index - 1].to;
  render();
}
function render() {
  const result = model();
  const state = result.states[current];
  byId("owner").textContent = state.owner === null ? "∅" : `P${state.owner}`;
  for (let process = 0; process < 2; process++) {
    const actor = byId(`p${process}`);
    actor.className = `actor${state.pc[process] === "critical" ? (state.invariant ? " critical" : " violation") : ""}`;
    actor.querySelector("span").textContent = state.pc[process];
  }
  const check = byId("invariant");
  check.className = `invariant${state.invariant ? "" : " fail"}`;
  check.textContent = `critical数=${state.pc.filter(pc=>pc==="critical").length} / MutualExclusion: ${state.invariant ? "成立" : "違反 — P0とP1が同時にcritical"}`;
  byId("step-description").textContent = replay && step > 0 ? `P${result.shortest_counterexample[step - 1].process}: ${descriptions[result.shortest_counterexample[step - 1].action]}` : `状態 S${current}: ${stateLabel(state)}`;
  byId("position").textContent = replay ? `反例step ${step} / ${result.shortest_counterexample_steps}` : "自由探索";
  byId("previous").disabled = !replay || step === 0;
  byId("next").disabled = !replay || step === result.shortest_counterexample_steps;
  byId("enabled").replaceChildren();
  for (const transition of result.transitions.filter(edge=>edge.from === current)) {
    const button = document.createElement("button");
    button.textContent = `P${transition.process}: ${descriptions[transition.action]}`;
    button.onclick = ()=>selectState(transition.to); byId("enabled").append(button);
  }
  const bad = observation.models["split-guard"];
  byId("trace").replaceChildren();
  const sequence = [0, ...bad.shortest_counterexample.map(edge=>edge.to)];
  sequence.forEach((id, index)=>{
    const state = bad.states[id];
    const button = document.createElement("button");
    button.className = `trace-node${replay && step === index ? " active" : ""}${state.invariant ? "" : " bad"}`;
    button.textContent = index === 0 ? "0 初期状態" : `${index} P${bad.shortest_counterexample[index-1].process} ${bad.shortest_counterexample[index-1].action}`;
    const detail = document.createElement("small");detail.textContent = stateLabel(state);button.append(detail);
    button.onclick = ()=>enterReplay(index);byId("trace").append(button);
  });
  byId("states").replaceChildren();
  for (const state of result.states) {
    const tile = document.createElement("button");
    tile.className = `state-tile${state.id === current ? " current" : ""}${!state.invariant ? " bad" : state.pc.includes("critical") ? " occupied" : ""}`;
    tile.textContent = `S${state.id} [depth ${state.depth}] ${stateLabel(state)}`;
    tile.onclick = ()=>selectState(state.id);byId("states").append(tile);
  }
}
const environment = observation.environment;
for (const label of [observation.observation_finished_at, `Python ${environment.python} / ${environment.implementation}`, `${environment.os} ${environment.os_version} / ${environment.architecture}`, "2 process · 全到達状態 · 深さ打切りなし"]) {
  const badge = document.createElement("span");badge.textContent = label;byId("environment").append(badge);
}
displayCounts("atomic-counts", observation.models.atomic);
displayCounts("faulty-counts", observation.models["split-guard"]);
byId("variant").onchange = event=>{variant=event.target.value;current=0;replay=false;render();};
byId("reset").onclick = ()=>{current=0;replay=false;render();};
byId("counterexample").onclick = ()=>enterReplay(0);
byId("next").onclick = ()=>enterReplay(step + 1);
byId("previous").onclick = ()=>enterReplay(step - 1);
byId("predict-safe").onclick = ()=>{byId("prediction-answer").textContent="予想: 守れる。では、P0とP1が両方check-freeを終えた状態へ進めて比較しよう。";enterReplay(0);};
byId("predict-unsafe").onclick = ()=>{byId("prediction-answer").textContent="予想: 破れる。保存された最短反例を1stepずつ進め、最初の違反を確かめよう。";enterReplay(0);};
const bad = observation.models["split-guard"];
byId("answer").textContent = `この有限モデルでは、正常系${observation.models.atomic.state_count}到達状態の相互排他は成立した。guardを分離すると${bad.state_count}到達状態のうち${bad.violation_count}状態で違反し、最短${bad.shortest_counterexample_steps}遷移で到達する。空きを確認した事実が、後の入室を安全にするとは限らない。`;
byId("version").textContent = observation.model_version;
render();

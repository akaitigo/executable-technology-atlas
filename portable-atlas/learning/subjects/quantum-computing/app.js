/* SPDX-License-Identifier: Apache-2.0 */
"use strict";
const observation=window.QUANTUM_OBSERVATION;
const circuits=observation.result.circuits;
const el=id=>document.getElementById(id);
let step=0,variant="coherent",samplesVisible=false;
const fmt=x=>Math.abs(x)<1e-10?"0":x.toFixed(4);
const complex=z=>`${fmt(z[0])}${z[1]<0?" − ":" + "}${fmt(Math.abs(z[1]))}i`;
const probability=p=>`${(p*100).toFixed(2)}%`;
function plot(z,index){
  const x=65+50*z[0],y=65-50*z[1],magnitude=Math.hypot(...z);
  return `<div><svg class="complex-plot" viewBox="0 0 130 130" role="img" aria-label="amplitude ${index}: ${complex(z)}; arrow length is magnitude, not probability"><circle cx="65" cy="65" r="50" fill="#f6f9fa" stroke="#c8d7dd"/><path d="M10 65H120M65 10V120" stroke="#beced5"/><text x="108" y="59" font-size="10" fill="#54656d">Re</text><text x="71" y="15" font-size="10" fill="#54656d">Im</text><line x1="65" y1="65" x2="${x}" y2="${y}" stroke="#20627f" stroke-width="3"/><circle cx="${x}" cy="${y}" r="4" fill="#20627f"/></svg><div class="amp-value">a${index} = ${complex(z)}<br>|a| = ${fmt(magnitude)} / phase ${magnitude<1e-12?"未定義":fmt(Math.atan2(z[1],z[0]))+" rad"}</div></div>`;
}
function renderCard(prefix,state,title){
  if(prefix==="left")el("left-title").textContent=title;
  const pure=Math.abs(state.purity-1)<1e-12;
  el(`${prefix}-state-kind`).textContent=pure?"pure state / purity 1":"mixed state / purity 0.5";
  el(`${prefix}-amplitudes`).innerHTML=pure?`<div class="amplitude-row">${state.branches[0].amplitudes.map(plot).join("")}</div>`:`<div class="mixed-message"><strong>単一amplitude vectorはない</strong><p>このensembleのbranch表示：</p>${state.branches.map(b=>`<p class="branch">weight ${fmt(b.weight)} × (${b.amplitudes.map(complex).join(", ")})</p>`).join("")}<p>branch amplitudeは足し合わせない。</p></div>`;
  el(`${prefix}-matrix`).innerHTML=`ρ（密度行列）<table aria-label="${prefix} density matrix"><tbody>${state.density_matrix.map(row=>`<tr>${row.map(z=>`<td>${complex(z)}</td>`).join("")}</tr>`).join("")}</tbody></table>`;
  el(`${prefix}-bars`).innerHTML=state.probabilities.map((p,i)=>`<div class="prob-row"><span>P(${i})</span><div class="track"><div class="fill" style="width:${Math.min(100,p*100)}%"></div></div><strong>${probability(p)}</strong></div>`).join("");
  el(`${prefix}-metrics`).textContent=`|ρ01| ${fmt(state.coherence_magnitude)} · purity ${fmt(state.purity)} · trace ${fmt(state.trace)}`;
}
function renderSamples(){
  el("sampling").hidden=!samplesVisible;
  if(!samplesVisible)return;
  const records=[[variant,"左の経路"],["dephased","途中dephasing"]];
  el("sampling").innerHTML=`<p>最後のHの後の測定。現在の操作stepとは別に、保存runの最終stateを比較する。</p><table><thead><tr><th>経路</th><th>Born P(0), P(1)</th><th>counts / 4096</th><th>頻度0, 1</th></tr></thead><tbody>${records.map(([key,name])=>{const c=circuits[key];return `<tr><td>${name}</td><td>${c.stages.at(-1).probabilities.map(probability).join(" / ")}</td><td>${c.sampling.counts.join(" / ")}</td><td>${c.sampling.frequencies.map(probability).join(" / ")}</td></tr>`}).join("")}</tbody></table>`;
}
function render(){
  const leftIndex=variant==="coherent"?[0,1,1,2][step]:step;
  const left=circuits[variant].stages[leftIndex],right=circuits.dephased.stages[step];
  renderCard("left",left,{coherent:"H → H",phase_pi:"H → Z → H",phase_half_pi:"H → S → H"}[variant]);
  renderCard("right",right);
  el("step-status").textContent=`step ${step} / 3`;
  el("previous").disabled=step===0;el("next").disabled=step===3;
  document.querySelectorAll("[data-step]").forEach(b=>{b.classList.toggle("active",Number(b.dataset.step)===step);b.setAttribute("aria-current",Number(b.dataset.step)===step?"step":"false");});
  const messages=["同じ初期|0⟩から始める。0 amplitudeにphaseは定義しない。","両経路ともP(0)=P(1)=50%。ρ01=0.5を持つpure state。確率だけでなくamplitudeが残っている。","右はDでoff-diagonalが0に。Born確率は50/50のままでも、coherenceとpurityが変わった。左のZ/Sは位相を変えるunitary操作で、情報を捨てない。", "最後のH。左は保持したrelative phaseに応じて干渉する。右は混合stateなのでP(0)=P(1)=50%のまま。"];
  el("interpretation").textContent=step===2&&variant==="coherent"?"左は操作せずcoherenceを保持。右だけDを適用。両者のBorn確率は50/50なのにρ01とpurityは異なる。":messages[step];
  renderSamples();
}
el("environment").innerHTML=[observation.finished_at,`Python ${observation.environment.python} / ${observation.environment.implementation}`,`${observation.environment.os} ${observation.environment.release} / ${observation.environment.architecture}`,"1 qubit · ideal classical simulation"].map(t=>`<span>${t}</span>`).join("");
el("next").onclick=()=>{step=Math.min(3,step+1);render();};el("previous").onclick=()=>{step=Math.max(0,step-1);render();};el("reset").onclick=()=>{step=0;render();};
el("variant").onchange=e=>{variant=e.target.value;render();};
document.querySelectorAll("[data-step]").forEach(b=>b.onclick=()=>{step=Number(b.dataset.step);render();});
for(const [id,response] of [["predict-zero","予想：どちらも0。step2で密度行列のoff-diagonalを比べ、最後のHへ進もう。"],["predict-mixed","予想：結果が変わる。step2では確率が同じか、coherenceが同じかを別々に確認しよう。"]])el(id).onclick=()=>{el("prediction-response").textContent=response;step=0;render();};
el("show-sample").onclick=()=>{samplesVisible=!samplesVisible;el("show-sample").textContent=samplesVisible?"頻度を閉じる":"保存済み4096 shotの頻度を見る";renderSamples();};
render();

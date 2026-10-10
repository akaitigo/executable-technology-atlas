/* SPDX-License-Identifier: Apache-2.0 */
"use strict";
const observation=window.EXPRESSION_OBSERVATION;
const cases=observation.result.cases;
const el=id=>document.getElementById(id);
const escape=s=>String(s).replaceAll("&","&amp;").replaceAll("<","&lt;").replaceAll(">","&gt;").replaceAll('"',"&quot;");
const labels={precedence:"正常：2 + 3 * 4",parentheses:"括弧：(2 + 3) * 4",two_products:"比較：2 * 3 + 4 * 5",boundary:"境界：leading zero / 6桁",zero:"境界：0",missing_operand:"構文error：2 + * 3",missing_close:"構文error：(2 + 3",illegal_character:"字句error：2 + x",adjacent_integers:"構文error：2 3",multiline_error:"構文error：2行目の*"};
let selected="precedence",step=0;
function drawTree(tree,active,built,preview){
  if(!tree)return '<p class="fine">Root ASTは成立していない。評価へ進まない。</p>';
  let leaves=0,maxDepth=0,nodes=[],edges=[];
  function place(node,depth){
    maxDepth=Math.max(maxDepth,depth);
    const children=node.kind==="Group"?[node.child]:node.kind==="Integer"?[]:[node.left,node.right];
    const positions=children.map(child=>place(child,depth+1));
    const x=positions.length?positions.reduce((sum,p)=>sum+p.x,0)/positions.length:70+(leaves++)*135,y=38+depth*70;
    positions.forEach(p=>edges.push(`<line x1="${x}" y1="${y+19}" x2="${p.x}" y2="${p.y-19}" stroke="#8c9d87"/>`));
    const label=node.kind==="Integer"?node.value:{Add:"+",Multiply:"*",Group:"( )"}[node.kind];
    const pending=!preview&&!built.has(node.id);
    nodes.push(`<g><rect class="node ${pending?"pending":""} ${active===node.id?"active":""}" x="${x-46}" y="${y-21}" width="92" height="42" rx="9"/><text class="node-label" x="${x}" y="${y+6}" text-anchor="middle" opacity="${pending ? 0.3 : 1}">${label}</text><text x="${x}" y="${y+36}" font-size="9" text-anchor="middle" fill="#6b7e65">${node.id}</text></g>`);
    return {x,y};
  }
  place(tree,0);
  return `<svg viewBox="0 0 ${Math.max(220,leaves*135+10)} ${maxDepth*70+100}" role="img" aria-label="${preview?"naive final":"normal AST preview with current node"}">${edges.join("")}${nodes.join("")}</svg>`;
}
function render(){
  const c=cases[selected],timeline=c.timeline,current=timeline[step],past=timeline.slice(0,step+1);
  const [start,end]=current.span;
  el("source").innerHTML=escape(c.input.slice(0,start))+`<mark>${end===start?"⟂":escape(c.input.slice(start,end))}</mark>`+escape(c.input.slice(end));
  el("source-location").textContent=`選択span [${start}, ${end})。⟂はzero-width位置。`;
  el("step-counter").textContent=`${current.phase} / step ${step+1} of ${timeline.length}`;
  el("step-label").textContent=current.label;
  el("step-detail").textContent=current.phase==="evaluate"?`node ${current.node_id}: operands [${current.operands.join(", ")}] → ${current.result}`:current.phase==="parse"?"grammarに従ってtokenを消費し、nodeを組む。AST previewの生成済みnodeを点灯。":current.phase==="error"?"このinputは停止。Root AST・評価値を発行しない。":"文字のspanをtokenへ変換。まだ評価していない。";
  const emitted=new Set(past.filter(e=>e.phase==="token").map(e=>e.token_index));
  el("tokens").innerHTML=c.tokens.map((t,i)=>`<span class="token ${emitted.has(i)?"emitted":""} ${current.token_index===i?"current":""}">${escape(t.text||"EOF")}<small>${t.kind} [${t.start},${t.end})</small></span>`).join("");
  const built=new Set(past.filter(e=>e.phase==="parse"&&e.action==="build").map(e=>e.node_id));
  el("normal-tree").innerHTML=drawTree(c.ast,current.node_id,built,false);
  el("naive-tree").innerHTML=drawTree(c.naive?.ast,null,new Set(),true);
  const done=step===timeline.length-1;
  el("normal-result").textContent=c.status==="passed"?(done?`正常の結果 = ${c.value}`:"結果は最後の評価stepへ"):(done?"結果なし：errorで停止":"error原票。最後のstepで位置を確認");
  el("naive-result").textContent=c.naive?(done?`naiveの結果 = ${c.naive.value}`:"右は最終AST preview"):"このinputをnaiveでも評価しない";
  el("error").hidden=!(c.error&&done);
  if(c.error&&done){const e=c.error,line=c.input.split("\n")[e.line-1];el("error").innerHTML=`<h3>${escape(e.phase)} error · line ${e.line}, column ${e.column}</h3><pre>${escape(line)}\n${" ".repeat(e.column-1)}^</pre><p>offset ${e.offset}: expected ${escape(e.expected)} / found ${escape(e.found)}</p><p class="fine">最初に検出した位置。作者の修正意図を推定しているわけではない。</p>`;}
  el("previous").disabled=step===0;el("next").disabled=done;
  for(const [id,phase]of[["jump-token","token"],["jump-parse","parse"],["jump-evaluate","evaluate"]])el(id).disabled=!timeline.some(e=>e.phase===phase);
  el("trace").innerHTML=timeline.map((e,i)=>`<li><button data-event="${i}" class="${i===step?"active":""}">${i+1} · ${e.phase}: ${escape(e.label)}</button></li>`).join("");
  el("trace").querySelectorAll("button").forEach(b=>b.onclick=()=>{step=Number(b.dataset.event);render();});
}
el("case").innerHTML=Object.keys(cases).map(key=>`<option value="${key}">${labels[key]}</option>`).join("");
el("case").onchange=e=>{selected=e.target.value;step=0;render();};
el("next").onclick=()=>{step=Math.min(cases[selected].timeline.length-1,step+1);render();};el("previous").onclick=()=>{step=Math.max(0,step-1);render();};el("reset").onclick=()=>{step=0;render();};
for(const [id,phase]of[["jump-token","token"],["jump-parse","parse"],["jump-evaluate","evaluate"]])el(id).onclick=()=>{step=cases[selected].timeline.findIndex(e=>e.phase===phase);render();};
el("jump-final").onclick=()=>{step=cases[selected].timeline.length-1;render();};
for(const[id,response]of[["predict14","予想：14。*のnodeがどこに組まれるか見よう。"],["predict20","予想：20。左からのnaive木と、期待grammarの木を比較しよう。"]])el(id).onclick=()=>{selected="precedence";el("case").value=selected;step=0;el("prediction-response").textContent=response;render();};
el("environment").innerHTML=[observation.finished_at,`Python ${observation.environment.python} / ${observation.environment.implementation}`,`${observation.environment.os} ${observation.environment.release} / ${observation.environment.architecture}`,"独自bounded grammar · 保存10 input"].map(t=>`<span>${escape(t)}</span>`).join("");
render();

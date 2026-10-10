"use strict";
const $=id=>document.getElementById(id);
let report=null, position=0;
const json=v=>JSON.stringify(v,null,2);
function draw(){
  const result=report.result, event=result.events[position], matrix=event.matrix;
  $("summary").textContent=`検証済み ${matrix.verified}/${matrix.total}要求 · 独立oracle ${report.oracle.all_match ? "一致" : "不一致"}`;
  $("event").textContent=`${position+1}/${result.events.length} · ${event.action}`;
  $("matrix").replaceChildren();
  for(const row of matrix.rows){
    const tr=document.createElement("tr");
    const values=[`${row.requirement_id} / rev ${row.revision}`,row.statement,row.status,
      row.checks.map(c=>`${c.test_id}: ${c.status}\n現在: ${c.current_evidence.join(", ")||"なし"}\n${c.rejected_evidence.map(p=>`${p.evidence_id} → ${p.reasons.join(", ")}`).join("\n")}`).join("\n\n")];
    values.forEach((value,i)=>{const td=document.createElement("td");td.textContent=value;td.style.whiteSpace="pre-wrap";if(i===2)td.className="status "+row.status;tr.append(td);});$("matrix").append(tr);
  }
  $("previous").disabled=position===0;$("next").disabled=position===result.events.length-1;
  $("changed").disabled=!result.events.some(e=>e.action==="requirements-changed");$("final").disabled=false;
  $("diff").textContent=json(result.diff);
  $("proof").replaceChildren();
  for(const p of result.proofs.filter(p=>event.evidence_ids.includes(p.evidence_id))){const o=document.createElement("option");o.value=p.evidence_id;o.textContent=`${p.evidence_id} → ${p.requirement_id} rev${p.requirement_revision} (${p.passed?"pass":"fail"})`;$("proof").append(o);}
  if(event.latest_proof)$("proof").value=event.latest_proof.evidence_id;
  trace();
  $("raw").textContent=json({input:report.input,execution:report.execution,plan_digest:result.plan_digest,oracle:report.oracle});
}
function trace(){const p=report.result.proofs.find(p=>p.evidence_id===$("proof").value);$("trace").textContent=p?json(p):"このイベントではまだ実テストを実行していません。";}
$("run").onclick=async()=>{
  $("run").disabled=true;$("message").textContent="Pythonで実queueテストを実行中…";
  try{const response=await fetch("/run",{method:"POST",headers:{"Content-Type":"application/json"},body:json({case:$("case").value,record:$("record").checked})});if(!response.ok)throw new Error(`HTTP ${response.status}`);
    const data=await response.json();report=data.report;position=report.result.events.length-1;draw();$("message").textContent=`実行済み: ${report.execution.observed_at} · ${data.record_path||"read-only（保存なし）"}`;
  }catch(error){$("message").textContent=`失敗: ${error.message}`;}finally{$("run").disabled=false;}
};
$("previous").onclick=()=>{position--;draw();};$("next").onclick=()=>{position++;draw();};
$("changed").onclick=()=>{position=report.result.events.findIndex(e=>e.action==="requirements-changed");draw();};
$("final").onclick=()=>{position=report.result.events.length-1;draw();};$("proof").onchange=trace;

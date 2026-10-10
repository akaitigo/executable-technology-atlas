"use strict";
const data=window.PARTIAL_OBSERVATION,$=id=>document.getElementById(id);
let selected=0,step=0;
const labels=["初期plan","初回applyの実結果","同じplanをblind replay","refresh → 新plan","未適用分のreconcile","2回目plan/apply → no-op"];
function j(value){return JSON.stringify(value,null,2)}
function render(){
 const c=data.raw.cases[selected],expected=data.contracts.cases[selected];
 const states=[data.contracts.initial,c.partial,c.after_blind,c.refreshed,c.final,c.final],state=states[step];
 const results=[{actions:["create base","create config","create service"],observed_revision:0},{exit:c.first_exit,persisted_ids:Object.keys(c.partial.resources),rollback:false},{exit:c.blind_exit,state_unchanged:JSON.stringify(c.partial)===JSON.stringify(c.after_blind)},c.recovery_plan,{exit:c.recovery_exit,final:c.final},{exit:c.noop_exit,plan:c.noop_plan,store_hash_mtime_unchanged:c.noop_store_hash_mtime_unchanged}];
 const descriptions=["欲しい3件は全てmissing。依存順の3createを保存した。",c.id==="normal"?"全3createが完了した。":`InjectedFault ${c.fault}。部分stateを実fileから保存し、初期化していない。`,"baseが既に存在。非冪等createはDuplicateCreateで拒否され、stateを保持。","同じstoreを実読取し、desiredとの差から新planを保存。","新planだけをapply。既存resourceを再createしない。","新たなplanはactions0。再applyはstore hashとmtimeを変えなかった。"];
 $("progress").textContent=`段階 ${step+1} / 6 · ${c.id}`;$("step-label").textContent=`STEP ${step+1}`;$("step-title").textContent=labels[step];$("step-description").textContent=descriptions[step];$("revision").textContent=state.revision;$("count").textContent=Object.keys(state.resources).length;
 $("stage-result").textContent=j(results[step]);$("resource-tree").replaceChildren();
 data.contracts.desired.resources.forEach(resource=>{let card=document.createElement("article");const present=Object.hasOwn(state.resources,resource.id);card.className=present?"present":"absent";let h=document.createElement("h4");h.textContent=resource.id+(present?" · 存在":" · 未適用");let p=document.createElement("p");p.textContent=present?j(state.resources[resource.id].value):"desiredにあるが、実storeにまだない";let dependency=document.createElement("p");dependency.textContent=`depends_on: ${resource.depends_on.join(" → ")||"なし"}`;card.append(h,p,dependency);$("resource-tree").append(card)});
 $("advance").disabled=step===5;$("comparison").hidden=step<3;$("answer").hidden=step<5;
 $("blind").textContent=`exit ${c.blind_exit} · ${Object.keys(c.after_blind.resources).join(" / ")} · revision ${c.after_blind.revision}（partialと同じ）`;
 $("recovery").textContent=`create対象: ${c.recovery_plan.actions.map(a=>a.resource.id).join(" / ")||"なし（no-op）"} · 観測revision ${c.recovery_plan.observed_revision}`;
 const observed={first_exit:c.first_exit,partial_ids:Object.keys(c.partial.resources),partial_revision:c.partial.revision,recovery_ids:c.recovery_plan.actions.map(a=>a.resource.id)},hand={first_exit:expected.expected_first_exit,partial_ids:expected.expected_partial_ids,partial_revision:expected.expected_partial_revision,recovery_ids:expected.expected_recovery_ids};
 $("oracle").textContent=`事前手書き: ${j(hand)}\n保存実結果: ${j(observed)}\n${JSON.stringify(hand)===JSON.stringify(observed)?"独立期待と一致":"不一致・原票を確認"}`;
 $("prediction-result").textContent=$("prediction").value==="partial"?"予想は部分stateの実測と整合。正常条件は全3件が完了。":$("prediction").value?"予想を見直す：自動rollbackはなく、古いcreateのblind replayは重複拒否。":"予想未選択。途中stateと新planを比較する。";
 $("answer-text").textContent=`${c.id}：初回exit ${c.first_exit}、部分state ${Object.keys(c.partial.resources).join(" / ")}。再観測から${c.recovery_plan.actions.length}件のcreateだけをplanし、最終3件/revision3へ。次plan0/no-opを確認した。exit非0は変更ゼロを意味しない。`;
 $("trace").textContent=j(c.trace);$("rawlinks").replaceChildren();
 const base=`observations/${data.raw.run_id}/`;
 [["run raw","raw.json"],["artifact digest","artifact-index.json"],["失敗/初回command",`${c.id}/first-apply-command.json`],["partial file",`${c.id}/partial.json`],["blind command",`${c.id}/blind-replay-command.json`],["refresh command",`${c.id}/refresh-command.json`],["new plan",`${c.id}/recovery-plan.json`],["recovery command",`${c.id}/recovery-apply-command.json`],["no-op command",`${c.id}/noop-apply-command.json`]].forEach(([label,file],i)=>{if(i)$("rawlinks").append(" · ");let a=document.createElement("a");a.href=base+file;a.textContent=label;$("rawlinks").append(a)});
 const e=data.raw.environment;$("environment").textContent=`Run ${data.raw.run_id} · ${data.raw.started_at} → ${data.raw.ended_at} · Python ${e.python} / ${e.os} ${e.release} ${e.machine} / stdlib`;
}
$("scenario").addEventListener("change",()=>{selected=Number($("scenario").value);step=0;$("prediction").value="";$("answer").open=false;render()});
$("advance").addEventListener("click",()=>{if(step<5)step++;render()});$("reset").addEventListener("click",()=>{step=0;$("answer").open=false;render()});$("prediction").addEventListener("change",render);render();

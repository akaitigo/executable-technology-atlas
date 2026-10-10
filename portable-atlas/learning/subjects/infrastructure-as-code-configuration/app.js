"use strict";
const data = window.IAC_OBSERVATION, observation = data.observation;
const $ = s => document.querySelector(s);
const scenarios = {
  noop:["正常 / NO-OP","欲しい状態と、今の状態が同じ。","差分なしのplanをapply。合成storeのrevisionも変わらないかを確認します。","actionsは0、applyはno-op。stateのbytes/hash/revisionは不変で、2回目もno-opでした。"],
  reconcile:["正常 / RECONCILE","replicasを増やし、configを追加。","service.webを2→3へ更新し、config.extraを作成。既存config.bannerは保持します。","create＋updateを実行し、合成revisionは7→8へ。次のplanはactions0、再applyもno-opで同じstateです。"],
  drift:["正常 / OUT-OF-BAND DRIFT","宣言は同じ。観測だけ変わった。","計画前に合成stateのreplicasを2→1、revisionを7→8へ変更。宣言の2へ戻す差分を検出します。","out-of-band編集後の観測をplanへ束縛し、1→2をreconcile。revisionは8→9、2回目はno-op。これはJSON driftで、cloud resourceのrefresh実証ではありません。"],
  "stale-revision":["拒否 / STALE PLAN","plan後に、revisionが進んだ。","revision7でplanを保存し、apply直前にrevision8へ。resource内容は同じでもsnapshotは古くなっています。","stale-revisionでblocked。現在のrevision8 stateは変更せず保持し、古いplanを自動で作り直して実行しません。"],
  "silent-drift":["拒否 / CONTENT BINDING","revisionは同じ。内容だけ変わった。","plan後にreplicasを5へ変更、revision7は据え置き。revisionだけの検査では見逃す差です。","stale-observed-hashでblocked。revisionが同じでも内容hashが違うので、replicas5の現在stateを不変で保持しました。"],
  "delete-blocked":["境界 / DELETE AUTHORIZATION","宣言から消すと、deleteが出る。","service.webを宣言から除外。delete diffは見えますが、合成承認inputはありません。","delete-approval-requiredでblocked。planにdeleteがあることと、実行を承認したことは別です。service.webは合成storeへ残りました。"],
  "delete-approved":["正常 / SYNTHETIC APPROVAL","このplanの、このIDだけを承認。","plan digestとexact delete IDを持つ合成承認を渡し、合成service.webだけを削除します。","合成承認がplan digestとservice.webへ一致。deleteを合成store内で実行し、config.bannerを保持。実ユーザー認証・外部インフラ権限の証明ではありません。"],
  "wrong-approval":["拒否 / WRONG PLAN APPROVAL","IDは同じ。承認したplanが違う。","service.webのdelete IDは合いますが、承認のplan digestはzero digest。別planへの承認を流用しません。","delete-approval-requiredでblocked。ID一致だけでは足りず、このplanへの承認が必要です。stateは不変でした。"],
  "unknown-value":["未対応 / UNKNOWN VALUE","replicasが、まだ分からない。","replicas=nullを未知値として扱います。この有限simulatorはcomputed valueを解決しません。","unknown-valueでplan/実行をblocked。nullを0等へ勝手に置換せず、stateを保持。実製品のunknown/computed semanticsとは別の境界です。"],
  "unsupported-attribute":["未対応 / STRICT SCHEMA","知らない属性を、黙って無視しない。","service.webへextra属性を追加。replicas/port/enabled以外は教材schema外です。","unsupported-attributeでblocked。未知の設定を無視して成功へ見せず、stateは変えていません。"],
  "tampered-plan":["拒否 / PLAN BINDING","保存後のactionを、書き換える。","生成planはreplicas3。supplied planのactionだけ4へ変え、processに保持した初期pinはそのままです。","plan-digest-mismatchでblocked。生成時に保持したpinと違うplanを実行しません。独立checkerではpinまで作り直す反例もaction再計算で拒否しました。hashだけは署名ではありません。"],
  "desired-changed":["拒否 / DECLARATION BINDING","plan後に、宣言を変えた。","replicas3でplanを保存し、apply直前のdesiredを4へ変更。旧planへ新宣言を混ぜません。","desired-changedでblocked。宣言digestがplan時の期待値と違うため、旧actionを実行せず現在stateを保持しました。"]
};
const labels={noop:"no-op",reconcile:"reconcile",drift:"計画前drift","stale-revision":"stale revision","silent-drift":"内容だけdrift","delete-blocked":"delete無承認","delete-approved":"delete合成承認","wrong-approval":"別plan承認","unknown-value":"未知値","unsupported-attribute":"未知属性","tampered-plan":"plan改ざん","desired-changed":"宣言変更"};
let selected="noop", step=0, prediction=null;
const row=()=>observation.scenarios.find(r=>r.id===selected);
function node(tag,text,className){const n=document.createElement(tag);n.textContent=text;if(className)n.className=className;return n;}
function resources(target,doc){target.replaceChildren();for(const [id,attrs] of Object.entries(doc.resources)){const box=node("div","","resource");box.append(node("strong",id),node("pre",JSON.stringify(attrs,null,2)));target.append(box);}if(!Object.keys(doc.resources).length)target.append(node("p","resources: empty","small"));}
function stamp(target,doc,digest){target.textContent=`revision ${doc.revision}\n${digest}`;}
function render(){
  const r=row(), info=scenarios[selected];
  $("#case-type").textContent=info[0];$("#case-title").textContent=info[1];$("#case-description").textContent=info[2];
  document.querySelectorAll("[data-case]").forEach(b=>{const is=b.dataset.case===selected;b.classList.toggle("selected",is);b.setAttribute("aria-pressed",String(is));});
  document.querySelectorAll("[data-predict]").forEach(b=>{const is=b.dataset.predict===prediction;b.classList.toggle("selected",is);b.setAttribute("aria-pressed",String(is));});
  $("#steps").replaceChildren(...["1 input","2 diff / plan","3 apply","4 答え"].map((s,i)=>node("span",s,i<step?"active":"")));
  $("#next").disabled=prediction===null||step===4;$("#finish").disabled=prediction===null||step===4;
  $("#next").textContent=["入力を比べる →","diff / planを見る →","apply結果を見る →","答えを見る →","再生完了"][step];
  $("#prediction-note").textContent=step===4?(prediction===r.result.status?"予想と実結果は一致。どのsnapshotを使ったか比較しましょう。":"予想とは違いました。変更・no-op・blockedの境界を確かめましょう。") : "予想を選ぶと、入力と検査を1段ずつ確認できます。";
  $("#replay-note").textContent=`${observation.execution_id} / ${r.observed_at} の保存済み実結果。操作は再生のみ。外部インフラ・製品を操作しません。`;
  $("#observed-badge").textContent="";if(step){resources($("#desired"),r.desired_planning);resources($("#observed"),r.observed_planning);stamp($("#observed-badge"),r.observed_planning,r.plan_created.observed_digest);}else{$("#desired").replaceChildren(node("p","入力比較を進めると表示します。","small"));$("#observed").replaceChildren();}
  $("#actions").replaceChildren();$("#plan-binding").textContent="";
  if(step>=2){$("#plan-title").textContent=r.plan_created.status==="blocked"?"plan自体がblocked。":r.plan_created.actions.length?"保存した変更plan。":"変更なしのplan。";$("#action-count").textContent=String(r.plan_created.actions.length)+" actions";
    if(r.plan_created.status==="blocked")$("#actions").append(node("code",r.plan_created.blocked_reasons.join(", ")));
    for(const action of r.plan_created.actions){const box=node("div","","action");const detail=node("div","");detail.append(node("code",action.id),node("pre",JSON.stringify({before:action.before,after:action.after},null,2)));box.append(node("strong",action.op),detail);$("#actions").append(box);}
    $("#plan-binding").textContent=`保存時のobserved revision: ${r.plan_created.observed_revision}\nobserved hash: ${r.plan_created.observed_digest}\ndesired hash: ${r.plan_created.desired_digest}\nConsumer processが生成時に保持したplan pin: ${r.trusted_plan_digest}`;
  }else{$("#plan-title").textContent="まだplanを見ていません。";$("#action-count").textContent="?";}
  for(const id of ["#timeline","#current-badge","#current-state","#authorization","#decision","#after-badge","#after-state","#second-reconcile"])$(id).replaceChildren();
  $("#result-status").className="result-status";$("#result-status").textContent="未実行";
  if(step>=3){
    $("#timeline").append(node("p",r.drift_events.length?JSON.stringify(r.drift_events):"観測JSONのout-of-band edit eventなし。","timeline"));
    if(selected==="desired-changed")$("#timeline").append(node("p","apply直前のdesired replicas=4。plan時desiredは3。","timeline"));
    if(selected==="tampered-plan")$("#timeline").append(node("p","supplied plan action replicas=4。生成planは3。","timeline"));
    resources($("#current-state"),r.observed_current);stamp($("#current-badge"),r.observed_current,r.result.pre_digest);
    $("#authorization").textContent=r.approval?"合成delete承認input: "+JSON.stringify(r.approval):"合成delete承認input: なし";
    $("#result-status").textContent=r.result.status;$("#result-status").classList.add(r.result.status);
    $("#decision").append(node("div",r.result.reason|| (r.result.status==="noop"?"actions=0 / revision不変":"全action適用 / revision +1"),"decision"));
    resources($("#after-state"),r.result.state);stamp($("#after-badge"),r.result.state,r.result.post_digest);
    if(r.replan){$("#second-reconcile").append(node("strong","2回目: actions 0 → no-op"),node("p","再plan・再applyを実行し、stateとrevisionが同じことを検算しました。"));}
    else $("#second-reconcile").append(node("p","blocked後の自動再plan/retryはしません。現在stateを保持。"));
  }
  $("#trace").textContent=step>=2?JSON.stringify({plan_created:r.plan_created,plan_supplied:r.plan_supplied,apply:step>=3?r.result:"未表示",replan:step>=3?r.replan:"未表示"},null,2):"diff / planを進めると表示します。";
  $("#raw-links").replaceChildren();let names=["desired-planning.json","observed-baseline.json","observed-planning.json","plan-created.json","plan-supplied.json","desired-applying.json","observed-current.json","trusted-plan-pin.json","approval.json","apply-result.json","synthetic-store-after.json","observation.json"];if(r.replan)names.push("replan.json","reapply-result.json");for(const name of names){const a=node("a",name);a.href=`${data.directory}/${selected}/${name}`;$("#raw-links").append(a);}
  $("#answer-title").textContent=step===4?info[1]:"最後に、予想と比べる。";$("#answer-text").textContent=step===4?info[3]:"diff、plan時snapshot、apply直前state、適用結果を別々に見ます。";
}
for(const id of Object.keys(scenarios)){const b=node("button",labels[id]);b.dataset.case=id;b.addEventListener("click",()=>{selected=id;step=0;prediction=null;render();});$("#scenarios").append(b);}
document.querySelectorAll("[data-predict]").forEach(b=>b.addEventListener("click",()=>{prediction=b.dataset.predict;render();}));
$("#next").addEventListener("click",()=>{step=Math.min(4,step+1);render();});$("#finish").addEventListener("click",()=>{step=4;render();});$("#reset").addEventListener("click",()=>{step=0;prediction=null;render();});
const metadata={"Field ID":observation.field_id,"実行ID":observation.execution_id,"UTC観測":`${observation.started_at} — ${observation.completed_at}`,"実行host":`${observation.runtime.os} ${observation.runtime.release} / ${observation.runtime.machine} / CPython ${observation.runtime.python}`,"入力":"合成scope / 最大6resources / revision7のbaseline / 12条件", "試行/上限":"attempt 1 / retry 0 / outer 20秒", "Source bindings":Object.entries(observation.source_bindings).map(([f,d])=>f+" "+d).join(" / "),"実command exit":"原票読取中","変更範囲":"run内の合成JSONだけ / 外部infra不変 / Terraform未実行","未実証":"分散lock/CAS・並行writer・製品provider・全Subject/理解度完成"};
for(const [k,v] of Object.entries(metadata))$("#metadata").append(node("dt",k),node("dd",v));for(const name of ["observation.json","command.json","artifact-index.json"]){const a=node("a",name);a.href=`${data.directory}/${name}`;$("#record-links").append(a);}
fetch(data.directory+"/command.json").then(r=>{if(!r.ok)throw Error("command record unavailable");return r.json();}).then(c=>{$("#command").textContent=JSON.stringify(c,null,2);[...$("#metadata").querySelectorAll("dt")].find(t=>t.textContent==="実command exit").nextElementSibling.textContent=String(c.exit_code);}).catch(e=>{$("#command").textContent=e.message;});
render();

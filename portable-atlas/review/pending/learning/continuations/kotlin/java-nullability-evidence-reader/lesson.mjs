import {cases,labels,snippets,validateReceipt,projectCase} from "./evidence-model.mjs";
const reportPath="evidence/evidence/diagnostics/java-nullability-enhancement-process-pilot.json";
const expectedPath="evidence/labs/java-nullability-enhancement-process-pilot/expected.json";
const pins={report:"8f24466df0e322257474ce6cf414f095aa09ddf21be0f035e9f832698ee732fb",expected:"911575bc4a18d2ba045d1c963459ee9c01aa028aeb6253576d71a5e7012e8110"};
const el=id=>document.getElementById(id),prediction=()=>document.querySelector('input[name="prediction"]:checked')?.value||"";
let current="normal",generation=0,controller=null,observation=null;
function invalidate(message,clearPrediction=false){
 generation++;controller?.abort();controller=null;observation=null;
 if(clearPrediction)document.querySelectorAll('input[name="prediction"]').forEach(r=>r.checked=false);
 for(const id of ["result","answer","load-error"])el(id).hidden=true;
 for(const id of ["provenance","outcome","record","expected","digest-note","raw","verdict","explanation","load-error"])el(id).textContent="";
 el("comparison").replaceChildren();el("raw-details").open=false;
 el("load").disabled=!prediction();el("answer-button").disabled=true;el("status").textContent=message;
}
function showCase(){
 document.querySelectorAll("[data-case]").forEach(b=>b.setAttribute("aria-pressed",String(b.dataset.case===current)));
 el("snippet").textContent=snippets[current];
 const steps=current==="rejection"?["1. Java引数の@NotNull宣言","2. Kotlinからnullを渡すコード","3. compileの受理/拒否を確認"]:["1. Java戻り値の@NotNull宣言","2. Kotlin側がlengthを利用","3. Java実装が返す値とruntimeを比較"];
 ["flow-one","flow-two","flow-three"].forEach((id,i)=>el(id).textContent=steps[i]);
}
document.querySelectorAll("[data-case]").forEach(b=>b.addEventListener("click",()=>{current=b.dataset.case;showCase();invalidate("条件が変わりました。予想を選んでください。",true);}));
document.querySelectorAll('input[name="prediction"]').forEach(r=>r.addEventListener("change",()=>invalidate("予想を保存しました。証拠を読めます。")));
el("reset").addEventListener("click",()=>{current="normal";showCase();invalidate("最初の状態へ戻しました。",true);});
const digest=async bytes=>[...new Uint8Array(await crypto.subtle.digest("SHA-256",bytes))].map(v=>v.toString(16).padStart(2,"0")).join("");
async function loadJSON(path,pin,signal){
 const response=await fetch(path,{signal,cache:"no-store",credentials:"same-origin"});
 if(!response.ok)throw new Error("HTTP "+response.status+"：資料を取得できません。");
 const bytes=await response.arrayBuffer();if(await digest(bytes)!==pin)throw new Error("資料のSHA-256が固定記録と一致しません。");
 return JSON.parse(new TextDecoder().decode(bytes));
}
el("load").addEventListener("click",async()=>{
 if(!prediction())return;invalidate("保存JSONを取得・照合しています。native実行はしません。");
 const token=generation,chosen=current;controller=new AbortController();const signal=controller.signal;el("load").disabled=true;
 try{
  const [receipt,expected]=await Promise.all([loadJSON(reportPath,pins.report,signal),loadJSON(expectedPath,pins.expected,signal)]);
  validateReceipt(receipt,expected);
  for(const id of ["normal","boundary"]){const sha=await digest(new TextEncoder().encode(expected[id].stdout));if("sha256:"+sha!==receipt.runtime_cases.find(r=>r.name===id).stdout_digest)throw new Error("固定期待文字列と保存stdout digestが一致しません。");}
  if(token!==generation)return;
  const row=projectCase(receipt,expected,chosen);observation=row;
  el("outcome").textContent=row.outcome;el("record").textContent=row.record;el("expected").textContent=row.expectation;el("digest-note").textContent=row.digestNote+(chosen==="normal"||chosen==="boundary"?" 今回の読取でもdigest一致を確認しました。":"");
  el("raw").textContent=JSON.stringify(row.raw,null,2);
  el("provenance").textContent="元原票：Kotlin 2.4.10 / JDK 17.0.17、SHA-256 "+pins.report.slice(0,16)+"… を照合。元の実行日時は未保存です。";
  for(const id of cases){const tr=document.createElement("tr");for(const text of projectCase(receipt,expected,id).comparison){const td=document.createElement("td");td.textContent=text;tr.appendChild(td);}el("comparison").appendChild(tr);}
  el("result").hidden=false;el("answer-button").disabled=false;el("status").textContent="保存記録と固定期待値を照合しました。原典・実装を読み、答えと比較できます。新たな実行結果ではありません。";
 }catch(error){
  if(token!==generation)return;
  invalidate("資料を表示できませんでした。取得を再試行できます。");
  el("load-error").textContent="資料の取得・照合失敗です。compile拒否やNPEの観測ではありません。 "+(location.protocol==="file:"?"READMEの手順で127.0.0.1のHTTPサーバーから開いてください。":error.message);el("load-error").hidden=false;
 }finally{if(token===generation){controller=null;el("load").disabled=!prediction();}}
});
el("answer-button").addEventListener("click",()=>{if(!observation||!prediction())return;el("verdict").textContent=prediction()===observation.kind?"予想と元原票の記録は一致しました。":"予想と元原票の記録は異なりました。起きた段階を見直しましょう。";el("explanation").textContent=observation.explanation;el("answer").hidden=false;});
showCase();invalidate("予想を選んでください。",true);

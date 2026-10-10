"use strict";
const MANIFEST_SHA="4c73f40f70d4f72114a20bac37c8346c14ce8c257d1889cff3a622537ba07b3b";
const $=id=>document.getElementById(id);
const ids=["seq-synchronized","seq-publication","seq-none","concurrent-synchronized","concurrent-publication"];
const stages=["読む前","読み終えた結果","期待値と終了確認"];
let generation=0,controller=null,record=null,expected=null,manifest=null,stage=0;
const selected=()=>document.querySelector('input[name="case"]:checked').value;
function clear(message="予想や条件を変えました。記録を開き直して確かめてください。"){
 generation++;controller?.abort();controller=null;record=null;expected=null;manifest=null;stage=0;
 $("result").hidden=true;$("empty").hidden=false;$("answer").hidden=true;$("answer-button").disabled=true;$("previous").disabled=true;$("next").disabled=true;$("load").disabled=!$("prediction").value.trim();
 for(const id of ["case-label","result-kind","phase-title","phase-note","diagram","comparison","interpretation","raw","answer-text","prediction-copy"])$(id).textContent="";
 $("raw-details").open=false;$("status").textContent=message;$("status").className="";
}
async function checkedJSON(path,pin,signal){
 const response=await fetch(path,{cache:"no-store",signal});if(!response.ok)throw new Error("HTTP "+response.status);
 const bytes=await response.arrayBuffer(),digest=Array.from(new Uint8Array(await crypto.subtle.digest("SHA-256",bytes)),v=>v.toString(16).padStart(2,"0")).join("");
 if(digest!==pin)throw new Error("保存した記録のハッシュが一致しません");return JSON.parse(new TextDecoder().decode(bytes));
}
function shape(r,e){
 if(r.project!=="Atlas"||r.collection_complete!==true||r.errors.length||r.records.length!==7||r.compile_count!==1||r.jvm_count!==1)throw new Error("完了した五条件の記録ではありません");
 if(JSON.stringify(r.records.slice(1,-1).map(c=>c.id))!==JSON.stringify(ids)||JSON.stringify(e.cases.map(c=>c.id))!==JSON.stringify(ids))throw new Error("条件の対応が異なります");
 for(const [i,c] of r.records.slice(1,-1).entries())if(!c.collection_complete||c.failures.length||!e.cases[i].allowed_counts.includes(c.count_after)||c.reads.length!==e.cases[i].read_count)throw new Error("未完了または期待範囲外の条件があります");
}
function node(name,attrs={},text){const n=document.createElementNS("http://www.w3.org/2000/svg",name);for(const [k,v]of Object.entries(attrs))n.setAttribute(k,v);if(text!==undefined)n.textContent=text;return n;}
function draw(c){
 const small=window.innerWidth<=600;
 const svg=node("svg",{viewBox:small?"0 0 360 365":"0 0 640 245",role:"img","aria-label":"保存した読取りと共有される Token の模型"});
 const defs=node("defs"),marker=node("marker",{id:"arrow",viewBox:"0 0 10 10",refX:9,refY:5,markerWidth:5,markerHeight:5,orient:"auto"});marker.append(node("path",{d:"M 0 0 L 10 5 L 0 10 z",fill:"#247b9c"}));defs.append(marker);svg.append(defs);
 svg.append(node("rect",{x:small?18:388,y:small?213:40,width:small?324:234,height:small?104:147,rx:12,fill:"#dff0f4",stroke:"#80aebe"}),node("text",{x:small?34:406,y:small?241:73,"font-size":20,fill:"#163a50"},stage?"保持した Token":"まだ初期化していない"));
 const readers=c.workers?["worker-1","worker-2","main-after-workers"]:["main-1","main-2"];
 readers.forEach((reader,i)=>{const y=52+i*61;svg.append(node("text",{x:18,y,"font-size":18,fill:"#163a50"},reader),node("text",{x:18,y:y+24,"font-size":16,fill:"#527385"},stage?"読取り済み":"まだ読んでいない"));if(stage)svg.append(node("line",{x1:221,y1:y+7,x2:small?322:379,y2:small?203:110,stroke:"#247b9c","stroke-width":3,"marker-end":"url(#arrow)"}));});
 svg.append(node("text",{x:small?34:406,y:small?270:110,"font-size":19,fill:"#163a50"},stage?`id ${c.reads[0].id} / marker ${c.reads[0].marker}`:"count 0"),node("text",{x:small?34:406,y:small?299:145,"font-size":18,fill:"#163a50"},stage?"同じ参照（===）":"結果は未再生"),node("text",{x:18,y:small?347:225,"font-size":17,fill:"#163a50"},stage?`初期化関数 ${c.count_after} 回 / 読取り ${c.reads.length} 回`:"各条件は新しい Lazy から開始"));
 $("diagram").replaceChildren(svg);
}
function render(){
 const c=record.records.find(c=>c.id===selected()),w=expected.cases.find(c=>c.id===selected());
 $("result").hidden=false;$("empty").hidden=true;$("case-label").textContent=c.mode+" / "+(c.workers?"2 worker + 終了後の main":"main の逐次 2 回");
 $("result-kind").textContent=stage===2?"保存した正常終了を固定期待値と比較":"保存した実行の再生";
 $("phase-title").textContent=`${stage+1} / 3　${stages[stage]}`;$("previous").disabled=stage===0;$("next").disabled=stage===2;$("answer-button").disabled=stage!==2;
 $("phase-note").textContent=stage===0?"読む前の count は 0、isInitialized は false。以後の値はまだ表示しません。":stage===1?"全ての読取りが返した値です。二者の条件では、main は両 Future の終了後に読みました。":"手書き期待値の計算回数："+w.allowed_counts.join(" または ")+"。今回："+c.count_after+"。"+(c.workers?"二つの worker の終了を確認済み。":"追加 worker は作成していません。");
 draw(c);$("comparison").replaceChildren();
 const readers=c.workers?["worker-1","worker-2","main-after-workers"]:["main-1","main-2"];
 for(const [i,reader]of readers.entries()){const tr=document.createElement("tr"),r=c.reads[i];for(const text of stage?[reader,`${r.id} / ${r.marker}`,String(r.same_reference_as_first)]:[reader+" / 未再生","未再生","未再生"]){const td=document.createElement("td");td.textContent=text;tr.append(td);}$("comparison").append(tr);}
 $("interpretation").textContent=`実行日時 ${record.started_at} / Java ${record.records[0].java_version} / Kotlin ${record.records[0].kotlin_version}。`+(stage===2&&c.id==="concurrent-publication"?(c.count_after===1?"今回の計算は 1 回。複数回計算は未観測で、再試行して 2 回を狙いません。":"今回の計算は 2 回。計算した Token が二つでも、読取りは同じ参照を返しました。"):"画面操作による実験の再実行はありません。");
 const current=stage===0?{case_id:c.id,mode:c.mode,initial_count:c.initial_count,initial_initialized:c.initial_initialized}:stage===1?{case_id:c.id,count_after:c.count_after,initialized_after:c.initialized_after,reads:c.reads,events:c.events}:{case:c,expected:w};
 $("raw").textContent=JSON.stringify({started_at:record.started_at,...current,run_path:manifest.observation.path},null,2);
 $("answer").hidden=true;$("answer-text").textContent="";$("prediction-copy").textContent="";
}
$("load").addEventListener("click",async()=>{
 if(!$("prediction").value.trim())return;clear("保存した記録を取得し、ハッシュを確認しています。");const token=generation;controller=new AbortController();const signal=controller.signal;$("load").disabled=true;
 try{const m=await checkedJSON("reader-data.json",MANIFEST_SHA,signal);if(token!==generation)return;
 if(m.state==="not-executed"){clear("実測は未実施です。"+m.reason+"。結果はありません。固定期待値と公式規則を読み、予想と比べてください。");return;}
 const [r,e]=await Promise.all([checkedJSON(m.observation.path,m.observation.sha256,signal),checkedJSON(m.expected.path,m.expected.sha256,signal)]);shape(r,e);if(token!==generation)return;manifest=m;record=r;expected=e;render();$("status").textContent="保存した記録の照合が完了しました。Kotlin は再実行していません。";}
 catch(error){if(token!==generation)return;clear();$("status").textContent="資料の読込みに失敗："+error.message+"。表示は消去しました。同じボタンで再取得できます。";$("status").className="error";}
 finally{if(token===generation)$("load").disabled=!$("prediction").value.trim();}
});
for(const radio of document.querySelectorAll('input[name="case"]'))radio.addEventListener("change",()=>{$("prediction").value="";clear();});
$("prediction").addEventListener("input",()=>clear());
$("reset").addEventListener("click",()=>{document.querySelector('input[value="seq-synchronized"]').checked=true;$("prediction").value="";clear("最初の条件に戻しました。予想と結果は空です。");});
$("previous").addEventListener("click",()=>{if(record&&stage>0){stage--;render();}});$("next").addEventListener("click",()=>{if(record&&stage<2){stage++;render();}});
window.addEventListener("resize",()=>{if(record)draw(record.records.find(c=>c.id===selected()));});
$("answer-button").addEventListener("click",()=>{if(!record||stage!==2)return;const c=record.records.find(c=>c.id===selected());$("answer").hidden=false;$("answer-text").textContent=`今回の計算は ${c.count_after} 回、返った ${c.reads.length} 個の結果は同じ参照でした。`+(c.id==="concurrent-publication"?"PUBLICATION の許容範囲は 1〜2 回です。今回の回数を全ての実行の保証にしません。":c.id==="seq-none"?"NONE の逐次成功です。並行安全性は確認していません。":"今回の有限入力は、先に固定した期待値と一致しています。")+" id/marker の一致と === による参照同一性は別々に観測しています。";$("prediction-copy").textContent="あなたの予想："+$("prediction").value.trim();});

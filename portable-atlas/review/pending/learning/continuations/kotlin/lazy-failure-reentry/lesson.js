"use strict";
const MANIFEST_SHA="f917fd7ef867c07ce2d8629f0a6b0adc00bb73e1a7548ac7657ec7a21c051ebe";
const $=id=>document.getElementById(id),ids=["failure-synchronized","failure-publication","failure-none","reentry-synchronized","reentry-publication","reentry-none"];
let generation=0,controller=null,record=null,expected=null,manifest=null,stage=0;
const selected=()=>document.querySelector('input[name="case"]:checked').value;
const currentCase=()=>record.records.find(c=>c.kind==="case"&&c.id===selected());
const labels={initial:"読む前","first-failure":"最初の読取りは期待した例外","retry-success":"次のアクセスで成功","cached-read":"さらに読む","inner-returned":"内側の getter から戻る","outer-getter-returned":"外側の getter から戻る"};
const roles={"inner-getter":"内側 getter の返却","outer-created":"外側が生成した候補","outer-initializer-return":"外側 initializer の返却","outer-getter":"外側 getter の返却","retry-getter":"例外後の getter の返却","later-getter":"後の getter の返却"};
function clear(message="予想や条件を変えました。測定結果を開き直してください。"){
 generation++;controller?.abort();controller=null;record=null;expected=null;manifest=null;stage=0;
 $("result").hidden=true;$("empty").hidden=false;$("answer").hidden=true;
 for(const id of ["previous","next","answer-button"])$(id).disabled=true;
 $("load").disabled=!$("prediction").value.trim();
 for(const id of ["case-label","result-kind","phase-title","phase-note","diagram","comparison","interpretation","raw","answer-text","prediction-copy"])$(id).textContent="";
 $("raw-details").open=false;$("status").textContent=message;$("status").className="";
}
async function checkedJSON(path,pin,signal){
 const response=await fetch(path,{cache:"no-store",signal});if(!response.ok)throw Error("HTTP "+response.status);
 const bytes=await response.arrayBuffer(),sha=Array.from(new Uint8Array(await crypto.subtle.digest("SHA-256",bytes)),v=>v.toString(16).padStart(2,"0")).join("");
 if(sha!==pin)throw Error("保存した記録のハッシュが一致しません");return JSON.parse(new TextDecoder().decode(bytes));
}
function shape(r,e){
 const cases=r.records?.filter(c=>c.kind==="case");
 if(r.project!=="Atlas"||!r.collection_complete||r.errors.length||r.compile_count!==1||r.jvm_count!==1||JSON.stringify(cases?.map(c=>c.id))!==JSON.stringify(ids)||JSON.stringify(e.case_order)!==JSON.stringify(ids))throw Error("完了した6条件の記録ではありません");
 for(const c of cases)if(!c.collection_complete||c.failures.length||c.phases.length!==4||c.calls_total!==2)throw Error("未完了の条件があります");
}
function node(name,attrs={},text){const n=document.createElementNS("http://www.w3.org/2000/svg",name);for(const[k,v]of Object.entries(attrs))n.setAttribute(k,v);if(text!==undefined)n.textContent=text;return n;}
function draw(p){
 const entries=Object.entries(p.known_references),height=Math.max(190,118+entries.length*69),width=window.innerWidth<=600?360:540,svg=node("svg",{viewBox:`0 0 ${width} ${height}`,role:"img","aria-label":"その時点で記録済みの返却値の模型"});
 svg.append(node("text",{x:16,y:29,fill:"#163a50","font-size":20},`呼出し ${p.calls} 回 / 初期化済み ${p.initialized}`));
 if(!entries.length)svg.append(node("text",{x:16,y:84,fill:"#163a50","font-size":19},p.outcome==="expected-initializer-exception"?"期待した例外。返った値はない":"まだ値を読んでいない"));
 for(const[i,[role,t]]of entries.entries()){const y=58+i*69;svg.append(node("rect",{x:8,y,width:width-17,height:59,rx:9,fill:"#e2f0f3"}),node("text",{x:19,y:y+23,fill:"#163a50","font-size":18},roles[role]),node("text",{x:19,y:y+46,fill:"#163a50","font-size":17},`→ Token ${t.id} / marker ${t.marker}`));}
 svg.append(node("text",{x:16,y:height-32,fill:"#527385","font-size":16},"番号は呼出し順。"),node("text",{x:16,y:height-12,fill:"#527385","font-size":16},"内部cacheを直接見た図ではない"));$("diagram").replaceChildren(svg);
}
function render(){
 const c=currentCase(),p=c.phases[stage];$("result").hidden=false;$("empty").hidden=true;
 $("case-label").textContent=c.mode+" / "+(c.family==="failure"?"例外後の再試行・公開規則との対照":"再入・固定 JVM 実装だけの観測");
 $("result-kind").textContent=p.outcome==="expected-initializer-exception"?"意図した initializer 例外":stage===0?"読む前の保存状態":"正常に返った保存結果";
 $("phase-title").textContent=`${stage+1} / 4　${labels[p.id]}`;$("previous").disabled=stage===0;$("next").disabled=stage===3;$("answer-button").disabled=stage!==3;
 $("phase-note").textContent=p.id==="inner-returned"?"内側は戻りましたが外側はまだ初期化中です。外側候補や後の返却値はまだ表示しません。":p.outcome==="expected-initializer-exception"?"呼出し1の専用例外をcatchしました。資料の取得失敗とは別です。":"この時点までに記録した参照だけを表示します。";
 draw(p);$("comparison").replaceChildren();
 const rows=[["呼出し回数",p.calls],["isInitialized",p.initialized],["initializer の深さ",p.depth],["生成した id の順",p.created_ids.join(" → ")||"まだなし"],...Object.entries(p.known_references).map(([k,t])=>[roles[k],`id ${t.id} / marker ${t.marker}`])];
 if(p.planned_exceptions_so_far.length)rows.push(["期待した例外",p.planned_exceptions_so_far[0].type]);
 if(stage===3&&c.family==="reentry")rows.push(["外側 getter === 内側 getter",c.comparisons.first_same_as_inner],["外側 getter === 外側生成候補",c.comparisons.first_same_as_outer_created],["後の getter === 外側 getter",c.comparisons.later_same_as_first]);
 for(const row of rows){const tr=document.createElement("tr");for(const value of row){const td=document.createElement("td");td.textContent=String(value);tr.append(td);}$("comparison").append(tr);}
 $("interpretation").textContent=`実行日時 ${record.started_at}。画面操作は保存結果の再生です。`;
 $("raw").textContent=JSON.stringify({case_id:c.id,mode:c.mode,phase:p,...(stage===3?{comparisons:c.comparisons}:{}),run_path:manifest.observation.path},null,2);
 $("answer").hidden=true;$("answer-text").textContent="";$("prediction-copy").textContent="";
}
$("load").addEventListener("click",async()=>{
 if(!$("prediction").value.trim())return;clear("保存した測定結果を取得し、ハッシュを確認しています。");const token=generation;controller=new AbortController();const signal=controller.signal;$("load").disabled=true;
 try{const m=await checkedJSON("reader-data.json",MANIFEST_SHA,signal);if(token!==generation)return;
 if(!m.observation){clear("実測は未実施です。契約・手書き期待値・固定原典を読んでください。測定値はありません。");return;}
 const[r,e]=await Promise.all([checkedJSON(m.observation.path,m.observation.sha256,signal),checkedJSON(m.expected.path,m.expected.sha256,signal)]);shape(r,e);if(token!==generation)return;
 manifest=m;record=r;expected=e;render();$("status").textContent="保存した測定結果の照合が完了しました。Kotlin は起動していません。";}
 catch(error){if(token!==generation)return;clear();$("status").textContent="資料の取得失敗："+error.message+"。結果を消去しました。再取得できます。これは initializer の例外ではありません。";$("status").className="error";}
 finally{if(token===generation)$("load").disabled=!$("prediction").value.trim();}
});
for(const radio of document.querySelectorAll('input[name="case"]'))radio.addEventListener("change",()=>{$("prediction").value="";clear();});
$("prediction").addEventListener("input",()=>clear());
$("reset").addEventListener("click",()=>{document.querySelector('input[value="failure-synchronized"]').checked=true;$("prediction").value="";clear("最初の条件へ戻りました。予想と結果は空です。");});
$("previous").addEventListener("click",()=>{if(record&&stage>0){stage--;render();}});$("next").addEventListener("click",()=>{if(record&&stage<3){stage++;render();}});
$("answer-button").addEventListener("click",()=>{if(!record||stage!==3)return;const c=currentCase(),w=expected[c.family];$("answer").hidden=false;
 $("answer-text").textContent=c.family==="failure"?`呼出し回数 ${w.calls.join(" → ")} の期待に対し、今回も ${c.phases.map(p=>p.calls).join(" → ")}。最初の例外後は未初期化、次は成功し再読は同じ参照でした。副作用の巻戻しは測っていません。`:`内側が返した2、外側が作った1、外側getterが返した${c.reads["outer-getter"].id}を区別します。外側getter === 内側getter は ${c.comparisons.first_same_as_inner}、外側getter === 外側生成候補 は ${c.comparisons.first_same_as_outer_created}。後の読取りは外側getterと同じ参照（=== ${c.comparisons.later_same_as_first}）。固定期待 ${w[c.mode].first_id} と一致しています。この再入手順の固定JVM実装観測で、一般的なAPI保証ではありません。`;
 $("prediction-copy").textContent="あなたの予想："+$("prediction").value.trim();});

window.addEventListener("resize",()=>{if(record)draw(currentCase().phases[stage]);});

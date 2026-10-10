"use strict";
const MANIFEST_SHA="ca43f69387453b323397de34f429bd2d43c7a4738c5993dca8ece0f0893be3ca";
const $=id=>document.getElementById(id);
const phaseNames=["親：fork の前","子：fork の後","子：exec の後","親：wait の後"];
const caseNames={guarded_single:"元だけ・印 on",unguarded_single:"元だけ・印 off（設定漏れの対照）",dup_original_guarded:"元 on / 複製 off",dup_duplicate_guarded:"元 off / 複製 on"};
let generation=0,controller=null,record=null,expected=null,manifest=null,stage=0;
const selected=()=>document.querySelector('input[name="case"]:checked').value;
function invalidate(message="予想や条件を変更しました。記録を開いて確かめてください。"){
 generation++;controller?.abort();controller=null;record=null;expected=null;manifest=null;stage=0;
 $("result").hidden=true;$("empty").hidden=false;$("answer").hidden=true;$("answer-button").disabled=true;$("previous").disabled=true;$("next").disabled=true;$("load").disabled=!$("prediction").value.trim();
 for(const id of ["case-label","result-kind","phase-title","phase-note","diagram","comparison","interpretation","raw","answer-text","prediction-copy"])$(id).textContent="";
 $("raw-details").open=false;$("status").textContent=message;$("status").className="";
}
async function checkedJSON(path,pin,signal){
 const response=await fetch(path,{cache:"no-store",signal});if(!response.ok)throw new Error("HTTP "+response.status);
 const bytes=await response.arrayBuffer();const digest=Array.from(new Uint8Array(await crypto.subtle.digest("SHA-256",bytes)),v=>v.toString(16).padStart(2,"0")).join("");
 if(digest!==pin)throw new Error("保存した記録のハッシュが一致しません");return JSON.parse(new TextDecoder().decode(bytes));
}
function shape(run,fixed){
 if(run.project!=="Atlas"||run.collection_complete!==true||run.errors.length!==0||run.cases.length!==4)throw new Error("完了した4条件の記録ではありません");
 const wanted=Object.keys(caseNames);if(JSON.stringify(run.cases.map(c=>c.id))!==JSON.stringify(wanted))throw new Error("条件の並びが異なります");
 for(const c of run.cases){if(!c.complete||c.errors.length||JSON.stringify(c.phases.map(p=>p.phase))!==JSON.stringify(fixed.phases))throw new Error("途中で失敗した条件があります");}
}
function bytesText(row){if(row.status!=="target")return "読取なし";return '"'+String.fromCharCode(...row.bytes_hex.match(/../g).map(x=>parseInt(x,16)))+'"';}
function fdText(row){if(!row)return "複製なし";if(row.status==="EBADF")return `FD ${row.fd}\n期待した拒否：EBADF\nerrno ${row.errno} / 読取なし`;
 return `FD ${row.fd} / 印 ${row.cloexec?"on":"off"}\n対象 ${row.identity.join(" / ")}\n${bytesText(row)}`;}
function svgElement(name,attrs={},content){const n=document.createElementNS("http://www.w3.org/2000/svg",name);for(const [k,v] of Object.entries(attrs))n.setAttribute(k,v);if(content!==undefined)n.textContent=content;return n;}
function diagram(phase){
 const svg=svgElement("svg",{viewBox:"0 0 640 220",role:"img","aria-label":phaseNames[stage]+"のFD番号と対象ファイルの模型"});
 const defs=svgElement("defs"),marker=svgElement("marker",{id:"arrow",viewBox:"0 0 10 10",refX:9,refY:5,markerWidth:5,markerHeight:5,orient:"auto-start-reverse"});marker.append(svgElement("path",{d:"M 0 0 L 10 5 L 0 10 z",fill:"#247b9c"}));defs.append(marker);svg.append(defs);
 svg.append(svgElement("rect",{x:14,y:16,width:308,height:188,rx:12,fill:"white",stroke:"#91b9c9"}),svgElement("text",{x:30,y:48,"font-size":20,fill:"#163a50"},`${stage===0||stage===3?"親":"子"} PID ${phase.pid}`));
 const rows=["original","duplicate"].filter(label=>phase.fds[label]).map(label=>[label,phase.fds[label]]);for(const [i,[label,row]] of rows.entries()){
 const y=84+i*60;svg.append(svgElement("text",{x:30,y,"font-size":20,fill:"#163a50"},`${label==="original"?"元":"複製"} FD ${row.fd}`));
 svg.append(svgElement("text",{x:30,y:y+24,"font-size":16,fill:row.status==="EBADF"?"#98612e":"#527385"},row.status==="EBADF"?"EBADF：参照なし":`印 ${row.cloexec?"on":"off"} / 対象あり`));
 if(row.status==="target")svg.append(svgElement("line",{x1:224,y1:y+4,x2:421,y2:111,stroke:"#247b9c","stroke-width":3,"marker-end":"url(#arrow)"}));
 else svg.append(svgElement("line",{x1:224,y1:y+4,x2:357,y2:y+4,stroke:"#af8153","stroke-width":3,"stroke-dasharray":"7 5"}),svgElement("text",{x:360,y:y+11,"font-size":24,fill:"#98612e"},"×"));
 }
 svg.append(svgElement("rect",{x:431,y:59,width:190,height:102,rx:12,fill:"#dff0f4",stroke:"#80aebe"}),svgElement("text",{x:449,y:94,"font-size":19,fill:"#163a50"},"対象ファイル"),svgElement("text",{x:449,y:126,"font-size":18,fill:"#163a50"},"ATLAS-FD / 8 B"));
 $("diagram").replaceChildren(svg);
}
function render(){
 const c=record.cases.find(c=>c.id===selected()),phase=c.phases[stage];$("result").hidden=false;$("empty").hidden=true;
 $("case-label").textContent=caseNames[c.id];$("result-kind").textContent=c.id==="unguarded_single"?"設定漏れで継承が残る対照":"保存した正常操作と期待拒否";
 $("phase-title").textContent=`${stage+1} / 4　${phaseNames[stage]}`;$("previous").disabled=stage===0;$("next").disabled=stage===3;$("answer-button").disabled=stage!==3;
 $("phase-note").textContent=["これから子を作ります。各FDの印と参照先を確認します。","印 on でも fork 直後の子には対象があります。親とは別PIDです。","同じ子PIDでプログラムを切替えた後です。印 on のFDは今回EBADFになりました。","子の終了を wait で回収しました。親のFDは対象を保っています。"][stage];
 diagram(phase);$("comparison").replaceChildren();for(const [i,p] of c.phases.entries()){const tr=document.createElement("tr");for(const text of i>stage?[phaseNames[i]+"\n未再生","未再生","未再生"]:[phaseNames[i]+"\nPID "+p.pid,fdText(p.fds.original),fdText(p.fds.duplicate)]){const td=document.createElement("td");td.textContent=text;if(i===stage)td.className="current";tr.append(td);}$("comparison").append(tr);}
 $("interpretation").textContent=`実行日時 ${record.started_at} / ${record.environment.platform} / Python 3.9.6。子の終了コード ${c.wait.exit_code}、終了回収 ${c.cleanup.child_reaped?"済み":"未確認"}。EBADFは予想した拒否で、記録の取得失敗とは別です。`;
 $("raw").textContent=JSON.stringify({environment:record.environment,started_at:record.started_at,...(stage===3?{case:c}:{case_id:c.id,phase}),run_path:manifest.observation.path},null,2);
 $("answer").hidden=true;$("answer-text").textContent="";$("prediction-copy").textContent="";
}
$("load").addEventListener("click",async()=>{
 if(!$("prediction").value.trim())return;
 invalidate("保存した記録を読み込み、ハッシュを照合しています。");const token=generation;controller=new AbortController();const signal=controller.signal;$("load").disabled=true;
 try{const m=await checkedJSON("reader-data.json",MANIFEST_SHA,signal);const [r,e]=await Promise.all([checkedJSON(m.observation.path,m.observation.sha256,signal),checkedJSON(m.expected.path,m.expected.sha256,signal)]);shape(r,e);if(token!==generation)return;manifest=m;record=r;expected=e;stage=0;render();$("status").textContent="保存した記録の照合が完了しました。次の時点へ進めてください。OSの再実行はしていません。";}
 catch(error){if(token!==generation)return;invalidate();$("status").textContent="資料の読込みに失敗："+error.message+"。結果は消去しました。同じボタンで再取得できます。";$("status").className="error";}
 finally{if(token===generation)$("load").disabled=!$("prediction").value.trim();}
});
for(const radio of document.querySelectorAll('input[name="case"]'))radio.addEventListener("change",()=>{$("prediction").value="";invalidate();});
$("prediction").addEventListener("input",()=>invalidate());
$("reset").addEventListener("click",()=>{document.querySelector('input[value="guarded_single"]').checked=true;$("prediction").value="";invalidate("最初の条件に戻しました。予想と記録の表示は空です。");});
$("previous").addEventListener("click",()=>{if(record&&stage>0){stage--;render();}});$("next").addEventListener("click",()=>{if(record&&stage<3){stage++;render();}});
$("answer-button").addEventListener("click",()=>{if(!record||stage!==3)return;$("answer").hidden=false;$("answer-text").textContent="fork後は全ての対象FDを保持し、exec後は印onのFDだけが今回EBADFになりました。印offでは対象ファイルを引き継ぎます。複製したFDの印は個別で、子の終了後も親の参照は残ります。設定漏れを避けるには、渡すFDと印を各々確認します。";$("prediction-copy").textContent="あなたの予想："+($("prediction").value.trim()||"（未入力）");});

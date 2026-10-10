"use strict";
const data=window.UDP_OBSERVATION;
const $=id=>document.getElementById(id);
let active=0,step=0;
function json(v){return JSON.stringify(v,null,2)}
function readable(hex){if(hex==="")return "b''（空payload）";return String.fromCharCode(...hex.match(/../g).map(v=>parseInt(v,16)))}
function outcomes(){return data.raw.cases[active].events.filter(e=>["recvfrom-return","recvfrom-timeout"].includes(e.kind))}
function render(){
 const c=data.contracts.cases[active],raw=data.raw.cases[active],results=outcomes();
 $("sent").replaceChildren();
 raw.events.filter(e=>e.kind==="sendto-return").forEach((e,i)=>{let card=document.createElement("article");let title=document.createElement("strong");title.textContent=`sendto #${e.number} · ${readable(c.sent_hex[i])}`;let p=document.createElement("p");p.textContent=`hex ${c.sent_hex[i]||"∅"} / return ${e.returned_bytes} bytes`;card.append(title,p);$("sent").append(card)});
 $("endpoints").textContent=`所有sender ${raw.sender.join(":")} → receiver ${raw.receiver.join(":")} / 動的port / timeout ${data.raw.timeout_seconds}秒`;
 $("timeline").replaceChildren();
 results.slice(0,step).forEach((e,i)=>{let item=document.createElement("div");item.className="trace"+(e.kind==="recvfrom-timeout"?" timeout":"");let badge=document.createElement("strong");badge.textContent=`recv #${i+1}`;let body=document.createElement("div");let p=document.createElement("p");p.textContent=e.kind==="recvfrom-timeout"?`timeout例外: ${e.exception} / ${e.message}`:`${readable(e.payload_hex)} · ${e.byte_count} bytes · hex ${e.payload_hex||"∅"}`;let detail=document.createElement("p");detail.textContent=`recvfrom(${c.recv_widths[i]}, flags=0)`+(e.sender?` / sender ${e.sender.join(":")}`:" / dataもsenderも返らない");let time=document.createElement("small");time.textContent=`${e.at} / 経過 ${e.elapsed_ns} ns`;body.append(p,detail,time);item.append(badge,body);$("timeline").append(item)});
 $("advance").disabled=step===results.length;
 $("progress").textContent=step===0?"予想を選び、保存したrecvを1回ずつ進める。":`${step} / ${results.length} recvを表示`;
 $("comparison").hidden=step!==results.length;
 const prototype=raw.consumer_prototypes;
 $("candidate").textContent=json(prototype.datagram_candidates.map(readable));
 $("eof").textContent=json(prototype.tcp_eof_fault.map(readable));
 $("join").textContent=readable(prototype.stream_join_fault);
 const observed=results.map(e=>e.kind==="recvfrom-timeout"?null:e.payload_hex),matched=JSON.stringify(observed)===JSON.stringify(c.expected_hex);
 $("oracle").textContent=`事前手書きhex: ${json(c.expected_hex)}\n保存原票hex: ${json(observed)}\n${matched?"独立期待と一致":"不一致・原票を確認"}（nullはtimeout）`;
 $("prediction-result").textContent=$("prediction").value==="datagram"?"予想は今回の原票と整合。ただしUDP配送/順序保証へ一般化しない。":$("prediction").value?"予想を見直す：空はEOFではなく、末尾は戻らず、同順序到達の保証もない。":"予想未選択。原票と契約を比較する。";
 $("answer-text").textContent=c.answer;
 $("raw").textContent=json(raw);
 $("rawlinks").replaceChildren();
 [["raw / 実recvとcleanup","raw.json"],["実command stdout/stderr","command.json"],["入力契約","contracts.json"],["source / artifact digest","manifest.json"]].forEach(([label,file],i)=>{if(i)$("rawlinks").append(" · ");let a=document.createElement("a");a.textContent=label;a.href=`observations/${data.run_id}/${file}`;$("rawlinks").append(a)});
 $("environment").textContent=`Run ${data.run_id} / ${data.raw.started_at} → ${data.raw.ended_at} / Python ${data.raw.environment.python} / ${data.raw.environment.os} ${data.raw.environment.release} ${data.raw.environment.machine} / stdlib`;
}
data.contracts.cases.forEach((c,i)=>{const o=document.createElement("option");o.value=i;o.textContent=c.label;$("scenario").append(o)});
$("scenario").addEventListener("change",()=>{active=Number($("scenario").value);step=0;$("prediction").value="";$("answer").open=false;render()});
$("advance").addEventListener("click",()=>{if(step<outcomes().length)step++;render()});
$("reset").addEventListener("click",()=>{step=0;$("answer").open=false;render()});
$("prediction").addEventListener("change",render);
render();

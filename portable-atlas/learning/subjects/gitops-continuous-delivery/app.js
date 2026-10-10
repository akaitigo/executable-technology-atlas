const $=id=>document.getElementById(id);let result=null;
const names={'in-sync':'managed一致','new-desired':'宣言変更（actualはまだ変更しない）','apply':'差分を適用','observe':'観測のみ（差分を残す）','manual':'actualを手動変更','refuse':'拒否（actualを変更しない）'};
function render(){
 const row=result.trace[Number($('step').value)];const packet=row.packet;
 $('flow').textContent=`step ${Number($('step').value)+1}：${row.event} → ${names[row.action]}`;
 $('desired').textContent=packet?`packet ${packet.name} / generation ${packet.generation}\nbytes SHA-256 ${packet.sha256}\n${packet.bytes}${row.authoritative?'\n最新の許可revision generation '+row.authoritative.generation+' / '+row.authoritative.sha256:''}`:'このstepはactualへの手動変更';
 $('actual').textContent='前 '+JSON.stringify(row.liveBefore||row.liveAfter)+'\n後 '+JSON.stringify(row.liveAfter);
 $('status').textContent=row.reason?'拒否理由：'+row.reason:row.event==='tick'?`managed一致 ${row.managedEqualAfter} ／ exact一致 ${row.exactEqualAfter} ／ mode ${row.mode} ／ ignore ${row.ignore.join(',')||'なし'}`:'tick前：適用はまだ行わない';
 $('diff').innerHTML='<tr><th>field</th><th>actual → desired</th><th>扱い</th></tr>'+[...(row.diff||[]).map(d=>({...d,kind:'管理対象'})),...(row.ignoredDiff||[]).map(d=>({...d,kind:'明示ignore：rawは残す'}))].map(d=>`<tr><td>${d.field}</td><td>${d.live} → ${d.desired}</td><td>${d.kind}</td></tr>`).join('');
 $('rawStep').textContent=JSON.stringify(row,null,2);
}
$('run').addEventListener('click',async()=>{
 try{const res=await fetch('/api?case='+encodeURIComponent($('case').value));if(!res.ok)throw new Error('HTTP '+res.status);result=await res.json();$('predictionEcho').textContent='あなたの予想：'+($('prediction').value||'未記入');$('summary').textContent=`${result.case} ／ ${result.trace.length} step ／ 最終 ${JSON.stringify(result.final)}`;$('raw').textContent=JSON.stringify(result,null,2);$('step').innerHTML=result.trace.map((r,i)=>`<option value="${i}">${i+1} ${r.event} / ${names[r.action]}</option>`).join('');$('step').disabled=false;$('step').value=String(result.trace.length-1);render();}catch(e){$('summary').textContent='実行エラー：'+e.message;}
});$('step').addEventListener('change',render);

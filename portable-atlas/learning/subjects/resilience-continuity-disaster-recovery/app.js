const $=s=>document.querySelector(s);
$('#run').addEventListener('click',async()=>{
 $('#summary').textContent='専用一時DBで実行中';$('#guess').textContent='あなたの予想：'+$('#prediction').value;
 try{
 const response=await fetch('/api?case='+encodeURIComponent($('#case').value));if(!response.ok)throw Error('HTTP '+response.status);
 const result=await response.json(),r=result.raw;$('#raw').textContent=JSON.stringify(result,null,2);
 $('#summary').textContent=r.status==='restored'?`restored ／ 欠落 ${r.dataLossWrites} write ／ gap ${r.rpoGapSyntheticTicks} synthetic tick`:`refused：${r.reason} ／ live維持`;
 $('#rows').textContent=`snapshot: ${JSON.stringify(r.snapshotRows)}\nlatest: ${JSON.stringify(r.latestRows)}\nreopened: ${JSON.stringify(r.reopenedRows)}`;$('#rows').style.whiteSpace='pre-wrap';
 $('#metrics').textContent=`missing IDs: ${JSON.stringify(r.missingWriteIds)}\nrestore observed ns: ${r.restoreObservedNs===null?'対象なし（拒否）':r.restoreObservedNs}\nattempt observed ns: ${r.attemptObservedNs}\nintegrity: ${r.reopenedIntegrity}`;$('#metrics').style.whiteSpace='pre-wrap';
 $('#hash').textContent=`candidate一致: ${r.candidateHash===r.expectedSnapshotHash} ／ live前後一致: ${r.liveBeforeHash===r.liveAfterHash} ／ actual SHA-256はrawへ`;
 $('#steps').replaceChildren();for(const t of r.trace){let tr=document.createElement('tr');for(const text of [t.phase,t.elapsedNs,JSON.stringify(Object.fromEntries(Object.entries(t).filter(([k])=>!['phase','elapsedNs','utc'].includes(k))))]){let td=document.createElement('td');td.textContent=text;tr.append(td)}$('#steps').append(tr)}
 const svg=$('#timeline');svg.replaceChildren();svg.setAttribute('viewBox',`0 0 980 ${r.trace.length*30+20}`);const ns='http://www.w3.org/2000/svg';
 r.trace.forEach((t,i)=>{let dot=document.createElementNS(ns,'circle');dot.setAttribute('cx',170+Math.round(700*t.elapsedNs/r.trace.at(-1).elapsedNs));dot.setAttribute('cy',i*30+18);dot.setAttribute('r',6);dot.setAttribute('fill',t.phase==='mutate'?'#ad563b':'#367a5d');let label=document.createElementNS(ns,'text');label.setAttribute('x',5);label.setAttribute('y',i*30+23);label.setAttribute('font-size','13');label.textContent=t.phase;svg.append(label,dot)});
 }catch(e){$('#summary').textContent='実行失敗：'+e.message}
});

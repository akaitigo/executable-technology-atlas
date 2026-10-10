const params=new URLSearchParams(location.search),caseId=params.get('case'),runId=params.get('run');
const loadedAt=new Date().toISOString(),environment={userAgent:navigator.userAgent,language:navigator.language,visibility:document.visibilityState,width:innerWidth,height:innerHeight,timeOrigin:performance.timeOrigin};
const response=await fetch('sources.json'),manifest=await response.json();
if(!response.ok)throw Error('source manifest failed');
if(!['basic','nested','caught-error'].includes(caseId)||!/^\d+$/.test(runId))throw new RangeError('unsupported input');
document.querySelector('#title').textContent='Case: '+caseId+' / run '+runId;
const startedAt=new Date().toISOString(),start=performance.now(),trace=[];let caught=null;
function mark(label,kind){trace.push({sequence:trace.length+1,label,kind,at:new Date().toISOString(),elapsedMs:performance.now()-start});}
function complete(){
 const raw={kind:'actual-browser-event-loop',input:{caseId,runId,timerDelayMs:0},loadedAt,startedAt,completedAt:new Date().toISOString(),environment,sourceHashes:manifest.sourceHashes,loading:{manifestStatus:response.status,manifestContentType:response.headers.get('content-type'),script:'case.mjs',documentPath:location.pathname+location.search},trace,caught};
 for(const event of trace){const row=document.createElement('tr');for(const v of [event.sequence,event.label,event.elapsedMs.toFixed(3)]){const cell=document.createElement('td');cell.textContent=v;row.append(cell);}document.querySelector('#events').append(row);}
 document.querySelector('#raw').textContent=JSON.stringify(raw,null,2);document.querySelector('#status').textContent='観測完了: '+caseId+' / '+trace.length+' events';
 parent.postMessage({type:'event-loop-result',raw},location.origin);
}
// 以下の同じ同期呼出し内で両timerとPromiseを登録。runnerはoracleの期待値を読まない。
mark('sync-start','sync');
if(caseId==='caught-error'){
 Promise.resolve().then(()=>{mark('micro-throw','microtask');throw new Error('intentional promise reaction failure');}).catch(error=>{caught={name:error.name,message:error.message};mark('micro-caught','microtask');});
 Promise.resolve().then(()=>mark('micro-peer','microtask'));
}else{
 Promise.resolve().then(()=>{mark('micro-parent','microtask');if(caseId==='nested')queueMicrotask(()=>{mark('micro-child','microtask');queueMicrotask(()=>mark('micro-grandchild','microtask'));});});
 if(caseId==='nested')Promise.resolve().then(()=>mark('micro-peer','microtask'));
}
setTimeout(()=>{mark('timer-first','timer-task');Promise.resolve().then(()=>mark('timer-micro','microtask'));},0);
setTimeout(()=>{mark('timer-second','timer-task');complete();},0);
mark('sync-end','sync');

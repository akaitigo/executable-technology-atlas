import fs from 'node:fs';import vm from 'node:vm';import assert from 'node:assert/strict';
class Element{
 constructor(){this.value='';this.children=[];this.textContent='';this.hidden=true;this.listeners={};this.className='';}
 append(e){this.children.push(e);if(!this.value&&e.value)this.value=e.value;}
 replaceChildren(){this.children=[];this.value='';}
 addEventListener(n,f){this.listeners[n]=f;}
 get options(){return this.children;}
}
const flush=async()=>{for(let i=0;i<20;i++)await Promise.resolve();};
async function setup(){
 const elements=Object.fromEntries(['sources','fixture','schedule','prediction','result','comparison','raw','comparison-rows','answer','probe-raw','status','step-info','seen','requests','flow','step','summary','run','compare','previous','next','reset','probes','mode','width','a-state','b-state','ab','ba','totals','event'].map(n=>[n,new Element()]));elements.prediction.value='unanswered';elements.mode.value='normal';elements.width.value='64';
 const pending=[];const context=vm.createContext({document:{getElementById:n=>elements[n],createElement:()=>new Element()},fetch:(url,options)=>url==='/fixtures'?Promise.resolve({ok:true,json:async()=>([{id:'ping',label:'ping'}])}):new Promise((resolve,reject)=>pending.push({url,body:options?.body,resolve,reject})),console});
 vm.runInContext(fs.readFileSync(process.argv[2]||'app.js','utf8'),context);await flush();return {elements,pending};
}
const row=JSON.parse(fs.readFileSync('observations/attempt-01/raw.json','utf8')).rows.find(r=>r.fixture==='ping'&&r.mode==='normal'&&r.width===64);
const response={ok:true,json:async()=>row};const proof=[];
for(const old of ['run','compare']){
 const {elements:e,pending:p}=await setup();const oldWork=e[old].onclick();assert.equal(p.length,1);
 const newer=e.run.onclick();assert.equal(p.length,2);p[1].resolve(response);await flush();await newer;
 assert.equal(e.result.hidden,false);const before=e.raw.textContent;p[0].reject(Error('obsolete transport failure'));await flush();await oldWork;
 assert.equal(e.raw.textContent,before);assert.equal(e.result.hidden,false);assert.equal(e.status.textContent,'保存観測の読取完了');proof.push({case:old+'_old_failure_after_new_success',retained:true});
}
for(const action of ['run','compare']){
 const {elements:e,pending:p}=await setup();const initial=e.run.onclick();p[0].resolve(response);await flush();await initial;assert.equal(e.result.hidden,false);
 const failing=e[action].onclick();p[1].reject(Error('current transport failure'));await flush();await failing;
 assert.equal(e.result.hidden,true);assert.equal(e.raw.textContent,'');assert.equal(e.status.textContent,'失敗: current transport failure');proof.push({case:action+'_current_failure',cleared:true});
}
const {elements:e,pending:p}=await setup();const obsolete=e.run.onclick();e.reset.onclick();p[0].resolve(response);await flush();await obsolete;assert.equal(e.result.hidden,true);assert.equal(e.status.textContent,'リセット: 未読');proof.push({case:'old_success_after_reset',ignored:true});
for(const action of ['run','compare']){
 const {elements:e,pending:p}=await setup();const main=e[action].onclick();const w=e.probes.onclick();assert.equal(p.length,2);
 p[1].resolve({ok:true,json:async()=>({probe:'saved'})});await flush();await w;
 assert.equal(e['probe-raw'].textContent,JSON.stringify({probe:'saved'},null,2));
 p[0].resolve(response);await flush();
 if(action==='compare'){assert.equal(p.length,3);p[2].resolve(response);await flush();}
 await main;assert.equal(e.status.textContent,action==='run'?'保存観測の読取完了':'比較完了');
 assert.equal(action==='run'?e.result.hidden:e.comparison.hidden,false);
 proof.push({case:action+'_pending_then_probe',both_completed:true});
}
for(const action of ['run','compare']){
 const {elements:e,pending:p}=await setup();const w=e.probes.onclick();const main=e[action].onclick();
 p[1].resolve(response);await flush();if(action==='compare'){p[2].resolve(response);await flush();}await main;
 p[0].resolve({ok:true,json:async()=>({probe:'obsolete'})});await flush();await w;
 assert.equal(e['probe-raw'].textContent,'');assert.equal(e.status.textContent,action==='run'?'保存観測の読取完了':'比較完了');
 proof.push({case:'probe_pending_then_'+action,obsolete_probe_ignored:true});
}
for(const oldResult of ['success','failure']){
 const {elements:e,pending:p}=await setup();const old=e.probes.onclick();const latest=e.probes.onclick();
 p[1].resolve({ok:true,json:async()=>({probe:'latest'})});await flush();await latest;
 const expected=JSON.stringify({probe:'latest'},null,2);
 if(oldResult==='success')p[0].resolve({ok:true,json:async()=>({probe:'old'})});else p[0].reject(Error('old probe failure'));
 await flush();await old;assert.equal(e['probe-raw'].textContent,expected);
 proof.push({case:'duplicate_probe_old_'+oldResult,latest_retained:true});
}
console.log(JSON.stringify({runtime:process.version,actual_app_source:true,method:'controlled fetch promises and minimal DOM; separate from actual browser evidence',rows:proof}));

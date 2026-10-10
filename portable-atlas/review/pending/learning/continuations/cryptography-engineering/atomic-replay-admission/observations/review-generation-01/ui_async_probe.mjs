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
 const elements=Object.fromEntries(['sources','fixture','schedule','prediction','result','comparison','raw','comparison-rows','answer','thread-raw','status','step-info','seen','requests','flow','step','summary','run','compare','previous','next','reset','threads'].map(n=>[n,new Element()]));elements.prediction.value='unanswered';
 const pending=[];const context=vm.createContext({document:{getElementById:n=>elements[n],createElement:()=>new Element()},fetch:(url,options)=>url==='/fixtures'?Promise.resolve({ok:true,json:async()=>({fixtures:[{id:'same',label:'same'}],schedules:{'split-2':[],'atomic-AB':[]}})}):new Promise((resolve,reject)=>pending.push({url,body:options?.body,resolve,reject})),console});
 vm.runInContext(fs.readFileSync('app.js','utf8'),context);await flush();return {elements,pending};
}
const row={fixture:'same',schedule:'split-2',accepted_count:2,seen:['MSG1'],trace:[{event:'initial',requests:{A:{id:'MSG1',authenticated:true,cached_absent:null,status:'pending'},B:{id:'MSG1',authenticated:true,cached_absent:null,status:'pending'}},seen:[],accepted_count:0},{event:'Bw',requests:{A:{id:'MSG1',authenticated:true,cached_absent:true,status:'accepted'},B:{id:'MSG1',authenticated:true,cached_absent:true,status:'accepted'}},seen:['MSG1'],accepted_count:2}]};
const response={ok:true,json:async()=>row};const proof=[];
for(const old of ['run','compare']){
 const {elements:e,pending:p}=await setup();const oldWork=e[old].onclick();assert.equal(p.length,1);
 const newer=e.run.onclick();assert.equal(p.length,2);p[1].resolve(response);await flush();await newer;
 assert.equal(e.result.hidden,false);const before=e.raw.textContent;p[0].reject(Error('obsolete transport failure'));await flush();await oldWork;
 assert.equal(e.raw.textContent,before);assert.equal(e.result.hidden,false);assert.equal(e.status.textContent,'完了');proof.push({case:old+'_old_failure_after_new_success',retained:true});
}
for(const action of ['run','compare']){
 const {elements:e,pending:p}=await setup();const initial=e.run.onclick();p[0].resolve(response);await flush();await initial;assert.equal(e.result.hidden,false);
 const failing=e[action].onclick();p[1].reject(Error('current transport failure'));await flush();await failing;
 assert.equal(e.result.hidden,true);assert.equal(e.raw.textContent,'');assert.equal(e.status.textContent,'失敗: current transport failure');proof.push({case:action+'_current_failure',cleared:true});
}
const {elements:e,pending:p}=await setup();const obsolete=e.run.onclick();e.reset.onclick();p[0].resolve(response);await flush();await obsolete;assert.equal(e.result.hidden,true);assert.equal(e.status.textContent,'リセット: 未実行');proof.push({case:'old_success_after_reset',ignored:true});
console.log(JSON.stringify({runtime:process.version,actual_app_source:true,method:'controlled fetch promises and minimal DOM; separate from actual browser evidence',rows:proof}));

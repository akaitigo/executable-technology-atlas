// Actual ui.js in Node vm; in-memory DOM/fetch and a saved baseline receipt.
// No browser, network, SQLite execution, or producer rerun.
const fs=require('node:fs'),path=require('node:path'),vm=require('node:vm'),assert=require('node:assert/strict'),crypto=require('node:crypto');
const P=__dirname,read=n=>fs.readFileSync(path.join(P,n),'utf8'),hash=s=>crypto.createHash('sha256').update(s).digest('hex');
const fixed=JSON.parse(read('fixture.json')),pointer=JSON.parse(read('evidence/current.json')),saved=JSON.parse(read('evidence/'+pointer.raw)).attempts.find(r=>r.id==='baseline').raw;
assert.equal(hash(read('evidence/'+pointer.raw)),pointer.sha256);
const clone=x=>JSON.parse(JSON.stringify(x));
async function setup(source){
 const elements=new Map(),get=id=>{if(!elements.has(id))elements.set(id,{textContent:'',innerHTML:'',value:id==='case'?'baseline':'',replaceChildren(){this.innerHTML=''}});return elements.get(id)};
 let pending=[];const context=vm.createContext({document:{getElementById:get},fetch(url){if(url==='fixture.json')return Promise.resolve({json:async()=>clone(fixed)});if(url==='/api/run')return Promise.resolve({ok:true,json:async()=>clone(saved)});assert.equal(url,'/api/unavailable');return new Promise((resolve,reject)=>pending.push({resolve,reject}))}});
 vm.runInContext(source,context,{filename:'ui.js'});await new Promise(r=>setImmediate(r));
 const state=()=>Object.fromEntries(['status','answer','raw','comparison'].map(id=>[id,id==='comparison'?get(id).innerHTML:get(id).textContent]));
 const success=async()=>{get('input').value=JSON.stringify(fixed[0].input);get('input').oninput();await get('run').onclick();assert.equal(get('status').textContent,'OBSERVED / exit=0');assert.ok(get('comparison').innerHTML.includes('COVERING_REPORTED'));return state()};
 return{get,state,success,pending};
}
const scenarios=[
 ['current-503','current',503],['old-503-new-success','success',503],['old-reject-new-success','success','reject'],
 ['current-reject','current','reject'],['unexpected-200','current',200],['unexpected-418','current',418],['unexpected-500','current',500],
 ['old-unexpected-new-success','success',200],['old-reject-reset','reset','reject'],['old-503-edited','edit',503]
];
async function collect(source){let rows=[];
 for(const [id,steer,response] of scenarios){
  const h=await setup(source);const promise=h.get('httpfail').onclick();let rejection=null;
  // Attach rejection observation immediately, including the old broken handler.
  const settled=Promise.resolve(promise).catch(e=>{rejection=String(e.message||e)});
  if(steer==='success')await h.success();
  if(steer==='reset')h.get('reset').onclick();
  if(steer==='edit'){h.get('input').value='{}';h.get('input').oninput()}
  const before=h.state();if(response==='reject')h.pending[0].reject(Error('SIMULATED_OFFLINE'));else h.pending[0].resolve({status:response});
  await settled;await new Promise(r=>setImmediate(r));const after=h.state();let errors=[];
  try{
   assert.equal(rejection,null,'handler promise must settle without rejection');
   if(steer!=='current')assert.deepEqual(after,before,'stale completion changed newer state');
   else{assert.equal(after.raw,'');assert.equal(after.comparison,'');if(response===503){assert.equal(after.status,'HTTP_ERROR 503');assert.equal(after.answer,'HTTP503: 結果なし')}else{assert.equal(after.status,'HTTP_ERROR');assert.ok(after.answer.startsWith('503試験を完了できません: '));assert.ok(after.answer.includes(response==='reject'?'SIMULATED_OFFLINE':String(response)));assert.notEqual(after.answer,'HTTP503: 結果なし')}}
  }catch(e){errors.push(e.message)}
  rows.push({id,response,steer,status:errors.length?'failed':'passed',errors,rejection,before,after});
 }
 return{status:rows.every(r=>r.status==='passed')?'passed':'failed',cases:rows};
}
(async()=>{
 const started=new Date().toISOString(),old=read('evidence/async-review-old/ui.js'),current=read('ui.js');const before=await collect(old),after=await collect(current);
 assert.equal(before.status,'failed');assert.equal(before.cases.find(r=>r.id==='old-503-new-success').status,'failed');assert.equal(before.cases.find(r=>r.id==='old-reject-new-success').status,'failed');assert.equal(after.status,'passed');
 const result={status:'passed',started,completed:new Date().toISOString(),method:'Node vm: actual ui.js; simulated DOM/fetch; saved baseline success; not live browser/network/SQLite',old_source_sha256:hash(old),source_sha256:hash(current),saved_raw_sha256:pointer.sha256,old:before,current:after};
 if(process.argv.includes('--record'))fs.writeFileSync(path.join(P,'evidence/async-regression.json'),JSON.stringify(result,null,2)+'\n');
 console.log(JSON.stringify({status:result.status,started,completed:result.completed,old_failed:before.cases.filter(r=>r.status==='failed').map(r=>r.id),current_cases:after.cases.length,source_sha256:result.source_sha256}));
})().catch(e=>{console.error(e);process.exitCode=1});

const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict');
class Element {
 constructor(){this.value='';this.textContent='';this.rows=[];this.listeners={};}
 append(){} replaceChildren(){} addEventListener(n,f){this.listeners[n]=f;}
 insertCell(){return new Element();} insertRow(){const e=new Element();this.rows.push(e);return e;}
}
async function test(source,kind){
 const elements={};const el=s=>elements[s]||(elements[s]=new Element());
 el('#fixture').value='chain';el('#mode').value='none';const calls=[];
 const fixture={id:'chain',program:[],initial:[0]};
 function fetch(url){
  if(url==='/fixtures')return Promise.resolve({json:async()=>[fixture]});
  return new Promise((resolve,reject)=>calls.push({resolve,reject}));
 }
 const context=vm.createContext({document:{querySelector:el,createElement:()=>new Element()},fetch});
 vm.runInContext(source,context);
 await new Promise(resolve=>setImmediate(resolve));
 const old=el(kind==='run'?'#run':'#compare').onclick();
 assert.equal(calls.length,1);
 el('#mode').value='forwarding';el('#mode').listeners.change();
 const fresh=el('#run').onclick();assert.equal(calls.length,2);
 const row={fixture:'chain',mode:'forwarding',cycles:7,stalls:0,retired:3,matches_oracle:true,registers:[0,5,10,9],trace:[]};
 calls[1].resolve({ok:true,json:async()=>row});await fresh;
 assert.ok(el('#raw').textContent.includes('forwarding'));
 calls[0].reject(new Error('controlled old delayed failure'));await old;
 return {kind,retained:el('#raw').textContent.includes('forwarding'),status:el('#status').textContent};
}
(async()=>{
 const old=fs.readFileSync('observations/review-generation-01/app.js','utf8');
 const current=fs.readFileSync('app.js','utf8');const rows=[];
 for(const kind of ['run','compare']){
  const before=await test(old,kind),after=await test(current,kind);
  assert.equal(before.retained,false);assert.equal(after.retained,true);
  assert.equal(after.status,'実行済み：chain / forwarding');rows.push({before,after});
 }
 console.log(JSON.stringify({node:process.version,scope:'Controlled fetch promises and minimal DOM mock, not a browser test',rows,status:'passed'},null,2));
})().catch(e=>{console.error(e);process.exitCode=1;});

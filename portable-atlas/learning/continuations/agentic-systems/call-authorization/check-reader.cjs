/* Atlas: finite state/data validation; no browser, external tool or recalculation. */
const fs=require('fs'),vm=require('vm'),path=require('path'),crypto=require('crypto'),assert=require('assert');
const root=__dirname,sha=f=>crypto.createHash('sha256').update(fs.readFileSync(path.join(root,f))).digest('hex');
const context={};context.window=context;vm.createContext(context);
for(const name of ['reader-data.js','reader-expectations.js','reader-state.js'])vm.runInContext(fs.readFileSync(path.join(root,name),'utf8'),context,{filename:name});
const S=context.AtlasCallState,D=context.AtlasCallData,clone=x=>JSON.parse(JSON.stringify(x));let checks=[];
function check(name,test){test();checks.push({name,passed:true});}
for(const row of D.result.cases){
 check('saved-'+row.id,()=>assert.equal(S.validate(D,row.id).id,row.id));
 const s=S.change(S.initial(),'case',row.id),pred=row.authority_breach?'fault':row.authorized?'approved':'reject';
 check('prediction-required-'+row.id,()=>{const n=S.read(s,D);assert(!n.shown&&n.error);});
 const shown={...S.read(S.change(s,'prediction',pred),D),answer:true};
 check('shown-'+row.id,()=>assert(shown.shown&&!shown.error));
 for(const [kind,value] of [['prediction',pred==='reject'?'approved':'reject'],['record','missing'],['case',row.id],['reset',null]]){
  check('clear-'+row.id+'-'+kind,()=>{const n=S.change(shown,kind,value);assert(!n.shown&&!n.answer&&!n.error);});
 }
}
let shown={...S.read(S.change(S.initial(),'prediction','approved'),D),answer:true};
for(const mode of ['missing','altered','old'])check('record-refusal-'+mode,()=>{let n=S.read(S.change(shown,'record',mode),D);assert(!n.shown&&!n.answer&&n.error);n=S.read(S.change(n,'record','normal'),D);assert(n.shown&&!n.answer&&!n.error);});
for(const [name,mutate] of [
 ['timestamp',x=>x.result.observed_at_utc='2030-01-01T00:00:00Z'],['run',x=>x.run_id='other-valid-run'],
 ['digest',x=>x.result_sha256='0'.repeat(64)],['fixture-approval',x=>x.fixtures.cases[1].input.approval.args.a=100],
 ['consumption',x=>x.result.cases[0].trace[3].data.consumed=false],['stale',x=>x.result.cases[8].authorized=true],
 ['extra',x=>x.unknown=true],['missing-data',()=>{}],
])check('tamper-'+name,()=>{const x=clone(D);mutate(x);const n=S.read(shown,name==='missing-data'?undefined:x);assert(!n.shown&&!n.answer&&n.error);});
const result=JSON.parse(fs.readFileSync(path.join(root,'observations/calculation-20261006T205623999075Z/result.json'))),fixture=JSON.parse(fs.readFileSync(path.join(root,'fixtures.json')));
check('exact-saved-json',()=>assert.equal(S.canonical(D.result),S.canonical(result)));check('exact-fixture',()=>assert.equal(S.canonical(D.fixtures),S.canonical(fixture)));
const report={title:'Atlas saved reader state checks',passed:true,checks,browser_executed:false,model_executed:false,source_sha256:Object.fromEntries(['reader-data.js','reader-expectations.js','reader-state.js','check-reader.cjs'].map(n=>[n,sha(n)]))};
fs.writeFileSync(path.join(root,'observations/reader-state-check.json'),JSON.stringify(report,null,2)+'\n');console.log(JSON.stringify({passed:true,checks:checks.length,browser_executed:false}));

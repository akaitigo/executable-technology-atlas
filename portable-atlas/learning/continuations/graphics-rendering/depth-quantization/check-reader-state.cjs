/* Atlas: saved-data pure state checks, no DOM, GPU, browser or model execution. */
const fs=require('fs'),path=require('path'),vm=require('vm'),assert=require('assert'),crypto=require('crypto'),S=require('./reader-state.js');
const box={};for(const f of ['reader-data.js','reader-expectations.js'])vm.runInNewContext(fs.readFileSync(path.join(__dirname,f),'utf8'),box);
const D=JSON.parse(JSON.stringify(box.ATLAS_DATA)),E=JSON.parse(JSON.stringify(box.ATLAS_EXPECTED));assert(D&&E,'saved calculation not connected');const checks=[];
const ok=(name,value)=>{assert(value,name);checks.push(name);},send=(s,e,data=D)=>S.transition(s,e,data,E);
function loaded(id){let s=send(S.initial(),{type:'case',value:id});s=send(s,{type:'prediction',key:'exactPrediction',value:'A'});s=send(s,{type:'prediction',key:'quantizedPrediction',value:'B'});return send(s,{type:'load'});}
for(const c of [...D.result.central,...D.result.boundaries]){
 let s=send(S.initial(),{type:'case',value:c.id});ok('prediction-required-'+c.id,!!send(s,{type:'load'}).error);s=loaded(c.id);ok('load-'+c.id,!!s.shown&&!s.error);assert.deepStrictEqual(s.shown,c);
 for(let i=0;i<=c.trace.length;i++){s=send(s,{type:'step',value:i});const expected=i===0?{exact:{depth:'1',winner:null},quantized:{code:c.maximum,winner:null}}:{exact:c.trace[i-1].exact_after,quantized:c.trace[i-1].quantized_after};assert.deepStrictEqual(S.snapshot(s),expected);ok('stage-'+c.id+'-'+i,!s.answer&&s.step===i);}
 s=send(s,{type:'answer'});ok('answer-'+c.id,s.answer);
 for(const event of [{type:'prediction',key:'exactPrediction',value:'B'},{type:'prediction',key:'quantizedPrediction',value:'A'},{type:'case',value:S.ids[(S.ids.indexOf(c.id)+1)%S.ids.length]},{type:'mode',value:'missing'},{type:'reset'}]){const x=send(s,event);ok('clear-'+c.id+'-'+event.type+'-'+(event.key||''),!x.shown&&!x.answer&&!x.error&&x.step===0);}
 for(const i of [-1,3,0.5])ok('invalid-stage-'+c.id+'-'+i,send(s,{type:'step',value:i})===s);
}
for(const [name,change] of [
 ['missing',()=>null],['code',d=>{d.result.central[0].trace[0].code=2;return d;}],
 ['timestamp',d=>{d.observed_at_utc='2000-01-01T00:00:00Z';return d;}],
 ['run-id',d=>{d.run_id='calculation-other';return d;}],['sha',d=>{d.result_sha256='a'.repeat(64);return d;}],
 ['fixture',d=>{d.fixture.central[0].request.bits=4;return d;}],['clear-bin',d=>{d.result.boundaries[4].quantized_final.winner='F';return d;}],
 ['extra-key',d=>{d.unchecked=true;return d;}],['float-type',d=>{d.result.central[0].trace[0].code='3';return d;}]
]){let s=send(loaded(S.ids[0]),{type:'answer'});s=send(s,{type:'load'},change(JSON.parse(JSON.stringify(D))));ok('reject-'+name,!s.shown&&!s.answer&&!!s.error);s=send(s,{type:'load'});ok('recover-'+name,!!s.shown&&!s.answer&&!s.error);}
const report={title:'Atlas saved depth reader state checks',passed:true,checks,dom_checked:false,model_executed:false,browser_started:0,server_started:0,sources:Object.fromEntries(['reader-state.js','reader-data.js','reader-expectations.js','check-reader-state.cjs'].map(n=>[n,crypto.createHash('sha256').update(fs.readFileSync(path.join(__dirname,n))).digest('hex')]))};
fs.writeFileSync(path.join(__dirname,'observations/reader-state-check.json'),JSON.stringify(report,null,2)+'\n');console.log(JSON.stringify({passed:true,checks:checks.length,dom_checked:false}));

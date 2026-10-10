/* Atlas: pure state checks on saved results; no DOM, model calculation, browser or server. */
const fs=require('fs'),path=require('path'),vm=require('vm'),assert=require('assert'),crypto=require('crypto');
const root=__dirname,S=require('./reader-state.js'),box={window:{}};
for(const file of ['reader-data.js','reader-expectations.js'])vm.runInNewContext(fs.readFileSync(path.join(root,file),'utf8'),box);
const D=JSON.parse(JSON.stringify(box.window.ATLAS_RETRY_DATA)),E=JSON.parse(JSON.stringify(box.window.ATLAS_RETRY_EXPECTED));
assert(D&&E,'saved calculation has not been connected');
let checks=[];
const ok=(name,value)=>{assert(value,name);checks.push(name);};
const send=(s,type,value,data=D)=>S.transition(s,{type,value},data,E);
function loaded(id){let s=S.initial(id);s=send(s,'prediction','succeeded');s=send(s,'duePrediction','3');s=send(s,'load');ok('loaded-'+id,!!s.shown&&!s.error);return s;}
for(const r of D.result.cases){
 let s=S.initial(r.id);ok('prediction-required-'+r.id,!send(s,'load').shown&&!!send(s,'load').error);
 s=loaded(r.id);assert.deepStrictEqual(s.shown,r);
 for(let i=0;i<r.boundaries.length;i++){s=send(s,'step',i);ok('boundary-'+r.id+'-'+i,s.step===i&&!s.answer&&s.shown.boundaries[i].t===r.boundaries[i].t);}
 s=send(s,'answer');ok('answer-'+r.id,s.answer);
 for(const [kind,value] of [['prediction','failed'],['duePrediction','2'],['mode','missing'],['reset',null],['case',S.ids[(S.ids.indexOf(r.id)+1)%4]]]){
  const next=send(s,kind,value);ok('clear-'+r.id+'-'+kind,next.shown===null&&!next.answer&&next.step===0&&!next.error);
 }
 for(const value of [-1,r.boundaries.length,0.5])ok('invalid-boundary-'+r.id+'-'+value,send(s,'step',value)===s);
}
for(const mode of ['missing','altered','old']){let s=loaded(S.ids[0]);s=send(s,'answer');s=send(s,'mode',mode);s=send(s,'load');ok('reject-'+mode,!s.shown&&!s.answer&&!!s.error);s=send(s,'mode','normal');s=send(s,'load');ok('recover-'+mode,!!s.shown&&!s.error);}
for(const [name,change] of [
 ['fixture',d=>d.fixture.retry_budget=3],['timestamp',d=>d.result.observed_at_utc='2000-01-01T00:00:00Z'],
 ['run-id',d=>d.run_id='calculation-other'],['sha',d=>d.result_sha256='a'.repeat(64)],
 ['sticky-cleared',d=>d.result.cases[3].boundaries[4].d_state='pending'],
 ['extra-field',d=>d.unchecked=true]]){
 const candidate=JSON.parse(JSON.stringify(D));change(candidate);let s=send(loaded(S.ids[0]),'answer');s=send(s,'load',null,candidate);
 ok('changed-record-'+name,!s.shown&&!s.answer&&!!s.error);
}
const report={title:'Atlas saved retry reader pure-state checks',passed:true,checks,dom_checked:false,model_executed:false,browser_started:0,server_started:0,
 sources:Object.fromEntries(['reader-state.js','reader-data.js','reader-expectations.js','check-reader-state.cjs'].map(n=>[n,crypto.createHash('sha256').update(fs.readFileSync(path.join(root,n))).digest('hex')]))};
fs.writeFileSync(path.join(root,'observations/reader-state-check.json'),JSON.stringify(report,null,2)+'\n');console.log(JSON.stringify({passed:true,checks:checks.length,dom_checked:false}));

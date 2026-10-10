/* Atlas: finite pure state checks against saved calculation; no DOM or receiver. */
const fs=require('fs'),path=require('path'),vm=require('vm'),assert=require('assert'),crypto=require('crypto'),S=require('./reader-state.js');
const box={window:{}};for(const f of ['reader-data.js','reader-expectations.js'])vm.runInNewContext(fs.readFileSync(path.join(__dirname,f),'utf8'),box);
const D=JSON.parse(JSON.stringify(box.window.ATLAS_PHASE_DATA)),E=JSON.parse(JSON.stringify(box.window.ATLAS_PHASE_EXPECTED));assert(D&&E,'saved calculation not connected');let checks=[];
const ok=(name,value)=>{assert(value,name);checks.push(name);};const send=(s,type,value,data=D)=>S.transition(s,{type,value},data,E);
function loaded(id){let s=S.initial(id);s=send(s,'prediction','equal');s=send(s,'load');ok('load-'+id,!!s.shown&&!s.error);return s;}
for(const c of D.result.cases){
 let s=S.initial(c.id);ok('prediction-required-'+c.id,!send(s,'load').shown&&!!send(s,'load').error);s=loaded(c.id);assert.deepStrictEqual(s.shown,c);
 for(let n=2;n<=5;n++){s=send(s,'step',n);ok('selection-'+c.id+'-'+n,s.n===n&&!s.answer&&s.shown.methods[0].receiver.rows[n-2].n===n);}
 s=send(s,'answer');ok('answer-'+c.id,s.answer);
 for(const [type,value] of [['prediction','hold'],['mode','missing'],['case',S.ids[(S.ids.indexOf(c.id)+1)%4]],['reset',null]]){const x=send(s,type,value);ok('clear-'+c.id+'-'+type,x.shown===null&&!x.answer&&x.n===2&&!x.error);}
 for(const n of [1,6,2.5])ok('bad-index-'+c.id+'-'+n,send(s,'step',n)===s);
}
for(const mode of ['missing','altered','old']){let s=send(loaded(S.ids[0]),'answer');s=send(s,'mode',mode);s=send(s,'load');ok('reject-'+mode,!s.shown&&!s.answer&&!!s.error);s=send(s,'mode','normal');s=send(s,'load');ok('recover-'+mode,!!s.shown&&!s.error);}
for(const [name,change] of [
 ['fixture',d=>d.fixture.cases[0].request.known_pilots[0].bit=1],
 ['timestamp',d=>d.result.observed_at_utc='2000-01-01T00:00:00Z'],['run-id',d=>d.run_id='calculation-other'],
 ['sha',d=>d.result_sha256='a'.repeat(64)],['missing-null',d=>d.result.cases[3].methods[1].comparison.errors=0],
 ['imaginary-sign',d=>d.result.cases[2].methods[1].receiver.rows[2].corrected[1]='-24/25'],['extra-key',d=>d.unchecked=true]]){
 const data=JSON.parse(JSON.stringify(D));change(data);let s=send(loaded(S.ids[0]),'answer');s=send(s,'load',null,data);ok('mutation-'+name,!s.shown&&!s.answer&&!!s.error);
}
const report={title:'Atlas telecom saved reader state checks',passed:true,checks,dom_checked:false,model_executed:false,browser_started:0,server_started:0,sources:Object.fromEntries(['reader-state.js','reader-data.js','reader-expectations.js','check-reader-state.cjs'].map(n=>[n,crypto.createHash('sha256').update(fs.readFileSync(path.join(__dirname,n))).digest('hex')]))};
fs.writeFileSync(path.join(__dirname,'observations/reader-state-check.json'),JSON.stringify(report,null,2)+'\n');console.log(JSON.stringify({passed:true,checks:checks.length,dom_checked:false}));

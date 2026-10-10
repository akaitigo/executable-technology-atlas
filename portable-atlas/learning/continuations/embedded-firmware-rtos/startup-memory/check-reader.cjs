/* Atlas: finite state checks over saved bytes; no DOM/browser/model run. */
const fs=require('fs'),path=require('path'),crypto=require('crypto'),assert=require('assert');
const root=__dirname,sha=n=>crypto.createHash('sha256').update(fs.readFileSync(path.join(root,n))).digest('hex');
require('./reader-data.js');require('./reader-expectations.js');
const S=require('./reader-state.js'),D=globalThis.AtlasStartupData,E=globalThis.AtlasStartupExpected,checks=[];
const check=(name,value)=>{assert(value,name);checks.push({name,passed:true});},act=(s,type,value,data=D)=>S.transition(s,{type,value},data,E);
function shown(id){let s=act(S.initial(id),'prediction','pass');s=act(s,'load');check('shown-'+id,!!s.shown&&!s.error);return s;}
function clear(name,s,error=false){check(name,s.shown===null&&!s.answer&&s.step===0&&(error?!!s.error:!s.error));}
for(const r of D.result.cases){let s=shown(r.id);assert.deepStrictEqual(s.shown,r);for(let i=0;i<r.snapshots.length;i++){s=act(s,'step',i);check(r.id+'-boundary-'+i,s.step===i&&s.shown.snapshots[i].phase===r.snapshots[i].phase&&!s.answer);}s=act(s,'answer');check('answer-'+r.id,s.answer);s=act(s,'prediction','fault');clear('prediction-clear-'+r.id,s);}
let s=shown('copy-zero-main');s=act(s,'answer');clear('reset',act(s,'reset'));clear('case-change',act(s,'case','main-early'));
clear('prediction-required',act(S.initial(),'load'),true);
for(const mode of ['missing','altered','old']){let a=shown('copy-zero-main');a=act(a,'answer');a=act(a,'mode',mode);clear('mode-clear-'+mode,a);a=act(a,'load');clear('refusal-'+mode,a,true);a=act(a,'mode','normal');a=act(a,'load');check('recovery-'+mode,!!a.shown&&!a.error);}
const changes=[['run-id',d=>d.run_id='calculation-20000101T000000Z'],['sha',d=>d.result_sha256='0'.repeat(64)],['time',d=>d.result.observed_at_utc='2000-01-01T00:00:00+00:00'],['fixture',d=>d.fixtures.ram_initial[0]=0],['main',d=>d.result.cases[4].main.initialized=true],['write',d=>d.result.cases[5].writes.pop()],['empty',d=>d.result.cases[6].write_count=1]];
for(const [name,mutate] of changes){const d=JSON.parse(JSON.stringify(D));mutate(d);let a=shown('copy-zero-main');a=act(a,'answer');clear('external-mutation-'+name,act(a,'load',undefined,d),true);}
const report={title:'Atlas saved reader state checks',passed:true,checks,count:checks.length,model_rerun:false,browser_executed:false,dom_verified:false,sources:Object.fromEntries(['reader-state.js','reader-data.js','reader-expectations.js','check-reader.cjs'].map(n=>[n,sha(n)]))};
fs.writeFileSync(path.join(root,'observations/reader-state-check.json'),JSON.stringify(report,null,2)+'\n');console.log(JSON.stringify({passed:true,count:checks.length,browser_executed:false}));

'use strict';
// Atlas: saved data and finite reader transitions only; no WASI or browser.
const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict'),crypto=require('node:crypto');
const path=require('node:path'),root=__dirname,S=require('./reader-state.js');
const scope={window:{}};vm.runInNewContext(fs.readFileSync(path.join(root,'reader-data.js'),'utf8'),scope);const D=JSON.parse(JSON.stringify(scope.window.ATLAS_WASI_DATA));
let count=0;const check=(ok,label)=>{assert.ok(ok,label);count++;};const equal=(a,b,label)=>{assert.deepEqual(a,b,label);count++;};
const report=JSON.parse(fs.readFileSync(path.join(root,'observations',D.run_id,'report.json')));
for(const id of S.ids){
 const file=path.join(root,'observations',D.run_id,id+'.json'),saved=JSON.parse(fs.readFileSync(file));
 equal(D.records[id],saved,id+' equals complete saved WASI record');equal(S.validate(D,id),saved,id+' accepted');
 let s=S.change(S.initial(),'case',id);check(!s.shown&&!s.answer&&s.prediction===null,id+' initially hidden');s=S.read(s,D);check(!s.shown&&!!s.error,id+' prediction required');
 s=S.change(s,'prediction',S.expected[id][0]);check(!s.error&&!s.shown,id+' clear input error');s=S.read(s,D);check(s.shown&&!s.answer&&!s.error,id+' compare before answer');s.answer=true;
 for(const action of ['prediction','case','reset','mode']){let next=S.change(s,action,action==='prediction'?'bytes_observed':action==='case'?'granted':action==='mode'?'missing':undefined);check(!next.shown&&!next.answer&&!next.error,id+' '+action+' clears result');}
 for(const mode of ['missing','altered','old']){let t=S.read(S.change(s,'mode',mode),D);check(!t.shown&&!t.answer&&!!t.error,id+' rejects '+mode);t=S.read(S.change(t,'mode','normal'),D);check(t.shown&&!t.error,id+' recovers '+mode);}
 let wrong=S.read(S.change(s,'prediction',S.expected[id][0]==='bytes_observed'?'missing_entry':'bytes_observed'),D);check(wrong.shown&&wrong.prediction!==D.records[id].outcome.classification,id+' wrong prediction still compares');
}
check(report.cases.every(x=>x.child_reaped&&x.output_complete)&&report.fixture_cleanup,'parent cleanup saved');
console.log(JSON.stringify({title:'Atlas 保存readerの有限確認',passed:true,checks:count,cases:S.ids,actual_records_compared:4,runtime_executed:false,browser_executed:false},null,2));

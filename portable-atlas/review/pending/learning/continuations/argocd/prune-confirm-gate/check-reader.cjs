'use strict';
const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict'),crypto=require('node:crypto'),R=require('./reader-state.js');
const hash=n=>crypto.createHash('sha256').update(fs.readFileSync(path.join(__dirname,n))).digest('hex');
const report={kind:'confirm-gate-reader-state-check',started_at_utc:new Date().toISOString(),checks:[],refusals:[],browser_executed:false,live_executed:false,numerical_model_rerun:false,artifact_sha256:Object.fromEntries(['index.html','reader.css','reader-app.js','reader-state.js','reader-data.js','check-reader.cjs'].map(n=>[n,hash(n)])),old_model_sha256:hash('observations/model-check.json')};
const note=(name,detail)=>report.checks.push({name,detail,pass:true});
function cleared(s,label,empty=false){const v=R.view(s);assert.equal(s.step,0);assert.equal(s.answer,false);assert.equal(v.score,null);for(const k of ['groupsVisible','scanVisible','gateVisible'])assert.equal(v[k],false);if(empty){assert.equal(s.gate,null);assert.equal(s.blocker,null);}note(label,'段階・走査・ゲート・答えが未表示');}
function finish(id,gate,blocker){let s=R.predict(R.predict(R.initial(id),'gate',gate),'blocker',blocker);for(let i=0;i<3;i++)s=R.advance(s);return R.reveal(s);}
try{
 const oracle=JSON.parse(fs.readFileSync(path.join(__dirname,'hand-oracle.json'))).cases,run=JSON.parse(fs.readFileSync(path.join(__dirname,'observations/model-check.json')));
 assert.deepEqual(R.data.outcomes,oracle);assert.deepEqual(R.data.outcomes,run.outcomes);for(const[n,h]of Object.entries(R.data.bindings))assert.equal(hash(n),h);note('4ケース保存原票・手追跡・reader一致',true);
 for(const c of R.data.cases){const o=oracle[c.id],s=finish(c.id,o.gate,o.first_blocker||'none');assert.deepEqual(R.view(s).score,{gate:true,blocker:true});assert.deepEqual(R.view(s).outcome,o);note(c.id+' 全出力と予想',true);
  cleared(R.predict(s,'gate',o.gate==='pass'?'pending':'pass'),c.id+' ゲート予想変更');cleared(R.predict(s,'blocker','old-later'),c.id+' 資源予想変更');cleared(R.initial(c.id),c.id+' reset',true);
  let t=R.initial(c.id);t=R.advance(t);assert.ok(t.error);cleared(t,c.id+' 未選択エラー',true);t=R.predict(t,'gate','pass');assert.equal(t.error,null);t=R.advance(t);assert.ok(t.error);cleared(t,c.id+' 片方未選択');
  t=R.predict(t,'blocker','none');assert.equal(t.error,null);t=R.advance(t);assert.deepEqual([R.view(t).groupsVisible,R.view(t).scanVisible,R.view(t).gateVisible],[true,false,false]);t=R.advance(t);assert.deepEqual([R.view(t).groupsVisible,R.view(t).scanVisible,R.view(t).gateVisible],[true,true,false]);note(c.id+' 段階別公開と入力訂正',true);
  const w=finish(c.id,o.gate==='pass'?'pending':'pass','old-later');assert.deepEqual(R.view(w).score,{gate:false,blocker:false});note(c.id+' 誤予想照合',true);
 }
 for(const[name,fn]of [['unknown case',()=>R.initial('ghost')],['invalid gate',()=>R.predict(R.initial(),'gate','success')],['invalid blocker',()=>R.predict(R.initial(),'blocker','ghost')],['unknown key',()=>R.predict(R.initial(),'api','pass')],['early answer',()=>R.reveal(R.initial())]]){assert.throws(fn);report.refusals.push(name);}
 assert.equal(hash('observations/model-check.json'),report.old_model_sha256);report.status='pass';
}catch(e){report.status='fail';report.error=String(e.stack||e);process.exitCode=1;}
report.finished_at_utc=new Date().toISOString();if(process.argv.includes('--record'))fs.writeFileSync(path.join(__dirname,'observations/reader-state-check.json'),JSON.stringify(report,null,2)+'\n',{flag:'wx'});console.log(JSON.stringify({status:report.status,checks:report.checks.length,refusals:report.refusals.length,error:report.error},null,2));

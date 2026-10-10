'use strict';
const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict'),crypto=require('node:crypto'),R=require('./reader-state.js');
const hash=name=>crypto.createHash('sha256').update(fs.readFileSync(path.join(__dirname,name))).digest('hex');
const report={kind:'prune-last-reader-state-check',started_at_utc:new Date().toISOString(),checks:[],refusals:[],browser_executed:false,live_executed:false,numerical_model_rerun:false,artifact_sha256:Object.fromEntries(['index.html','reader.css','reader-app.js','reader-state.js','reader-data.js','check-reader.cjs'].map(n=>[n,hash(n)])),old_model_sha256:hash('observations/model-check.json')};
const note=(name,detail)=>report.checks.push({name,detail,pass:true});
function cleared(s,label,empty=false){const v=R.view(s);assert.equal(s.step,0);assert.equal(s.answer,false);assert.equal(v.score,null);assert.equal(v.ordinaryVisible,false);assert.equal(v.maximumVisible,false);assert.equal(v.finalVisible,false);if(empty){assert.equal(s.wave,'');assert.equal(s.selection,null);}note(label,'段階・候補・指定後・答えを初期化');}
function finish(id,wave,selected){let s=R.initial(id);s=R.setWave(s,wave);s=R.setSelection(s,selected);for(let i=0;i<3;i++)s=R.advance(s);return R.reveal(s);}
try{
 const oracle=JSON.parse(fs.readFileSync(path.join(__dirname,'hand-oracle.json'))).cases;
 const run=JSON.parse(fs.readFileSync(path.join(__dirname,'observations/model-check.json')));
 assert.deepEqual(R.data.outcomes,oracle);assert.deepEqual(R.data.outcomes,run.outcomes);for(const[n,d]of Object.entries(R.data.bindings))assert.equal(hash(n),d);
 note('原票・手計算・reader5ケースの同一性',true);
 for(const item of R.data.cases){const expected=oracle[item.id];const selection=expected.selected.join(',')||'none';const s=finish(item.id,String(expected.last_wave_candidate),selection);assert.deepEqual(R.view(s).score,{wave:true,selection:true});assert.deepEqual(R.view(s).outcome,expected);note(item.id+'全結果と予想一致',true);
  cleared(R.setWave(s,'6'),item.id+'候補予想変更');cleared(R.setSelection(s,R.choices[item.id].find(x=>x!==selection)),item.id+'対象予想変更');cleared(R.initial(item.id),item.id+'reset',true);
  let bad=R.advance(R.setWave(s,'abc'));assert.ok(bad.error);cleared(bad,item.id+'入力失敗で古い結果消去');assert.equal(R.setWave(bad,'1').error,null);note(item.id+'入力訂正でエラー消去',true);
  const wrong=finish(item.id,'100',R.choices[item.id].find(x=>x!==selection));assert.deepEqual(R.view(wrong).score,{wave:false,selection:false});note(item.id+'誤答照合',true);
 }
 cleared(R.initial('ordinary'),'失敗後の場面変更',true);
 for(const val of ['x','1.5','102','-101']){assert.throws(()=>R.parseWave(val));report.refusals.push('wave '+val);}
 assert.throws(()=>R.initial('ghost'));report.refusals.push('unknown case');assert.throws(()=>R.reveal(R.initial()));report.refusals.push('early answer');
 const missing=R.advance(R.initial());assert.ok(missing.error);cleared(missing,'未選択の応答');report.refusals.push('missing predictions');
 assert.equal(hash('observations/model-check.json'),report.old_model_sha256);report.status='pass';
}catch(error){report.status='fail';report.error=String(error.stack||error);process.exitCode=1;}
report.finished_at_utc=new Date().toISOString();if(process.argv.includes('--record'))fs.writeFileSync(path.join(__dirname,'observations/reader-state-check.json'),JSON.stringify(report,null,2)+'\n',{flag:'wx'});
console.log(JSON.stringify({status:report.status,checks:report.checks.length,refusals:report.refusals.length,error:report.error},null,2));

'use strict';
const fs=require('node:fs'),path=require('node:path'),crypto=require('node:crypto'),assert=require('node:assert/strict'),R=require('./reader-state.js');
const hash=n=>crypto.createHash('sha256').update(fs.readFileSync(path.join(__dirname,n))).digest('hex');
const report={title:'Atlas：期限教材の画面状態検査',started_at_utc:new Date().toISOString(),checks:[],refusals:[],browser_executed:false,numerical_model_rerun:false,source_sha256:Object.fromEntries(['index.html','reader.css','reader-app.js','reader-state.js','reader-data.js','check-reader.cjs'].map(n=>[n,hash(n)]))};
const note=n=>report.checks.push({name:n,pass:true});
function cleared(s,name,empty=false){assert.equal(s.compared,false);assert.equal(s.answer,false);assert.equal(s.tick,0);assert.equal(R.view(s).score,null);assert.equal(R.view(s).frame,null);assert.equal(R.view(s).fifoFrame,null);if(empty){assert.equal(s.average,null);assert.equal(s.deadline,null);}note(name);}
function ready(order,average,deadline){return R.compare(R.predict(R.predict(R.initial(order),'average',average),'deadline',deadline));}
try{const hand=JSON.parse(fs.readFileSync(path.join(__dirname,'hand-oracle.json'))),saved=JSON.parse(fs.readFileSync(path.join(__dirname,'observations/model-check.json')));
 for(const[n,h]of Object.entries(R.data.bindings))assert.equal(hash(n),h);
 assert.deepEqual(R.data.outcomes,saved.results.outcomes);assert.deepEqual(R.data.frames,saved.results.frames);note('保存結果と画面データの結合');
 for(const row of hand.cases){assert.deepEqual(R.data.outcomes[row.order],row);let s=ready(row.order,row.order==='ABC'?'equal':'lower',row.missed.length?'some':'all');s=R.reveal(s);assert.deepEqual(R.view(s).score,{average:true,deadline:true});note(row.order+' 手計算と予想一致');
  for(let t=0;t<=7;t++){const expected=Object.fromEntries([... 'ABC'].map(n=>[n,row.slots.slice(0,t).split(n).length-1===row.slots.split(n).length-1?'完了':t<7&&row.slots[t]===n?'実行中':'待ち']));s=R.tick(s,t);assert.deepEqual(R.view(s).frame,expected);assert.equal(s.answer,true);}note(row.order+' 8時点と同一条件の答え保持');
  cleared(R.predict(s,'average','higher'),row.order+' 平均予想の編集');cleared(R.predict(s,'deadline','all'),row.order+' 期限予想の編集');cleared(R.initial(row.order),row.order+' リセット',true);
  const wrong=R.reveal(ready(row.order,'higher',row.missed.length?'all':'some'));assert.deepEqual(R.view(wrong).score,{average:false,deadline:false});note(row.order+' 誤予想照合');
 }
 let s=R.compare(R.initial());assert.ok(s.error);cleared(s,'未選択エラー',true);s=R.predict(s,'average','lower');assert.equal(s.error,null);s=R.compare(s);assert.ok(s.error);cleared(s,'片方未選択エラー');s=R.predict(s,'deadline','some');assert.equal(s.error,null);s=R.compare(s);assert.equal(s.compared,true);note('入力訂正');
 for(const[name,fn]of [['unknown-order',()=>R.initial('ABA')],['unknown-prediction-key',()=>R.predict(R.initial(),'x','all')],['unknown-average',()=>R.predict(R.initial(),'average','all')],['early-answer',()=>R.reveal(R.initial())],['early-tick',()=>R.tick(R.initial(),1)],...[-1,8,1.5,true,'1'].map(v=>['invalid-tick '+v,()=>R.tick(s,v)])]){assert.throws(fn);report.refusals.push(name);}
 report.status='pass';
}catch(e){report.status='fail';report.error=String(e.stack||e);process.exitCode=1;}
report.finished_at_utc=new Date().toISOString();if(process.argv.includes('--record'))fs.writeFileSync(path.join(__dirname,'observations/reader-state-check.json'),JSON.stringify(report,null,2)+'\n',{flag:'wx'});console.log(JSON.stringify({status:report.status,checks:report.checks.length,refusals:report.refusals.length,error:report.error},null,2));

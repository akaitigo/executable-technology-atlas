'use strict';
const fs=require('fs'),path=require('path'),vm=require('vm'),assert=require('assert/strict'),crypto=require('crypto');
const root=__dirname,ctx={window:{}};
vm.runInNewContext(fs.readFileSync(path.join(root,'reader-data.js'),'utf8'),ctx);
const D=JSON.parse(JSON.stringify(ctx.window.ATLAS_SEARCH_DATA)),S=require('./reader-state.js');
const observed=JSON.parse(fs.readFileSync(path.join(root,'observations',D.run_id,'result.json'),'utf8'));
const checks=[];function ok(name,fn){fn();checks.push(name);}
ok('saved cases identical',()=>assert.deepEqual(D.cases,observed.cases));
ok('saved fixture identical',()=>assert.equal(D.fixture_sha256,observed.fixture_sha256));
for(const id of S.ids){
 const r=S.validate(D,id);ok(id+' 4 rows',()=>assert.equal(r.rows.length,4));
 let s=S.change(S.initial(),'mode',id);
 ok(id+' initially hidden',()=>assert(!s.shown&&!s.answer&&!s.prediction));
 s=S.read(s,D);ok(id+' missing prediction refused',()=>assert(!s.shown&&s.error));
 s=S.change(s,'prediction',S.expected[id].winner);s=S.read(s,D);
 ok(id+' valid read',()=>assert(s.shown&&!s.error));s={...s,answer:true};
 for(const kind of ['prediction','mode','reset']){
  const value=kind==='prediction'?'d2':kind==='mode'?'bm25-b0':undefined,n=S.change(s,kind,value);
  ok(id+' '+kind+' clears result/answer',()=>assert(!n.shown&&!n.answer&&!n.error));
 }
 for(const mode of ['missing','altered','old']){
  const n=S.change(s,'record',mode);ok(id+' '+mode+' clears',()=>assert(!n.shown&&!n.answer));
  const refused=S.read(n,D);ok(id+' '+mode+' refused',()=>assert(!refused.shown&&!refused.answer&&refused.error));
  const restored=S.read(S.change(refused,'record','normal'),D);ok(id+' '+mode+' recovered',()=>assert(restored.shown&&!restored.error));
 }
}
const hash=n=>crypto.createHash('sha256').update(fs.readFileSync(path.join(root,n))).digest('hex');
const result={title:'Atlas 保存結果と画面状態の有限確認',passed:true,checks,check_count:checks.length,source_sha256:Object.fromEntries(['reader-data.js','reader-state.js','check-reader.cjs'].map(n=>[n,hash(n)])),browser_executed:false,calculation_executed:false};
fs.writeFileSync(path.join(root,'observations/reader-state-check.json'),JSON.stringify(result,null,2)+'\n');console.log(JSON.stringify({passed:true,checks:checks.length}));

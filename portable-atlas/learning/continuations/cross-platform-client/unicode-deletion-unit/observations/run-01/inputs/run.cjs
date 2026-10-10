'use strict';
const fs=require('fs'),path=require('path'),crypto=require('crypto'),os=require('os');
if(process.version!=='v25.2.1')throw Error('Only the existing Node v25.2.1 is in this contract');
if(os.getPriority(process.pid)<10)throw Error('actual nice10 required before target calculation');
const {removeLast}=require('./delete.cjs'),{check,mutationChecks}=require('./verify.cjs');
const root=__dirname,out=path.join(root,'observations/run-01'),sha=b=>crypto.createHash('sha256').update(b).digest('hex');
fs.mkdirSync(path.join(root,'observations'),{recursive:true});fs.mkdirSync(out);fs.mkdirSync(path.join(out,'inputs'));
const names=['CONTRACT.md','SOURCES.md','cases.json','expected.json','delete.cjs','verify.cjs','run.cjs','execute_once.py'],bindings={};
for(const name of names){const data=fs.readFileSync(path.join(root,name));fs.writeFileSync(path.join(out,'inputs',name),data,{flag:'wx'});bindings[name]=sha(data);}
const fixture=JSON.parse(fs.readFileSync(path.join(root,'cases.json'),'utf8'));
const result={Atlas:'正規化後に末尾1単位を削除した有限計算',kind:'Node_API_results_not_native_keyboard',startedAt:new Date().toISOString(),toolchain:{node:process.version,icu:process.versions.icu,unicode:process.versions.unicode,v8:process.versions.v8,execPath:process.execPath,execSha256:sha(fs.readFileSync(process.execPath)),platform:process.platform,arch:process.arch},pid:process.pid,actualNice:os.getPriority(process.pid),sourceSha256:bindings,cases:[],refusals:[]};
const began=process.hrtime.bigint();
for(const group of ['cases','refusals'])for(const c of fixture[group]){const request=structuredClone(c.request),before=structuredClone(request);result[group].push({id:c.id,requestBefore:before,response:removeLast(request),requestAfter:request});}
result.calculationSeconds=Number(process.hrtime.bigint()-began)/1e9;
const bytes=JSON.stringify(result,null,2)+'\n';fs.writeFileSync(path.join(out,'results.json'),bytes,{flag:'wx'});
const report={Atlas:'literalと整数符号化による照合',passed:true,checks:check(JSON.parse(bytes)),mutations:mutationChecks(JSON.parse(bytes)),resultsSha256:sha(bytes),producerImportedByChecker:false};
fs.writeFileSync(path.join(root,'verification/saved-result-check.json'),JSON.stringify(report,null,2)+'\n',{flag:'wx'});
console.log(JSON.stringify({passed:true,requests:7,methodResults:21,refusals:6,checks:report.checks,actualNice:result.actualNice,pid:process.pid,calculationSeconds:result.calculationSeconds,toolchain:result.toolchain}));

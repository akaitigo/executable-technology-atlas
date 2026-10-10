'use strict';
// Atlas: no producer import, normalization API, Segmenter or native text encoding.
const fs=require('fs'),path=require('path'),assert=require('assert/strict');
const read=n=>JSON.parse(fs.readFileSync(path.join(__dirname,n),'utf8'));
function utf16(scalars){return scalars.flatMap(n=>n<65536?[n]:[0xd800+Math.floor((n-65536)/1024),0xdc00+(n-65536)%1024]);}
function utf8(scalars){return scalars.flatMap(n=>n<128?[n]:n<2048?[192+Math.floor(n/64),128+n%64]:n<65536?[224+Math.floor(n/4096),128+Math.floor(n/64)%64,128+n%64]:[240+Math.floor(n/262144),128+Math.floor(n/4096)%64,128+Math.floor(n/64)%64,128+n%64]);}
function clustersAfter(scalars){
 const key=scalars.join(',');
 const literal={'':[],'65':[[65]],'65,101':[[65],[101]],'65,128105,8205':[[65],[128105,8205]]};
 assert.ok(Object.hasOwn(literal,key),'fixed after cluster list');return literal[key];
}
function check(result){
 const input=read('cases.json'),expected=read('expected.json');let checks=0;
 function eq(a,b,label){checks++;assert.deepEqual(a,b,label);}
 function measured(actual,scalars,clusters,label){
  eq(actual.scalarValid,true,label+'/valid');eq(actual.scalars,scalars,label+'/scalars');eq(actual.utf16Units,utf16(scalars),label+'/units');eq(actual.utf8,utf8(scalars),label+'/bytes');
  const text=String.fromCodePoint(...scalars);eq(actual.text,text,label+'/text');eq(actual.escapedText,JSON.stringify(text),label+'/escaped');
  let offset=0;const parts=clusters.map(values=>{const start=offset,u=utf16(values);offset+=u.length;return{text:String.fromCodePoint(...values),index:start,end:offset,scalars:values,utf16Units:u};});eq(actual.segments,parts,label+'/segments');
 }
 eq(result.cases.map(x=>x.id),input.cases.map(x=>x.id),'ids');eq(result.refusals.map(x=>x.id),input.refusals.map(x=>x.id),'refusal ids');
 for(const [i,c]of result.cases.entries()){
  const x=expected.cases[c.id],request=input.cases[i].request;eq(c.requestBefore,request,'before');eq(c.requestAfter,request,'after');eq(c.response.accepted,true,'accepted');eq(c.response.reason,null,'reason');const p=c.response.payload;
  eq(p.normalization,request.normalization,'form');eq(p.normalizationCalls,request.normalization==='none'?0:1,'normalization calls');measured(p.source,x.sourceScalars,x.sourceClusters,c.id+'/source');measured(p.normalized,x.normalizedScalars,x.normalizedClusters,c.id+'/normalized');
  eq(p.methods.map(m=>m.method),expected.methodOrder,'methods');const before=utf16(x.normalizedScalars);
  for(const m of p.methods){const want=x.after[m.method],afterUnits=want.valuesKind==='utf16-units'?want.values:utf16(want.values);
   eq(m.cutOffset,afterUnits.length,'cut offset');eq(m.removedUtf16Units,before.slice(afterUnits.length),'removed units');eq(m.removedUnitCount,want.removedUnitCount,'removed count');eq(m.matchesAppPolicy,want.matchesAppPolicy,'policy');eq(m.after.utf16Units,afterUnits,'after units');eq(m.after.scalarValid,want.scalarValid,'after valid');
   if(want.scalarValid)measured(m.after,want.values,clustersAfter(want.values),c.id+'/'+m.method);
   else{for(const key of ['text','scalars','utf8','segments'])eq(m.after[key],null,'invalid '+key);eq(m.after.escapedText,JSON.stringify(String.fromCharCode(...afterUnits)),'invalid escaped');}
  }
 }
 for(const [i,c]of result.refusals.entries()){eq(c.requestBefore,input.refusals[i].request,'refused before');eq(c.requestAfter,input.refusals[i].request,'refused after');eq(c.response,expected.refusals[c.id],'refused response');}
 return checks;
}
function mutationChecks(result){
 const variants=[],copy=()=>JSON.parse(JSON.stringify(result));let r=copy();r.cases.pop();variants.push(['missing-case',r]);
 r=copy();r.cases[1].response.payload.methods[2].after.utf16Units=[65,101];variants.push(['wrong-egc-result',r]);
 r=copy();r.cases[4].response.payload.methods[0].after.utf8=[65,239,191,189];variants.push(['silent-replacement',r]);
 r=copy();r.cases[5].response.payload.methods[1].matchesAppPolicy=true;variants.push(['scalar-equals-egc',r]);
 r=copy();r.cases[6].response.payload.methods[0].removedUnitCount=1;variants.push(['empty-counted',r]);
 r=copy();r.cases[2].response.payload.normalized.segments[1].index=2;variants.push(['old-offset',r]);
 r=copy();r.refusals[0].response.payload={};variants.push(['refusal-payload',r]);
 return variants.map(([name,value])=>{let rejected=false;try{check(value);}catch{rejected=true;}assert.ok(rejected,name);return{name,rejected};});
}
module.exports={check,mutationChecks};
if(require.main===module){const result=read('observations/run-01/results.json');console.log(JSON.stringify({Atlas:'保存値の再照合',checks:check(result),mutations:mutationChecks(result)}));}

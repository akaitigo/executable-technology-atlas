(function(root){
 'use strict';
 const central=['same-bin-ab','same-bin-ba','separated-ab','separated-ba','exact-tie-ab','exact-tie-ba'];
 const boundaries=[3,4].flatMap(b=>['zero','half-before','half','half-after','clear-bin','one'].map(n=>`b${b}-${n}`));
 const ids=[...central,...boundaries],winners=['A','B','F','background'],modes=['normal','missing','altered','old'];
 function canonical(value){if(Array.isArray(value))return '['+value.map(canonical).join(',')+']';if(value!==null&&typeof value==='object')return '{'+Object.keys(value).sort().map(k=>JSON.stringify(k)+':'+canonical(value[k])).join(',')+'}';return JSON.stringify(value);}
 function initial(){return {caseId:central[0],exactPrediction:'',quantizedPrediction:'',mode:'normal',step:0,shown:null,answer:false,error:''};}
 function clear(s){return {...s,step:0,shown:null,answer:false,error:''};}
 function valid(data,expected){return !!data&&!!expected&&canonical(data)===canonical(expected)&&data.schema===1&&typeof data.run_id==='string'&&typeof data.observed_at_utc==='string'&&typeof data.result_sha256==='string';}
 function transition(s,event,data,expected){
  if(event.type==='reset')return initial();
  if(event.type==='case'&&ids.includes(event.value))return {...clear(s),caseId:event.value,exactPrediction:'',quantizedPrediction:''};
  if(event.type==='prediction'&&['exactPrediction','quantizedPrediction'].includes(event.key)&&winners.includes(event.value))return {...clear(s),[event.key]:event.value};
  if(event.type==='mode'&&modes.includes(event.value))return {...clear(s),mode:event.value};
  if(event.type==='load'){
   const next=clear(s);
   if(!s.exactPrediction||!s.quantizedPrediction)return {...next,error:'両方式の予想を選んでください。'};
   if(!valid(data,expected))return {...next,error:'保存記録が欠落しているか、固定した内容・由来と一致しません。'};
   const c=[...data.result.central,...data.result.boundaries].find(x=>x.id===s.caseId);
   if(!c)return {...next,error:'選んだ条件の保存記録がありません。'};
   return {...next,shown:c};
  }
  if(event.type==='step'&&s.shown&&Number.isInteger(event.value)&&event.value>=0&&event.value<=s.shown.trace.length)return {...s,step:event.value,answer:false,error:''};
  if(event.type==='answer'&&s.shown)return {...s,answer:true};
  return s;
 }
 function snapshot(s){if(!s.shown)return null;return s.step===0?{exact:{depth:'1',winner:null},quantized:{code:s.shown.maximum,winner:null}}:{exact:s.shown.trace[s.step-1].exact_after,quantized:s.shown.trace[s.step-1].quantized_after};}
 root.ATLAS_STATE={central,boundaries,ids,canonical,initial,transition,snapshot,valid};
 if(typeof module!=='undefined')module.exports=root.ATLAS_STATE;
})(globalThis);

/* Atlas: saved-record state only; no receiver calculation or networking. */
(function(root){
'use strict';
const ids=['constant-phase','constant-rate','rate-reversal','first-pilot-missing'];
const predictions=['equal','hold','extrapolate','unavailable'];
const modes=['normal','missing','altered','old'];
function canonical(x){if(x===null||typeof x!=='object')return JSON.stringify(x);if(Array.isArray(x))return '['+x.map(canonical).join(',')+']';return '{'+Object.keys(x).sort().map(k=>JSON.stringify(k)+':'+canonical(x[k])).join(',')+'}';}
function initial(id=ids[0]){return {id:ids.includes(id)?id:ids[0],prediction:null,mode:'normal',n:2,shown:null,answer:false,error:''};}
function cleared(s){return {...s,n:2,shown:null,answer:false,error:''};}
function transition(s,a,data,expected){
 if(a.type==='case'&&ids.includes(a.value))return initial(a.value);
 if(a.type==='prediction'&&predictions.includes(a.value))return {...cleared(s),prediction:a.value};
 if(a.type==='mode'&&modes.includes(a.value))return {...cleared(s),mode:a.value};
 if(a.type==='reset')return initial(s.id);
 if(a.type==='step')return Number.isInteger(a.value)&&a.value>=2&&a.value<=5&&s.shown?{...s,n:a.value,answer:false,error:''}:s;
 if(a.type==='answer')return s.shown?{...s,answer:true}:s;
 if(a.type!=='load')return s;
 let next=cleared(s);
 if(!s.prediction)return {...next,error:'先に、どちらが有利か予想を選んでください。'};
 try{
  let candidate=data?JSON.parse(JSON.stringify(data)):null;
  if(s.mode==='missing')candidate=null;
  if(s.mode==='altered'&&candidate)candidate.result.cases[0].methods[0].receiver.rows[0].corrected[0]='-1';
  if(s.mode==='old'&&candidate)candidate.run_id='calculation-other';
  if(!candidate||!expected||canonical(candidate)!==canonical(expected))throw Error('保存記録が欠落・変更されているか、由来が一致しません。');
  if(candidate.result.status!=='observed'||candidate.result.scope.model_only!==true)throw Error('保存記録の範囲が一致しません。');
  const shown=candidate.result.cases.find(c=>c.id===s.id);
  if(!shown)throw Error('選んだ条件の保存値がありません。');
  return {...next,shown};
 }catch(e){return {...next,error:'読取り拒否：'+e.message};}
}
const api={ids,predictions,modes,initial,transition,canonical};
if(typeof module!=='undefined'&&module.exports)module.exports=api;else root.ATLAS_PHASE_STATE=api;
})(typeof window!=='undefined'?window:globalThis);

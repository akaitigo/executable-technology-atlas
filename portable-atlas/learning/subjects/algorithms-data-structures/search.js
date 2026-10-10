/* 独自実装。NodeとBrowserが同じ関数を実行する。図の再生状態は別管理。 */
(function(root){
  'use strict';
  const version='binary-range-lesson/1';
  function validate(a,x){
    if(!Array.isArray(a)||a.length>32||!a.every(v=>Number.isSafeInteger(v)&&Math.abs(v)<=999)||!Number.isSafeInteger(x)||Math.abs(x)>999)throw Error('整数-999〜999、配列32件以内を指定してください');
  }
  function partition(a,x,lo,hi){return {bounds:0<=lo&&lo<=hi&&hi<=a.length,left:a.slice(0,lo).every(v=>v<x),right:a.slice(hi).every(v=>v>=x)};}
  function binary(a,x,mode='correct'){
    validate(a,x);if(!['correct','off-by-one','stalled','unchecked'].includes(mode))throw Error('未知の方式');
    let sorted=true,preconditionComparisons=0;for(let i=1;i<a.length;i++){preconditionComparisons++;if(a[i-1]>a[i])sorted=false;}
    let lo=0,hi=a.length;const states=[{lo,hi,mid:null,probe:null,comparisons:0,action:'初期化',invariant:partition(a,x,lo,hi)}];
    const result={version,mode,input:[...a],target:x,sorted,preconditionComparisons,states,iterations:0,searchComparisons:0,exactComparisons:0,position:null,index:null,diagnostics:[]};
    if(!sorted&&mode!=='unchecked'){result.status='refused';result.diagnostics.push('未整列：二分探索の前提を満たさない');return result;}
    while(lo<hi){
      const mid=lo+Math.floor((hi-lo)/2),oldLo=lo,oldHi=hi,probe=a[mid];result.iterations++;result.searchComparisons++;
      if(probe<x)lo=mode==='stalled'?mid:mid+1;else hi=mode==='off-by-one'?mid-1:mid;
      const invariant=partition(a,x,lo,hi),progress=hi-lo<oldHi-oldLo;
      states.push({lo,hi,mid,probe,comparisons:result.searchComparisons,previous:[oldLo,oldHi],action:probe<x?(mode==='stalled'?'lo = mid（異常）':'lo = mid + 1'):(mode==='off-by-one'?'hi = mid - 1（異常）':'hi = mid'),invariant,progress});
      if(!Object.values(invariant).every(Boolean))result.diagnostics.push('不変条件破れ：iteration '+result.iterations);
      if(!progress){result.status='stalled';result.diagnostics.push('範囲が縮まらない。教材の診断器が停止した（本来の異常ループは継続する）');return result;}
      if(!invariant.bounds){result.status='invalid-range';return result;}
    }
    result.position=lo;if(lo<a.length){result.exactComparisons=1;if(a[lo]===x)result.index=lo;}
    result.status=result.diagnostics.length?'incorrect':'completed';return result;
  }
  function linear(a,x){validate(a,x);const visited=[];for(let i=0;i<a.length;i++){visited.push(i);if(a[i]===x)return{index:i,comparisons:visited.length,visited};}return{index:null,comparisons:visited.length,visited};}
  const api={version,binary,linear};if(typeof module!=='undefined'&&module.exports)module.exports=api;else root.SearchLesson=api;
})(typeof globalThis==='undefined'?this:globalThis);

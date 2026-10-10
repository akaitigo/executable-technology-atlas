(function(root){
  'use strict';
  const original=typeof module!=='undefined'&&module.exports?require('./core.js').contains:root.contains;
  function lower(x,lo,hi){const afterStart=x>lo;const beforeEnd=x<hi;return afterStart&&beforeEnd;}
  function upper(x,lo,hi){const afterStart=x>=lo;const beforeEnd=x<=hi;return afterStart&&beforeEnd;}
  function either(x,lo,hi){const afterStart=x>=lo;const beforeEnd=x<hi;return afterStart||beforeEnd;}
  function empty(x,lo,hi){const afterStart=x>=lo;const beforeEnd=x<hi;return lo===hi||(afterStart&&beforeEnd);}
  function equivalent(x,lo,hi){const afterStart=!(x<lo);const beforeEnd=!(x>=hi);return afterStart&&beforeEnd;}
  const variants=[{id:'original',name:'元の関数',fn:original},{id:'lower',name:'M1：下端を含めない',fn:lower},{id:'upper',name:'M2：上端を含める',fn:upper},{id:'either',name:'M3：AND→OR',fn:either},{id:'empty',name:'M4：空区間を受理',fn:empty},{id:'equivalent',name:'E1：比較の否定形',fn:equivalent,equivalent:true}];
  // 仕様oracle：整数区間の要素を列挙。対象関数の比較式をコピーしない。
  function oracle(x,lo,hi){if(![x,lo,hi].every(Number.isSafeInteger)||Math.min(x,lo,hi)<-10||Math.max(x,lo,hi)>10||lo>hi)throw Error('教材oracleは-10〜10の整数、lo<=hiのみ');return Array.from({length:hi-lo},(_,i)=>lo+i).includes(x);}
  const weak=[{id:'inside',name:'中ほど',x:3,lo:2,hi:5},{id:'below',name:'下端より外',x:1,lo:2,hi:5},{id:'above',name:'上端より外',x:6,lo:2,hi:5}];
  const additions={lower:[{id:'lower-boundary',name:'下端そのもの',x:2,lo:2,hi:5}],upper:[{id:'upper-boundary',name:'上端そのもの',x:5,lo:2,hi:5}],empty:[{id:'empty-interval',name:'空区間',x:2,lo:2,hi:2}],property:[]};
  for(let lo=-3;lo<=3;lo++)for(let hi=lo;hi<=3;hi++)for(let x=-4;x<=4;x++)additions.property.push({id:`finite/${x}/${lo}/${hi}`,name:'有限集合の仕様照合',x,lo,hi});
  function run(enabled=[]){if(!Array.isArray(enabled)||new Set(enabled).size!==enabled.length||enabled.some(k=>!(k in additions)))throw Error('未知・重複の追加テスト');const tests=[...weak,...enabled.flatMap(k=>additions[k])].map(t=>({...t,expected:oracle(t.x,t.lo,t.hi)}));const matrix=variants.map(v=>{const results=tests.map(t=>({test:t.id,actual:v.fn(t.x,t.lo,t.hi),expected:t.expected}));const failed=results.filter(r=>r.actual!==r.expected).map(r=>r.test);return{id:v.id,name:v.name,source:v.fn.toString(),equivalent:v.equivalent===true,results,failed,status:v.id==='original'?(failed.length?'failed':'passed'):(failed.length?'killed':'survived')};});const all=matrix.filter(v=>v.id!=='original'),scored=all.filter(v=>!v.equivalent);return{version:'quality-interval-lesson/1',enabled,tests,matrix,score:{killed:scored.filter(v=>v.status==='killed').length,total:scored.length},rawScore:{killed:all.filter(v=>v.status==='killed').length,total:all.length},equivalentTreatment:'E1 excluded only for the declared finite-integer domain; survives both sets; no automatic equivalence inference'};}
  const api={run,oracle,variants,weak,additions};if(typeof module!=='undefined'&&module.exports)module.exports=api;else root.QualityLesson=api;
})(globalThis);

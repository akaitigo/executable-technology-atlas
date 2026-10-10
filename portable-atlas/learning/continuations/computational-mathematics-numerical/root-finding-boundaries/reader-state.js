(function (root) {
  'use strict';
  const IDS=['cubic-cycle','cubic-local','zero-derivative','bad-bracket','exact-endpoint'];
  const same=(a,b)=>{
    if(a===null||b===null||typeof a!=='object'||typeof b!=='object') return a===b;
    if(Array.isArray(a)!==Array.isArray(b))return false;
    const ka=Object.keys(a),kb=Object.keys(b);
    return ka.length===kb.length&&ka.every(k=>Object.hasOwn(b,k)&&same(a[k],b[k]));
  };
  function initial(){return {case_id:IDS[0],prediction_bisection:'',prediction_newton:'',mode:'saved',shown:null,answer:false,error:'',indices:{bisection:0,newton:0}};}
  function cleared(s){return {...s,shown:null,answer:false,error:'',indices:{bisection:0,newton:0}};}
  function transition(state,action,data,expected){
    let s={...state,indices:{...state.indices}};
    if(action.type==='reset')return initial();
    if(action.type==='case'&&IDS.includes(action.value))return {...cleared(s),case_id:action.value};
    if(action.type==='prediction'&&['bisection','newton'].includes(action.method))return {...cleared(s),['prediction_'+action.method]:action.value};
    if(action.type==='mode'&&['saved','missing','altered','old'].includes(action.value))return {...cleared(s),mode:action.value};
    if(action.type==='load'){
      s=cleared(s);
      if(!s.prediction_bisection||!s.prediction_newton)return {...s,error:'両方法の停止理由を予想してください。'};
      let candidate=data===null?null:JSON.parse(JSON.stringify(data));
      if(s.mode==='missing')candidate=null;
      if(candidate&&s.mode==='altered')candidate.values.cases[0].newton.estimate='999';
      if(candidate&&s.mode==='old')candidate.run_id='root-boundaries-old-saved-run';
      if(!candidate||!expected||!same(candidate,expected)||candidate.schema!=='atlas-root-boundaries-reader-v1')return {...s,error:'保存記録を確認できません。表示していた数値・答え・詳細を消去しました。'};
      const chosen=candidate.values.cases.find(c=>c.id===s.case_id);
      if(!chosen)return {...s,error:'選んだ条件の記録がありません。'};
      return {...s,shown:{case_id:s.case_id,payload:chosen,run_id:candidate.run_id,observed_at_utc:candidate.observed_at_utc,result_sha256:candidate.result_sha256}};
    }
    if(action.type==='step'&&s.shown&&['bisection','newton'].includes(action.method)){
      const max=Math.max(0,s.shown.payload[action.method].rows.length-1);
      s.indices[action.method]=Math.max(0,Math.min(max,s.indices[action.method]+action.delta));s.answer=false;return s;
    }
    if(action.type==='answer'&&s.shown)return {...s,answer:true};
    return s;
  }
  const api={IDS,same,initial,transition};
  if(typeof module!=='undefined'&&module.exports)module.exports=api;
  root.RootBoundaryState=api;
})(typeof globalThis!=='undefined'?globalThis:this);

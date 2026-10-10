(function(root){
  'use strict';
  const IDS=['synchronized','staggered','skewed','budget-five'];
  const same=(a,b)=>{
    if(a===null||b===null||typeof a!=='object'||typeof b!=='object')return a===b;
    if(Array.isArray(a)!==Array.isArray(b))return false;
    if(Array.isArray(a))return a.length===b.length&&a.every((v,i)=>same(v,b[i]));
    const keys=Object.keys(a);return keys.length===Object.keys(b).length&&keys.every(k=>Object.hasOwn(b,k)&&same(a[k],b[k]));
  };
  const initial=()=>({case_id:IDS[0],prediction:'',mode:'saved',shown:null,index:0,answer:false,error:''});
  const clear=s=>({...s,shown:null,index:0,answer:false,error:''});
  const refused=s=>({...s,error:'保存記録を確認できません。数値・図・答え・詳細を消去しました。'});
  function transition(state,action,data,expected){
    let s={...state};
    if(action.type==='reset')return initial();
    if(action.type==='case'&&IDS.includes(action.value))return {...clear(s),case_id:action.value};
    if(action.type==='prediction'&&['all','not-all'].includes(action.value))return {...clear(s),prediction:action.value};
    if(action.type==='mode'&&['saved','missing','altered','old'].includes(action.value))return {...clear(s),mode:action.value};
    if(action.type==='load'){
      s=clear(s);
      if(!s.prediction)return {...s,error:'全員が成功するか予想してください。'};
      if(!data||!expected||!same(data,expected)||data.schema!=='atlas-retry-concentration-reader-v1')return refused(s);
      let candidate=JSON.parse(JSON.stringify(data));
      if(s.mode==='missing')candidate=null;
      if(s.mode==='altered')candidate.values.cases[3].ticks[2].clients[2].retries_remaining=1;
      if(s.mode==='old')candidate.run_id='retry-concentration-old-record';
      if(!candidate||!same(candidate,expected))return refused(s);
      const c=candidate.values.cases.find(x=>x.id===s.case_id);
      if(!c)return refused(s);
      return {...s,shown:{case_id:s.case_id,payload:c,fixture:candidate.fixture.cases.find(x=>x.id===s.case_id),
        run_id:candidate.run_id,observed_at_utc:candidate.observed_at_utc,result_sha256:candidate.result_sha256}};
    }
    if(action.type==='step'&&s.shown&&[-1,1].includes(action.delta))return {...s,index:Math.max(0,Math.min(7,s.index+action.delta)),answer:false};
    if(action.type==='answer'&&s.shown)return {...s,answer:true};
    return s;
  }
  const api={IDS,same,initial,transition};root.RetryConcentrationState=api;
  if(typeof module!=='undefined'&&module.exports)module.exports=api;
})(typeof globalThis!=='undefined'?globalThis:this);

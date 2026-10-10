(function(root){
  'use strict';
  const ids=['copy-zero-main','zero-copy-main','skip-copy','skip-zero','main-early','copy-one-past','empty-regions'];
  const stable=v=>Array.isArray(v)?'['+v.map(stable).join(',')+']':v&&typeof v==='object'?'{'+Object.keys(v).sort().map(k=>JSON.stringify(k)+':'+stable(v[k])).join(',')+'}':JSON.stringify(v);
  const initial=(caseId=ids[0])=>({caseId,prediction:null,mode:'normal',shown:null,step:0,answer:false,error:''});
  const clear=s=>({...s,shown:null,step:0,answer:false,error:''});
  function transition(s,event,data,expected){
    if(event.type==='case')return ids.includes(event.value)?initial(event.value):s;
    if(event.type==='prediction')return ['pass','fault'].includes(event.value)?{...clear(s),prediction:event.value}:s;
    if(event.type==='mode')return ['normal','missing','altered','old'].includes(event.value)?{...clear(s),mode:event.value}:s;
    if(event.type==='reset')return initial(s.caseId);
    if(event.type==='step')return s.shown&&Number.isInteger(event.value)&&event.value>=0&&event.value<s.shown.snapshots.length?{...s,step:event.value,answer:false}:s;
    if(event.type==='answer')return s.shown?{...s,answer:true}:s;
    if(event.type!=='load')return s;
    let next=clear(s);
    if(!s.prediction)return {...next,error:'先に予想を選んでください。'};
    try{
      if(!data||!expected)throw Error('missing');
      const candidate=JSON.parse(JSON.stringify(data));
      if(s.mode==='missing')candidate.result.cases.pop();
      if(s.mode==='altered')candidate.result.cases[0].final_ram[6]=0;
      if(s.mode==='old')candidate.run_id='previous-run';
      if(stable(candidate)!==stable(expected))throw Error('record mismatch');
      const row=candidate.result.cases.find(c=>c.id===s.caseId);
      if(!row)throw Error('case missing');
      return {...next,shown:row};
    }catch(_){return {...next,error:'保存した記録の欠落・変更・由来の不一致を検出しました。古い結果は表示しません。'};}
  }
  const api={ids,initial,transition,stable};root.AtlasStartupState=api;
  if(typeof module!=='undefined')module.exports=api;
})(typeof window!=='undefined'?window:globalThis);

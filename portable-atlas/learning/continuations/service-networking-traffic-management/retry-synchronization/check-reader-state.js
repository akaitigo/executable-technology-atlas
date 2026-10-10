'use strict';
globalThis.checkRetryReader=function(S,D,E){
  const checks=[];
  function check(id,ok){if(!ok)throw new Error(id);checks.push({id,passed:true});}
  function act(s,a,d=D){return S.transition(s,a,d,E);}
  const cleared=s=>s.shown===null&&!s.answer&&s.index===0;
  let s=act(S.initial(),{type:'load'});check('prediction required',cleared(s)&&!!s.error);
  for(const id of S.IDS){
    s=act(S.initial(),{type:'case',value:id});s=act(s,{type:'prediction',value:'all'});s=act(s,{type:'load'});
    check(id+' loaded',s.shown?.case_id===id&&s.error==='');
    for(let i=0;i<8;i++){check(id+' tick '+i,s.index===i&&s.shown.payload.ticks[i].tick===i);s=act(s,{type:'step',delta:1});}
    check(id+' upper bound',s.index===7);
    s=act(s,{type:'answer'});check(id+' answer',s.answer);
    s=act(s,{type:'step',delta:-1});check(id+' step clears answer',s.index===6&&!s.answer);
    for(let i=0;i<8;i++)s=act(s,{type:'step',delta:-1});check(id+' lower bound',s.index===0);
    s=act(s,{type:'answer'});s=act(s,{type:'prediction',value:'not-all'});check(id+' prediction clears',cleared(s)&&s.error==='');
  }
  function opened(){let s=act(S.initial(),{type:'prediction',value:'all'});s=act(s,{type:'load'});return act(s,{type:'answer'});}
  for(const mode of ['missing','altered','old']){
    s=act(opened(),{type:'mode',value:mode});check(mode+' mode clears',cleared(s));s=act(s,{type:'load'});check(mode+' rejected',cleared(s)&&!!s.error);
    s=act(s,{type:'mode',value:'saved'});s=act(s,{type:'load'});check(mode+' recovered',!!s.shown&&!s.error);
  }
  for(const bad of [null,{}, {...D,values:null}, {...D,values:{cases:[]}}]){
    s={...opened(),mode:'altered'};s=act(s,{type:'load'},bad);check('malformed plus alteration '+checks.length,cleared(s)&&!!s.error);
  }
  for(const [key,value] of [['run_id','retry-concentration-other'],['observed_at_utc','2026-10-07T00:00:00+00:00'],['result_sha256','f'.repeat(64)]]){
    s=act(opened(),{type:'load'},{...D,[key]:value});check('changed provenance '+key,cleared(s)&&!!s.error);
  }
  s=act(opened(),{type:'case',value:'budget-five'});check('case clears',cleared(s)&&s.case_id==='budget-five');
  s=act(opened(),{type:'reset'});check('reset exact',S.same(s,S.initial()));
  check('saved input unmodified',S.same(D,E));
  return {passed:true,checks,model_executions:0,DOM_executions:0,scope:'pure saved reader state only; not browser evidence'};
};

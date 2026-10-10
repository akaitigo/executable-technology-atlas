'use strict';
// Atlas: finite pure state checks. No DOM, browser, child or renderer execution.
const fs=require('fs'),path=require('path'),vm=require('vm'),crypto=require('crypto'),assert=require('assert/strict');
const root=__dirname,context={};vm.createContext(context);
for(const n of ['reader-state.js','reader-data.js','reader-expectations.js'])vm.runInContext(fs.readFileSync(path.join(root,n),'utf8'),context,{timeout:1000});
const S=context.ATLAS_STATE,D=context.ATLAS_DATA,E=context.ATLAS_EXPECTED;assert.ok(D&&E,'saved result must be connected first');
const checks=[];
function check(name,condition){assert.ok(condition,name);checks.push({name,passed:true});}
function ready(scene,pixel){let s=S.initial();s=S.transition(s,{type:'scene',value:scene},D,E);s=S.transition(s,{type:'pixel',value:pixel},D,E);s=S.transition(s,{type:'prediction',key:'centerPrediction',value:'0'},D,E);s=S.transition(s,{type:'prediction',key:'fourPrediction',value:'0'},D,E);return S.transition(s,{type:'load'},D,E);}
for(const scene of S.scenes)for(let pixel=0;pixel<4;pixel++){
  let s=ready(scene,pixel);check('load '+scene+'/'+pixel,!!s.shown&&!s.error);
  for(let step=0;step<s.shown[0].pixels[pixel].stages.length;step++){
    s=S.transition(s,{type:'step',value:step},D,E);
    check('stage '+scene+'/'+pixel+'/'+step,S.canonical(S.snapshots(s))===S.canonical(s.shown.map(r=>r.pixels[pixel].stages[step]))&&!s.answer);
  }
  const a=S.transition(s,{type:'answer'},D,E);check('answer '+scene+'/'+pixel,a.answer===true);
  for(const event of [{type:'scene',value:'edge-high'},{type:'pixel',value:(pixel+1)%4},{type:'prediction',key:'fourPrediction',value:'4'},{type:'mode',value:'missing'},{type:'reset'}]){
    const n=S.transition(a,event,D,E);check('clear '+scene+'/'+pixel+'/'+event.type,n.shown===null&&n.answer===false&&n.error==='');
  }
}
const original=ready('edge-low',1),shown=S.transition(original,{type:'answer'},D,E);
const changes=[
 ['run-id',d=>d.run_id='calculation-other'],['time',d=>d.observed_at_utc='2026-10-07T00:00:00+00:00'],
 ['digest',d=>d.result_sha256='f'.repeat(64)],['fixture',d=>d.fixture.layouts.four[0][0]='1/2'],
 ['scope',d=>d.result.scope.hardware_measured=true],['color',d=>d.result.results[1].pixels[1].stages[1].resolved_rgb=['1','0','0']],
 ['not-reached',d=>d.result.results[0].pixels[1].draws[0].events[0].accepted=false],
 ['different-condition',d=>d.result.results[0].scene_id='edge-high']];
for(const [name,change] of changes){const d=JSON.parse(JSON.stringify(D));change(d);const n=S.transition(shown,{type:'load'},d,E);check('refuse '+name,n.shown===null&&!n.answer&&!!n.error);const recovered=S.transition(n,{type:'load'},D,E);check('recover '+name,!!recovered.shown&&!recovered.error);}
const missing=S.transition(shown,{type:'load'},null,E);check('missing',!missing.shown&&!missing.answer&&!!missing.error);
check('no-prediction',!!S.transition(S.initial(),{type:'load'},D,E).error);
const sources=Object.fromEntries(['check-reader.cjs','reader-state.js','reader-data.js','reader-expectations.js'].map(n=>[n,crypto.createHash('sha256').update(fs.readFileSync(path.join(root,n))).digest('hex')]));
fs.writeFileSync(path.join(root,'observations/reader-state-check.json'),JSON.stringify({title:'Atlas pure multisample reader state checks',passed:true,checks,source_sha256:sources,dom_observed:false,model_executed:false,browser_started:false},null,2)+'\n');
process.stdout.write(JSON.stringify({passed:true,checks:checks.length,dom_observed:false})+'\n');

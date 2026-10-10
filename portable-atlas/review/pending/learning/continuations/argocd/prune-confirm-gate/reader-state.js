(function(root){
  'use strict';
  const data=typeof module!=='undefined'&&module.exports?require('./reader-data.js'):root.ConfirmGateData;
  const lookup=id=>{const item=data.cases.find(c=>c.id===id);if(!item)throw new Error('保存済みケースを選んでください');return item;};
  function initial(id='needs-confirmation'){lookup(id);return{id,gate:null,blocker:null,step:0,answer:false,error:null};}
  function predict(state,key,value){if(!['gate','blocker'].includes(key)||!(key==='gate'?['pass','pending']:['none','old-a','old-b','old-later']).includes(value))throw new Error('予想が範囲外です');return{...state,[key]:value,step:0,answer:false,error:null};}
  const ready=s=>s.gate!==null&&s.blocker!==null;
  function advance(s){if(!ready(s))return{...s,step:0,answer:false,error:'ゲートと、確認待ちになる資源の両方を予想してください。'};return{...s,step:Math.min(3,s.step+1),answer:false,error:null};}
  function reveal(s){if(s.step!==3||s.error)throw new Error('対照を最後まで進めてください');return{...s,answer:true};}
  function view(s){const outcome=data.outcomes[s.id];return{item:lookup(s.id),outcome,groupsVisible:s.step>=1,scanVisible:s.step>=2,gateVisible:s.step>=3,score:s.answer?{gate:s.gate===outcome.gate,blocker:s.blocker===(outcome.first_blocker||'none')}:null};}
  const api={data,lookup,initial,predict,ready,advance,reveal,view};if(typeof module!=='undefined'&&module.exports)module.exports=api;else root.ConfirmGateReader=api;
})(globalThis);

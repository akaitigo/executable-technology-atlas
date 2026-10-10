(function(root){
  'use strict';
  const data=typeof module!=='undefined'&&module.exports?require('./reader-data.js'):root.PruneLastData;
  const choices={ordinary:['none','old-low','old-high,old-low'],global:['none','old-low','old-high,old-low'],'resource-only':['none','old-low','old-high,old-low'],'all-negative':['none','old-low','old-high,old-low'],'presync-excluded':['none','old','old,pre-check']};
  const lookup=id=>{const item=data.cases.find(c=>c.id===id);if(!item)throw new Error('保存済みのケースを選んでください');return item;};
  function initial(id='global'){lookup(id);return{id,wave:'',selection:null,step:0,answer:false,error:null};}
  function setWave(state,wave){if(typeof wave!=='string')throw new Error('入力は文字列です');return{...state,wave,step:0,answer:false,error:null};}
  function setSelection(state,selection){if(!choices[state.id].includes(selection))throw new Error('対象の予想が範囲外です');return{...state,selection,step:0,answer:false,error:null};}
  const ready=s=>s.wave.trim()!==''&&s.selection!==null;
  function parseWave(text){if(!/^-?(0|[1-9][0-9]*)$/.test(text)||Number(text)<-100||Number(text)>101)throw new Error('候補waveは−100〜101の整数で入力してください（例：9、-1）。');return Number(text);}
  function advance(state){
    try{if(!ready(state))throw new Error('候補waveと上書き対象を予想してください。');parseWave(state.wave);}
    catch(error){return{...state,step:0,answer:false,error:error.message};}
    return{...state,step:Math.min(3,state.step+1),answer:false,error:null};
  }
  function reveal(state){if(state.step!==3||state.error)throw new Error('対照を最後まで進めてください');return{...state,answer:true};}
  function view(state){const item=lookup(state.id),outcome=data.outcomes[state.id];return{item,outcome,ordinaryVisible:state.step>=1,maximumVisible:state.step>=2,finalVisible:state.step>=3,score:state.answer?{wave:parseWave(state.wave)===outcome.last_wave_candidate,selection:state.selection===(outcome.selected.join(',')||'none')}:null};}
  const api={data,choices,lookup,initial,setWave,setSelection,ready,parseWave,advance,reveal,view};
  if(typeof module!=='undefined'&&module.exports)module.exports=api;else root.PruneLastReader=api;
})(globalThis);

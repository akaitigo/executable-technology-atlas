(function(global){'use strict';
const ids=['no-preopen','granted','rights-reduced','missing-file'];
const expected={'no-preopen':['descriptor_unavailable',8,null,null],'granted':['bytes_observed',0,0,'41746c61730a'],'rights-reduced':['rights_refusal',0,76,null],'missing-file':['missing_entry',0,44,null]};
function requireThat(ok,message){if(!ok)throw Error(message);}
function validate(data,id){
 requireThat(data&&data.schema===1&&data.run_id==='runtime-20261006T134814277752Z','保存記録がありません。');
 const r=data.records&&data.records[id];requireThat(r&&r.case_id===id,'選んだ条件の記録ではありません。');
 requireThat(r.module_sha256===data.module_sha256&&r.module_sha256==='41e5f0061be53f32aa28eb769a0527d91477a16d9e2e44fb5fbe2ada7916fadf','Wasmの対応が一致しません。');
 requireThat(r.stage==='observed'&&r.error===null&&r.cleanup?.complete&&r.host_fixture_read===false,'完了した実WASIの記録ではありません。');
 const e=expected[id],o=r.outcome;requireThat(o&&o.classification===e[0]&&o.prestat_errno===e[1]&&o.path_open_errno===e[2]&&o.hex===e[3],'返却値が確認済みの結果と一致しません。');
 const events=r.events;requireThat(Array.isArray(events)&&events.every((x,i)=>x.sequence===i),'呼出し順が欠けています。');
 requireThat(events[0]?.op==='fd_prestat_get'&&events[0].errno===e[1],'事前FDの結果が一致しません。');
 if(id==='no-preopen')requireThat(events.length===1&&o.read_status==='not_reached'&&o.nread_total===null,'未到達の処理に結果が混ざっています。');
 else {
  const open=events.find(x=>x.op==='path_open');requireThat(open?.errno===e[2]&&events.at(-1).op==='fd_close_preopen'&&events.at(-1).errno===0,'開く処理か後片付けが一致しません。');
  requireThat(BigInt(r.rights_before.base)&8192n&&BigInt(r.rights_before.inheriting)&2n,'必要な権限の記録がありません。');
  if(id==='rights-reduced')requireThat(o.reduce_errno===0&&BigInt(r.rights_after.base)===(BigInt(r.rights_before.base)&~8192n)&&r.rights_after.inheriting===r.rights_before.inheriting,'権限変更の範囲が一致しません。');
  const reads=events.filter(x=>x.op==='fd_read');
  if(id==='granted')requireThat(o.nread_total===6&&o.read_status==='success_then_eof'&&reads.length>=2&&reads.length<=8&&reads.every(x=>x.errno===0&&x.args[0]===open.output.opened_fd)&&reads.map(x=>x.output.hex).join('')==='41746c61730a'&&reads.at(-1).output.nread===0&&r.cleanup.file_close_errno===0,'読出しまたはEOFが一致しません。');
  else requireThat(reads.length===0&&o.read_status==='not_reached'&&o.nread_total===null&&open.output.opened_fd===null,'拒否後に読出し結果が残っています。');
 }
 return r;
}
const initial=()=>({id:'granted',prediction:null,mode:'normal',shown:false,answer:false,error:''});
function change(s,action,value){const n={...s,shown:false,answer:false,error:''};
 if(action==='case'){requireThat(ids.includes(value),'unknown case');return {...initial(),id:value};}
 if(action==='prediction'){requireThat(Object.values(expected).some(x=>x[0]===value),'unknown prediction');n.prediction=value;}
 else if(action==='mode'){requireThat(['normal','missing','altered','old'].includes(value),'unknown mode');n.mode=value;}
 else if(action==='reset')return {...initial(),id:s.id};
 else throw Error('unknown action');return n;
}
function read(s,data){if(!s.prediction)return {...s,shown:false,answer:false,error:'読めない理由、または読める結果を予想してください。'};
 try{let copy=data;if(s.mode!=='normal'){copy=JSON.parse(JSON.stringify(data));if(s.mode==='missing')delete copy.records[s.id];else if(s.mode==='altered')copy.records[s.id].outcome.prestat_errno=999;else copy.records[s.id]=copy.records[s.id==='granted'?'missing-file':'granted'];}validate(copy,s.id);return {...s,shown:true,answer:false,error:''};}
 catch(e){return {...s,shown:false,answer:false,error:'結果を表示しません：'+e.message};}}
const api={ids,expected,initial,change,read,validate};if(typeof module!=='undefined'&&module.exports)module.exports=api;else global.AtlasWasiState=api;
})(typeof window==='undefined'?globalThis:window);

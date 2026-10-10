(function(root){
'use strict';
const IDS=['reject-batch','quarantine-row','retain'];
const E=[{a:[],q:[],r:[1,2,3,4,5,6],m:[],s:null,n:0,k:0,x:0,f:null,status:'rejected'},{a:[1,2,4,5,6],q:[3],r:[],m:[1,2,4,6],s:200,n:4,k:3,x:1,f:{numerator:1,denominator:4},status:'accepted_with_quarantine'},{a:[1,2,3,4,5,6],q:[],r:[],m:[1,2,3,4,6],s:280,n:5,k:4,x:1,f:{numerator:1,denominator:5},status:'accepted'}];
const eq=(a,b)=>JSON.stringify(a)===JSON.stringify(b);
function validateFixture(x){
 const expected={schema:1,customers:[[10,'north'],[20,'south']],orders:[[1,10,100],[2,10,100],[3,999,80],[4,null,null],[5,20,50],[6,20,0]],lines:[[101,1],[102,1],[201,2],[301,3],[401,4],[601,6]],policies:IDS,null_customer_policy:'allow',metric:'accepted orders with at least one line; sum known amounts; report missing denominator'};
 if(!x||!eq(Object.keys(x).sort(),Object.keys(expected).sort()))throw Error('表示用入力が不足しています。');
 for(const [k,v] of Object.entries(expected))if(!eq(x[k],v))throw Error('表示用入力が固定条件と一致しません：'+k);
 return x;
}
function validate(record,id){
 if(!record||record.policy!==id)throw Error('別の方針、または欠落した記録です。');
 const e=E[IDS.indexOf(id)];if(!e)throw Error('未知の方針です。');
 const checks={accepted_ids:e.a,quarantined_ids:e.q,rejected_ids:e.r,metric_ids:e.m,sum_amount:e.s,input_rows:e.n,known_rows:e.k,missing_rows:e.x,missing_fraction:e.f,batch_status:e.status,candidate_ids:[1,2,3,4,6],candidate_coverage:{numerator:e.n,denominator:5},classification_rows:[[1,'known',2],[2,'known',1],[3,'unknown',1],[4,'null_key',1],[5,'known',0],[6,'known',1]],unknown_ids:[3],null_key_ids:[4],accepted_but_no_line_ids:e.a.length?[5]:[],foreign_keys_readback:1,database:':memory:',publish_performed:false};
 for(const [k,v] of Object.entries(checks))if(!eq(record[k],v))throw Error('保存記録が固定条件と一致しません：'+k);
 const decisions=[1,2,3,4,5,6].map(i=>[i,e.a.includes(i)?'accepted':e.q.includes(i)?'quarantined':'rejected',e.m.includes(i)?1:0]);
 if(!eq(record.decisions,decisions)||!eq(record.quarantine_records,e.q.map(i=>[i,'unknown_customer_key']))||!eq(record.rejection_records,e.r.map(i=>[i,'batch_rejected_unknown_key'])))throw Error('行の振分け記録が一致しません。');
 return record;
}
function validateProbes(probes){
 if(!Array.isArray(probes)||probes.length!==2)throw Error('外部キー比較の記録が不足しています。');
 probes.forEach((p,on)=>{
  const after=on?[[1],[1,2],[1,2],[1,2,4],[1,2,4,5],[1,2,4,5,6]]:[[1],[1,2],[1,2,3],[1,2,3,4],[1,2,3,4,5],[1,2,3,4,5,6]];
  const outcomes=[1,2,3,4,5,6].map(i=>on&&i===3?'foreign_key_constraint':'inserted');
  if(p.foreign_keys!==on||p.pragma_in_transaction!==false||p.isolation_level!==null||!eq(p.saved_ids,after[5])||!eq(p.ids_after_each,after)||!eq(p.outcomes,outcomes)||!eq(p.violations,on?[]:[['fk_orders',3,'customers',0]])||p.quarantine_rows_created!==0||!eq(p.rowid_order_id_pairs,after[5].map(i=>[i,i]))||p.events.length!==6)throw Error('外部キーの保存値が一致しません。');
  p.events.forEach((v,i)=>{if(v.order_id!==i+1||!eq(v.customer_id,[10,10,999,null,20,20][i])||v.outcome!==outcomes[i]||!eq(v.saved_ids,after[i])||v.in_transaction_before!==false||v.in_transaction_after!==false)throw Error('INSERTの保存値が一致しません。');if(outcomes[i]==='inserted'?v.error!==null:(!v.error||v.error.type!=='IntegrityError'||!v.error.message.includes('FOREIGN KEY constraint failed')))throw Error('制約応答が一致しません。');});
 });
 return probes;
}
function initial(){return {policy:'retain',prediction:'',recordMode:'normal',shown:null,answer:false,error:'',fk:1};}
function clear(s){return {...s,shown:null,answer:false,error:''};}
function transition(s,action,data){
 let z=clear(s);
 if(action.type==='reset')return initial();
 if(action.type==='policy'){if(!IDS.includes(action.value))return {...z,error:'未知の方針です。'};return {...z,policy:action.value,prediction:''};}
 if(action.type==='prediction')return {...z,prediction:action.value};
 if(action.type==='record')return {...z,recordMode:action.value};
 if(action.type==='fk')return {...s,fk:action.value===0?0:1};
 if(action.type==='answer')return {...s,answer:!!s.shown};
 if(action.type==='load'){
  if(!['undefined','1/4','1/5'].includes(s.prediction))return {...z,error:'金額欠損割合を予想してから比較してください。'};
  try{
   if(!data||!Array.isArray(data.policies)||!data.observed_at_utc||!data.runtime)throw Error('保存データがありません。');
   validateFixture(data.fixture);
   let r=data.policies.find(p=>p.policy===s.policy);r=r?JSON.parse(JSON.stringify(r)):null;
   if(s.recordMode==='missing')r=null;else if(s.recordMode==='altered'&&r)r.sum_amount=999;else if(s.recordMode==='old'&&r)r.policy=IDS[(IDS.indexOf(s.policy)+1)%3];else if(s.recordMode!=='normal')throw Error('記録条件が不正です。');
   validate(r,s.policy);validateProbes(data.foreign_key_probes);return {...z,shown:r};
  }catch(e){return {...z,error:e.message};}
 }
 return z;
}
root.AtlasDimensionState={IDS,initial,transition,validate,validateProbes,validateFixture};
})(typeof window==='undefined'?globalThis:window);

(function(global){'use strict';
const ids=['raw-tfidf','bm25-b0','bm25-bhalf','bm25-b1'];
const expected={
 'raw-tfidf':{winner:'d1',coeff:[2,1,0,0],num:[2,1,null,null],den:[1,1,null,null],b:null,order:['d1','d2'],ties:[]},
 'bm25-b0':{winner:'d1',coeff:[4/3,1,0,0],num:[4,2,null,null],den:[3,2,null,null],b:0,order:['d1','d2'],ties:[]},
 'bm25-bhalf':{winner:'tie',coeff:[8/7,8/7,0,0],num:[4,2,null,null],den:[3.5,1.75,null,null],b:.5,order:['d1','d2'],ties:[['d1','d2']]},
 'bm25-b1':{winner:'d2',coeff:[1,4/3,0,0],num:[4,2,null,null],den:[4,1.5,null,null],b:1,order:['d2','d1'],ties:[]}};
function need(ok,message){if(!ok)throw Error(message);}
const same=(a,b)=>JSON.stringify(a)===JSON.stringify(b),near=(a,b)=>typeof a==='number'&&Number.isFinite(a)&&Math.abs(a-b)<=1e-12;
function validate(data,id){
 need(data&&data.schema===1&&/^calculation-\d+T\d+Z$/.test(data.run_id),'保存した計算結果がありません。');
 need(data.fixture_sha256==='52864641eb925094abfd2d51662e123569c037994bf014ba88b79353d56956c8','入力の対応が一致しません。');
 const r=data.cases?.find(x=>x.mode_id===id),e=expected[id];need(r&&e,'選んだ方式の記録ではありません。');
 need(r.N===4&&r.df===2&&r.total_tokens===16&&r.avgdl===4&&r.query==='alpha'&&r.idf_variant==='ln(N/df)'&&near(r.idf,Math.LN2),'文書数・IDFの契約が一致しません。');
 need(r.k1===(id==='raw-tfidf'?null:1)&&r.b===e.b,'方式の設定が一致しません。');need(same(r.match_ids,['d1','d2'])&&same(r.nonmatch_ids,['d3','d4'])&&same(r.matched_order,e.order)&&same(r.tie_groups,e.ties),'候補・表示順・同点が一致しません。');
 need(Array.isArray(r.rows)&&r.rows.length===4,'文書の記録が欠けています。');
 r.rows.forEach((row,i)=>{need(row.id===['d1','d2','d3','d4'][i]&&row.length===[8,2,0,6][i]&&row.term_frequency===[2,1,0,0][i]&&same(row.positions,[[0,1],[0],[],[]][i]),'文書長・回数が一致しません。');need(row.matched===(i<2)&&row.nonmatch_short_circuit===(i>=2),'非一致の扱いが一致しません。');need(near(row.coefficient,e.coeff[i])&&near(row.score,e.coeff[i]*Math.LN2)&&row.numerator===e.num[i]&&row.denominator===e.den[i],'保存された得点が確認済みの計算と一致しません。');need(row.rank===(i<2?e.order.indexOf(row.id)+1:null),'表示順が一致しません。');});
 return r;
}
const initial=()=>({id:'raw-tfidf',prediction:null,recordMode:'normal',shown:false,answer:false,error:''});
function change(s,kind,value){const n={...s,shown:false,answer:false,error:''};if(kind==='mode'){need(ids.includes(value),'unknown mode');return {...initial(),id:value};}if(kind==='prediction'){need(['d1','tie','d2'].includes(value),'unknown prediction');n.prediction=value;}else if(kind==='record'){need(['normal','missing','altered','old'].includes(value),'unknown record mode');n.recordMode=value;}else if(kind==='reset')return {...initial(),id:s.id};else throw Error('unknown action');return n;}
function read(s,data){if(!s.prediction)return {...s,shown:false,answer:false,error:'どちらの得点が高いか、または同点かを予想してください。'};
 try{let copy=data;if(s.recordMode!=='normal'){copy=JSON.parse(JSON.stringify(data));const at=copy.cases.findIndex(x=>x.mode_id===s.id);if(s.recordMode==='missing')copy.cases.splice(at,1);else if(s.recordMode==='altered')copy.cases[at].rows[0].coefficient+=1;else copy.cases[at]=copy.cases.find(x=>x.mode_id!==s.id);}validate(copy,s.id);return {...s,shown:true,answer:false,error:''};}
 catch(e){return {...s,shown:false,answer:false,error:'結果を表示しません：'+e.message};}}
const api={ids,expected,initial,change,read,validate};if(typeof module!=='undefined'&&module.exports)module.exports=api;else global.AtlasSearchState=api;
})(typeof window==='undefined'?globalThis:window);

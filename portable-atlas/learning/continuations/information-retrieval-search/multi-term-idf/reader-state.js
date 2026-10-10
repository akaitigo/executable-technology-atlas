(function(global){'use strict';
const ids=['alpha-only','beta-only','two-terms','reversed-terms','repeated-terms','unknown-term'];
const queries={'alpha-only':'alpha','beta-only':'beta','two-terms':'alpha beta','reversed-terms':'beta alpha','repeated-terms':'alpha alpha beta','unknown-term':'alpha gamma'};
const predictions={'alpha-only':'d1-only','beta-only':'d2-only','two-terms':'d2-higher','reversed-terms':'d2-higher','repeated-terms':'d2-higher','unknown-term':'refused'};
const same=(a,b)=>JSON.stringify(a)===JSON.stringify(b),near=(a,b)=>typeof a==='number'&&Number.isFinite(a)&&Math.abs(a-b)<=1e-12;
function need(ok,message){if(!ok)throw Error(message);}
function validate(data,id){
 need(data&&data.schema===1&&/^calculation-\d+T\d+Z$/.test(data.run_id),'保存した計算結果をまだ読み込めません。');
 need(data.fixture_sha256==='29c0d97004546fec30db7af9137114ea94c38aac21c84679b5b186392435ce3b','固定入力の対応が一致しません。');
 const r=data.cases?.find(x=>x.request_id===id);need(r&&ids.includes(id)&&r.query===queries[id],'選んだ入力の記録ではありません。');
 if(id==='unknown-term'){need(r.status==='expected_query_refusal'&&r.code==='unknown_query_term'&&same(r.missing_terms,['gamma'])&&r.rows===null&&r.scores_returned===false,'未知語の拒否記録が一致しません。');return r;}
 const terms=id==='alpha-only'?['alpha']:id==='beta-only'?['beta']:['alpha','beta'],df={alpha:3,beta:2},idf={alpha:Math.log(4/3),beta:Math.log(2)},positions={d1:{alpha:[0],beta:[]},d2:{alpha:[],beta:[0]},d3:{alpha:[0],beta:[1]},d4:{alpha:[0],beta:[]}};
 const orders=id==='alpha-only'?{weighted:['d1','d3','d4'],unit:['d1','d3','d4'],wt:[['d1','d3','d4']],ut:[['d1','d3','d4']]}:id==='beta-only'?{weighted:['d2','d3'],unit:['d2','d3'],wt:[['d2','d3']],ut:[['d2','d3']]}:{weighted:['d3','d2','d1','d4'],unit:['d3','d1','d2','d4'],wt:[['d1','d4']],ut:[['d1','d2','d4']]};
 const matches=id==='alpha-only'?['d1','d3','d4']:id==='beta-only'?['d2','d3']:['d1','d2','d3','d4'];
 need(r.status==='calculated'&&same(r.query_tokens,queries[id].split(' '))&&same(r.canonical_terms,terms)&&r.removed_duplicates===(id==='repeated-terms'?1:0),'入力の正規化が一致しません。');
 need(r.N===4&&r.avgdl===4&&r.total_tokens===16&&r.k1===1&&r.b===0&&r.idf_variant==='ln(N/df)','文書数・式の設定が一致しません。');
 need(same(Object.keys(r.df).sort(),terms)&&same(Object.keys(r.idf).sort(),terms),'語の記録が欠けています。');for(const t of terms)need(r.df[t]===df[t]&&near(r.idf[t],idf[t]),'語ごとの文書頻度・IDFが一致しません。');
 need(same(r.matches,matches)&&same(r.weighted_order,orders.weighted)&&same(r.unit_order,orders.unit)&&same(r.weighted_ties,orders.wt)&&same(r.unit_ties,orders.ut),'候補・表示順・同点が一致しません。');need(Array.isArray(r.rows)&&r.rows.length===4,'文書の記録が欠けています。');
 r.rows.forEach((row,i)=>{need(row.id===['d1','d2','d3','d4'][i]&&row.length===4&&same(row.contributions.map(c=>c.term),terms),'文書・語の対応が一致しません。');let total=0,unit=0;for(const c of row.contributions){const at=positions[row.id][c.term],hit=at.length>0;need(same(c.positions,at)&&c.tf===at.length&&c.df===df[c.term]&&near(c.idf,idf[c.term])&&c.tf_factor===Number(hit)&&c.unit_contribution===Number(hit)&&c.nonmatch_short_circuit===!hit&&near(c.weighted_contribution,hit?idf[c.term]:0),'語ごとの寄与が一致しません。');if(hit){total+=idf[c.term];unit++;}}need(row.matched===matches.includes(row.id)&&near(row.weighted_score,total)&&near(row.unit_score,unit),'合計または候補が一致しません。');for(const kind of ['weighted','unit'])need(row[kind+'_rank']===(row.matched?orders[kind].indexOf(row.id)+1:null),'表示順が一致しません。');});return r;
}
const initial=()=>({id:'two-terms',prediction:null,recordMode:'normal',shown:false,answer:false,error:''});
function change(s,kind,value){const n={...s,shown:false,answer:false,error:''};if(kind==='case'){need(ids.includes(value),'unknown case');return {...initial(),id:value};}if(kind==='prediction'){need(['d1-only','d2-only','d2-higher','tie','refused'].includes(value),'unknown prediction');n.prediction=value;}else if(kind==='record'){need(['normal','missing','altered','old'].includes(value),'unknown record');n.recordMode=value;}else if(kind==='reset')return {...initial(),id:s.id};else throw Error('unknown change');return n;}
function read(s,data){if(!s.prediction)return {...s,shown:false,answer:false,error:'d1とd2の扱いを予想してから開いてください。'};try{let d=data;if(s.recordMode!=='normal'){d=JSON.parse(JSON.stringify(data));const i=d.cases.findIndex(c=>c.request_id===s.id);if(s.recordMode==='missing')d.cases.splice(i,1);else if(s.recordMode==='old')d.cases[i]=d.cases.find(c=>c.request_id!==s.id);else if(s.id==='unknown-term')d.cases[i].rows=[];else d.cases[i].rows[0].weighted_score+=1;}validate(d,s.id);return {...s,shown:true,answer:false,error:''};}catch(e){return {...s,shown:false,answer:false,error:'保存記録を表示しません：'+e.message};}}
const api={ids,queries,predictions,initial,change,read,validate};if(typeof module!=='undefined'&&module.exports)module.exports=api;else global.AtlasMultiState=api;
})(typeof window==='undefined'?globalThis:window);

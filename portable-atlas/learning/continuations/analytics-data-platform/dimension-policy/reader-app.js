/* Atlas: render only saved SQLite records; no database, server or fetch. */
(function(){'use strict';const D=window.ATLAS_DIMENSION_DATA,S=window.AtlasDimensionState,$=id=>document.getElementById(id),names={'reject-batch':'全件拒否','quarantine-row':'未知の行だけ隔離','retain':'全行を保持'},states={known:'既知の顧客',unknown:'存在しない顧客',null_key:'NULL（未指定）'},decisions={accepted:'受入',quarantined:'隔離',rejected:'拒否'};let s=S.initial();
const txt=v=>v===null?'NULL':String(v),list=a=>a.length?a.join(', '):'なし';
function dispatch(a){s=S.transition(s,a,D);render();}
S.IDS.forEach(id=>{const b=document.createElement('button');b.textContent=names[id];b.dataset.policy=id;b.onclick=()=>dispatch({type:'policy',value:id});$('policies').append(b);});
document.querySelectorAll('input[name=prediction]').forEach(i=>i.onchange=()=>dispatch({type:'prediction',value:i.value}));$('load').onclick=()=>dispatch({type:'load'});$('reset').onclick=()=>dispatch({type:'reset'});$('answer-button').onclick=()=>dispatch({type:'answer'});$('record-mode').onchange=e=>dispatch({type:'record',value:e.target.value});$('fk-off').onclick=()=>dispatch({type:'fk',value:0});$('fk-on').onclick=()=>dispatch({type:'fk',value:1});
function cells(parent,values){const tr=document.createElement('tr');values.forEach(v=>{const td=document.createElement('td');td.textContent=v;tr.append(td);});parent.append(tr);}
function card(parent,label,value){const div=document.createElement('div'),span=document.createElement('span'),strong=document.createElement('strong');span.textContent=label;strong.textContent=value;div.append(span,strong);parent.append(div);}
function render(){
 ['flow','metrics','rows','fk-rows','fk-summary','raw','answer','diagnostic'].forEach(id=>$(id).textContent='');$('details').open=false;$('error').textContent=s.error;$('answer-button').disabled=!s.shown;$('record-mode').value=s.recordMode;
 document.querySelectorAll('[data-policy]').forEach(b=>b.setAttribute('aria-pressed',String(b.dataset.policy===s.policy)));document.querySelectorAll('input[name=prediction]').forEach(i=>i.checked=i.value===s.prediction);$('fk-off').setAttribute('aria-pressed',String(s.fk===0));$('fk-on').setAttribute('aria-pressed',String(s.fk===1));
 $('record-time').textContent=D?`保存した計測：${D.observed_at_utc} / SQLite ${D.runtime.sqlite}。画面でSQLを再実行しません。`:'保存した計測は未接続です。';
 if(!s.shown)return;const r=s.shown;
 card($('flow'),'受け入れた注文',list(r.accepted_ids));card($('flow'),'隔離した注文',list(r.quarantined_ids));card($('flow'),'拒否した注文',list(r.rejected_ids));
 const fraction=r.missing_fraction?`${r.missing_fraction.numerator}/${r.missing_fraction.denominator}`:'未定義（分母0）';card($('metrics'),'既知金額の合計',txt(r.sum_amount));card($('metrics'),'対象 / 金額あり / 金額欠損',`${r.input_rows} / ${r.known_rows} / ${r.missing_rows}`);card($('metrics'),'金額欠損割合',fraction);card($('metrics'),'集計対象の注文',list(r.metric_ids));card($('metrics'),'元の候補5件に対する採用',`${r.candidate_coverage.numerator}/${r.candidate_coverage.denominator}`);card($('metrics'),'受入済みだが明細なし',list(r.accepted_but_no_line_ids));
 D.fixture.orders.forEach(o=>{const c=r.classification_rows.find(v=>v[0]===o[0]),d=r.decisions.find(v=>v[0]===o[0]);cells($('rows'),[o[0],txt(o[1]),states[c[1]],txt(o[2]),c[2],decisions[d[1]],d[2]?'対象':'対象外']);});
 $('diagnostic').textContent=r.batch_status==='rejected'?'全件拒否：合計NULL・対象0は受入なしの診断です。業務値0や公開成功ではありません。':'金額欠損の1件は注文4です。顧客キーの未知分類と、金額欠損を混ぜないでください。';
 const p=D.foreign_key_probes[s.fk];p.events.forEach(e=>cells($('fk-rows'),[e.order_id,txt(e.customer_id),e.outcome==='inserted'?'挿入成功':'外部キー制約で拒否',list(e.saved_ids)]));$('fk-summary').textContent=`PRAGMA読戻し ${p.foreign_keys}、設定時はトランザクション外。違反検査：${p.violations.length?'fk_orders / rowid 3 / customers / 制約0':'違反なし'}。自動の隔離行 ${p.quarantine_rows_created}件。`;
 $('raw').textContent=JSON.stringify({policy:r,foreign_key_probe:p},null,2);
 if(s.answer){const actual=r.missing_fraction?`${r.missing_fraction.numerator}/${r.missing_fraction.denominator}`:'undefined';const nullNote=r.batch_status==='rejected'?'NULLキー自体は許可する規約ですが、バッチ全体の拒否により注文4も受入なしです。':'NULLキーの注文4は受け入れられ、金額欠損の1件として残ります。';$('answer').textContent=(s.prediction===actual?'予想と一致しました。':'予想とは異なりました。')+` ${names[s.policy]}では金額欠損割合は${fraction}。${nullNote}`;}
}
render();})();

'use strict';
// Replays reviewed saved observations. No request is sent and no DB is opened.
const data=window.WAL_OBSERVATION,$=id=>document.getElementById(id),pretty=x=>JSON.stringify(x,null,2);
const PUBLIC_VALUE_SHA='63850f96b506f7d9c133efd5681f1bfd02174cc3fefb6adae7d7345459185aa0';
const IDS=['stale','fresh','rollback','busy','stale-small','fresh-high','busy-zero','rollback-high','bool','schedule','same','path','malformed'];
let revision=0;
for(const row of data.rows){const o=document.createElement('option');o.value=row.id;o.textContent=row.label;$('scenario').append(o);}
$('scenario').value=IDS[0];$('input-json').value=data.rows[0].input_json;$('input-json').readOnly=true;
$('initial-run').textContent=data.run_id;$('initial-raw').href='observation-data.js';
function clear(message){revision++;$('results').hidden=true;$('answer').hidden=true;$('answer').open=false;$('trace-disclosure').open=false;$('physical-disclosure').open=false;for(const id of ['classification','normal','attempt','state','physical','trace','run','answer-body'])$(id).textContent='';$('raw').removeAttribute('href');$('prediction-result').textContent=message;}
function same(a,b){const normalize=v=>Array.isArray(v)?v.map(normalize):v&&typeof v==='object'?Object.fromEntries(Object.keys(v).sort().map(k=>[k,normalize(v[k])])):v;return JSON.stringify(normalize(a))===JSON.stringify(normalize(b));}
async function verify(){
 if(!data||!Array.isArray(data.rows)||data.rows.length!==IDS.length||data.rows.some((r,i)=>r.id!==IDS[i]))throw Error('固定13条件ではありません');
 const b=await crypto.subtle.digest('SHA-256',new TextEncoder().encode(JSON.stringify(data)));
 if([...new Uint8Array(b)].map(x=>x.toString(16).padStart(2,'0')).join('')!==PUBLIC_VALUE_SHA)throw Error('保存データのSHAが一致しません');
 for(const row of data.rows){const r=row.run.result;if(r.status==='observed'){if(row.run.exit!==0||!['stale','busy','success'].includes(r.summary.category)||!same(r.summary,row.expected))throw Error('保存観測と固定期待の不一致');}
 else if(r.status==='input_refusal'){if(row.run.exit!==2||!same(r,row.expected))throw Error('保存拒否と固定期待の不一致');}
 else throw Error('実行失敗を正常観測として再生できません');}
}
$('scenario').addEventListener('change',()=>{const row=data.rows.find(r=>r.id===$('scenario').value);$('input-json').value=row?.input_json??'';$('prediction').value='';clear('保存条件を変更しました。予想もresetしました。');});
$('prediction').addEventListener('change',()=>clear('予想を変更しました。保存結果を読み直してください。'));
$('input-json').addEventListener('input',()=>clear('固定入力と異なる編集値は再生しません。条件を選び直してください。'));
$('compare').addEventListener('click',async()=>{
 clear('保存した13条件のSHAと固定期待を照合しています。SQLや通信は実行しません。');const mine=revision,id=$('scenario').value,input=$('input-json').value,pred=$('prediction').value;
 try{
  if(!pred)throw Error('先に予想を選んでください');await verify();if(mine!==revision)return;
  const row=data.rows.find(x=>x.id===id);if(!row||row.input_json!==input)throw Error('保存条件にない入力です。新しい実験結果は生成しません');
  const r=row.run.result,s=r.summary,cat=r.status==='input_refusal'?'input':s.category;
  $('prediction-result').textContent=(pred===cat?'予想と一致。':'予想と不一致。')+' 保存結果: '+cat+'。新しいDB実行ではありません。';$('results').hidden=false;
  $('classification').textContent=r.status==='input_refusal'?`保存された入力拒否 ${r.code}、exit2。DB未作成。`:`過去のnative SQLite観測 ${s.upgrade_code} ${s.upgrade_name}。保存データの再生です。`;
  $('normal').textContent=s?pretty({recovery_before:s.recovery_before,final:s.final_row,recovery_done:s.recovery_done}):'SQL未実行';
  $('attempt').textContent=s?pretty({first:s.first_row,after_attempt:s.after_attempt_row,code:s.upgrade_code,name:s.upgrade_name}):'昇格判定なし';
  $('state').textContent=s?pretty({attempt:s.attempt_state,final:s.final_state,tmp_cleanup:r.temporary_cleanup,handles_closed:r.handles_closed}):'DB未作成';
  $('physical').textContent=s?pretty({engine:r.engine,db_header_hex:r.db_header_hex,wal:r.wal,closed_db_sha256:r.closed_db_sha256,saved_database:'saved-db/'+id+'.sqlite'}):'DB bytesなし';
  $('trace').textContent=s?pretty(r.trace):pretty(r);$('run').textContent=`保存run ${data.run_id} / 条件 ${row.id} / 当時のexit${row.run.exit}`;$('raw').href='observation-data.js';
  $('answer').hidden=false;$('answer-body').textContent=s?`固定期待と保存summaryの全項目が一致しました。schedule=${s.input.schedule}、reader最初=${s.first_row}、昇格code=${s.upgrade_code} ${s.upgrade_name}、直後row=${s.after_attempt_row}、rollback再開始=${s.recovery_done}、再読=${s.recovery_before}、最終row=${s.final_row}。timeout設定だけで773 BUSY_TIMEOUTとは呼びません。新環境の実SQLite動作を検証した結果ではありません。`:`固定期待の入力拒否 ${row.expected.code} と一致。期待された拒否と、読込み失敗やDB実行失敗を分けます。`;
 }catch(e){if(mine!==revision)return;clear('保存資料の読込み失敗。SQLの期待された拒否とは別です。 '+e.message);}
});

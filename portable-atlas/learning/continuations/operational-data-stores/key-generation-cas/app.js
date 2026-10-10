'use strict';
const data=window.CAS_OBSERVATION,$=id=>document.getElementById(id);
for(const r of data.rows){const o=document.createElement('option');o.value=r.id;o.textContent=r.status==='accepted-experiment'?`${r.lifetime==='same'?'同世代':'再作成'} / ${r.mode==='version'?'version-only':'世代+version'}`:`${r.status==='expected-refusal'?'入力拒否':'SQL失敗'} · ${r.label}`;$('scenario').append(o);}
$('run').textContent=`保存run: ${data.run_id} / SQLite ${data.sqlite_version} / Python ${data.environment.python} / 4比較・6入力拒否・1SQL error`;
$('raw').href=`observations/${data.run_id}/raw.json`;$('command').href=`observations/${data.run_id}/command.json`;
function dbLink(){$('db').href=`observations/${data.run_id}/${data.rows.find(r=>r.id===$('scenario').value).database_file}`;}
function reset(){$('prediction').value='';for(const id of ['results','refusal','sql-error'])$(id).hidden=true;$('answer').open=false;$('prediction-result').textContent='予想してから比較する。';dbLink();}
$('scenario').addEventListener('change',reset);dbLink();
$('compare').addEventListener('click',()=>{
 const r=data.rows.find(x=>x.id===$('scenario').value),normal=r.status==='accepted-experiment',refused=r.status==='expected-refusal',error=r.status==='expected-sql-error';
 $('results').hidden=!normal;$('refusal').hidden=!refused;$('sql-error').hidden=!error;
 const actual=refused?'refused':error?'sql-error':r.old_request_rowcount===0?'stale-rejected':'stale-accepted',pred=$('prediction').value;
 $('prediction-result').textContent=!pred?'予想未選択。予想を選んで結果と照合する。':pred===actual?'予想と一致。rowcountとstateを照合しよう。':'予想と不一致。更新対象・入力拒否・SQL失敗を読み直そう。';
 if(normal){$('outcome').textContent=`旧要求 ${r.old_request_rowcount}行 / 新要求 ${r.fresh_request_rowcount}行 / 最終 ${r.final.generation}/v${r.final.version}/value${r.final.value}`;$('steps').replaceChildren();for(const t of r.steps){const tr=document.createElement('tr');for(const v of [t.label,t.rowcount,t.state?.generation??'absent',t.state?.version??'—',t.state?.value??'—']){const td=document.createElement('td');td.textContent=v;tr.append(td);}$('steps').append(tr);}$('trace').textContent=JSON.stringify({steps:r.steps,sql_trace:r.sql_trace},null,2);}
 if(refused){$('reason').textContent=`${r.reason} / update_sql_issued=false`;$('refused-input').textContent=JSON.stringify(r.request,null,2);}
 if(error)$('error').textContent=`${r.error.type}: ${r.error.message} / attempted: ${r.attempted_sql}`;
});

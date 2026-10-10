'use strict';
const data=window.BYTES_OBSERVATION, $=id=>document.getElementById(id);
for(const row of data.rows){const o=document.createElement('option');o.value=row.id;o.textContent=`${row.status==='accepted'?'比較':'拒否'} · ${row.label}`;$('scenario').append(o);}
$('run').textContent=`保存run: ${data.run_id} / Python ${data.environment.python} / ${data.environment.os} ${data.environment.machine} / 6比較 + 8 expected refusal`;
$('raw').href=`observations/${data.run_id}/raw.json`;$('command').href=`observations/${data.run_id}/command.json`;
function reset(){$('prediction').value='';$('results').hidden=true;$('refusal').hidden=true;$('answer').open=false;$('prediction-result').textContent='予想してから比較する。';}
$('scenario').addEventListener('change',reset);
$('compare').addEventListener('click',()=>{
 const r=data.rows.find(x=>x.id===$('scenario').value),accepted=r.status==='accepted';
 $('results').hidden=!accepted;$('refusal').hidden=accepted;
 const actual=!accepted?'refused':r.mode==='context'?'context':r.normal.tags_equal?'same':'different',pred=$('prediction').value;
 $('prediction-result').textContent=!pred?'予想未選択。予想を選んで結果と照合する。':pred===actual?'予想と一致。表示されたbyte/tagと照合しよう。':'予想と不一致。正常/故障版または入力拒否を読み直そう。';
 if(accepted){$('outcome').textContent=r.mode==='context'?`正常版: 元tagを拒否 / ${r.omitted}を落とした故障版: 元tagが通る`:r.normal.tags_equal?'独自canonical: 同じbytes/tagで通る':'raw: bytes/tagが異なり元tagを拒否';$('trace').textContent=JSON.stringify({normal:r.normal,...(r.faulty?{faulty:r.faulty}: {})},null,2);}
 else{$('reason').textContent=`${r.reason} / tags_created=false`;$('refused-input').textContent=r.input;}
});

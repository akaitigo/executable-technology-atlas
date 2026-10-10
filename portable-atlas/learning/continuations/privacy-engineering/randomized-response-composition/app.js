'use strict';
const data=window.RR_OBSERVATION,$=id=>document.getElementById(id);
for(const r of data.rows){const o=document.createElement('option');o.value=r.id;o.textContent=r.status==='expected-refusal'?`拒否 · ${r.id.replace('refuse-','')}`:r.id==='single'?'1回答 · bound3':'独立2回答 · bound9';$('scenario').append(o);}
$('run').textContent=`保存run: ${data.run_id} / Python ${data.environment.python} / 2計算 + 5入力拒否 / random samples=0`;
$('raw').href=`observations/${data.run_id}/raw.json`;$('command').href=`observations/${data.run_id}/command.json`;
function clear(message){$('results').hidden=true;$('refusal').hidden=true;$('answer').open=false;$('trace-disclosure').open=false;$('prediction-result').textContent=message;}
$('scenario').addEventListener('change',()=>{$('prediction').value='';clear('予想してから比較する。');});
$('prediction').addEventListener('change',()=>clear('予想を変更しました。比較するで照合してください。'));
$('compare').addEventListener('click',()=>{
 const r=data.rows.find(x=>x.id===$('scenario').value),refused=r.status==='expected-refusal';$('results').hidden=refused;$('refusal').hidden=!refused;
 const actual=refused?'refused':r.id==='single'?'ratio3':'ratio9',pred=$('prediction').value;
 $('prediction-result').textContent=!pred?'予想未選択。予想を選んで結果と照合する。':pred===actual?'予想と一致。分布と両方向比を照合しよう。':'予想と不一致。joint eventと入力契約を読み直そう。';
 if(refused){$('reason').textContent=`${r.reason} / distribution_created=false`;$('refused-input').textContent=JSON.stringify(r.request,null,2);return;}
 $('summary').textContent=`入力ごと${r.path_count_per_input}経路、質量${r.path_mass}、最大比${r.max_ratio} / 非空event ${r.nonempty_events.length}件（両方向）`;
 $('distribution').replaceChildren();for(const t of r.singleton_ratios){const tr=document.createElement('tr');for(const v of [t.outputs[0],t.p0,t.p1,t.ratio_0_over_1,t.ratio_1_over_0]){const td=document.createElement('td');td.textContent=v;tr.append(td);}$('distribution').append(tr);}
 $('normal').textContent=`正常: bound ${r.normal_bound}内=${r.normal_bound_holds} / epsilon=${r.epsilon_symbolic}, delta=${r.delta}`;
 $('faulty').textContent=`故障版: marginal最大比${r.faulty_marginal_max_ratio}だけでbound3内とclaim=${r.faulty_marginal_only_claim_holds} / jointで実際にbound3内=${r.reused_bound_actually_holds}`;
 $('violations').textContent=`bound3を破るevent: ${r.events_violating_reused_bound.length?r.events_violating_reused_bound.map(t=>'{'+t.outputs.join(',')+'}').join(' / '):'なし'}`;
 $('trace').textContent=JSON.stringify({paths:r.paths,nonempty_events:r.nonempty_events},null,2);
});

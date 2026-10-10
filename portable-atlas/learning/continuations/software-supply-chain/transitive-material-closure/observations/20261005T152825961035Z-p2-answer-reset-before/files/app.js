'use strict';
const $=id=>document.getElementById(id),data=window.MATERIAL_OBSERVATION;
const labels={baseline:'root→A→B 全material一致','B-changed':'B bytes変更、直接名Aは同じ','B-undeclared':'Bを使用、申告だけ欠落','changed-undeclared':'B変更と申告欠落','B-unreachable':'A→B edge欠落','unknown-node':'B→未知Xを拒否',cycle:'B→root cycleを拒否','read-failure':'B material読取失敗'};
for(const row of data.rows){const o=document.createElement('option');o.value=row.id;o.textContent=labels[row.id];$('scenario').appendChild(o);}
$('run').textContent=`保存run: ${data.run_id} / Python ${data.environment.python} / 5生成条件・2build前拒否・1読取失敗`;
$('raw').href=`observations/${data.run_id}/raw.json`;$('command').href=`observations/${data.run_id}/command.json`;
function clear(message){$('results').hidden=true;$('answer').hidden=true;$('answer').open=false;$('trace-disclosure').open=false;$('prediction-result').textContent=message;}
$('scenario').addEventListener('change',()=>{$('prediction').value='';clear('予想してから比較する。');});
$('prediction').addEventListener('change',()=>clear('予想を変更しました。比較するで照合してください。'));
const explain={agree:'全materialの実bytes・申告・固定期待値が一致。今回のunsigned fixture一致であり、SLSA適合や真正性の証明ではない。',changed:'B digestとartifactが変わる。直接名Aは同じでも正常consumerは旧期待Bとの差をdenyする。',undeclared:'artifact生成でBを読んだのに申告が欠ける。正常consumerは集合不一致をrefuse、直接名故障はallow。',closure:'申告と実到達集合は一致しても固定期待集合からBが消えている。正常consumerはexpected-closureをrefuse。',refused:'未知node/cycleをbuild前に拒否。material読取とartifact生成は実行せず、両版refuse。',error:'material読取失敗。partial attemptは原票へ保存するがartifactと正常答えを表示しない。'};
$('compare').addEventListener('click',()=>{const r=data.rows.find(x=>x.id===$('scenario').value),category=r.status==='execution-error'?'error':r.status==='expected-refusal'?'refused':r.normal.reason==='declared-material-set'?'undeclared':r.normal.reason==='expected-closure'?'closure':r.normal.decision==='deny'?'changed':'agree';
 $('prediction-result').textContent=$('prediction').value===''?'予想未選択。選んで結果と照合する。':$('prediction').value===category?'予想と一致。集合・Bdigest・consumer許可を照合しよう。':'予想と不一致。直接名と推移materialを読み直そう。';
 $('build-status').textContent=`生成観測: ${r.status} / artifact: ${r.artifact?'生成済み':'なし'}`;$('direct').textContent=`直接名: ${r.direct_names?JSON.stringify(r.direct_names):'未確定'}`;$('reachable').textContent=`実到達集合: ${r.reachable?JSON.stringify(r.reachable):'未確定'}`;$('declared').textContent=`申告集合: ${r.declared?JSON.stringify(Object.keys(r.declared).sort()):'未読取'}`;
 $('B-digest').textContent=r.materials.B?`B実digest: ${r.materials.B.sha256} / bytes: ${r.materials.B.size}`:'B実digest: 未読取';
 $('artifact').textContent=r.artifact?`artifact SHA256: ${r.artifact.sha256}\nbytes: ${r.artifact.size}\n実生成bytes:\n${r.artifact.ascii}`:'artifactなし（build前拒否 / 読取失敗）';$('artifact-file').hidden=!r.artifact;if(r.artifact)$('artifact-file').href=`observations/${data.run_id}/${r.id}/artifact.bin`;else $('artifact-file').removeAttribute('href');
 $('normal-result').textContent=JSON.stringify(r.normal,null,2);$('faulty-result').textContent=JSON.stringify(r.faulty,null,2);$('classification').textContent=explain[category];$('trace').textContent=JSON.stringify({materials:r.materials,declared:r.declared,trace:r.trace},null,2);$('results').hidden=false;$('answer').hidden=category==='error';$('answer').open=false;$('trace-disclosure').open=false;$('answer-text').textContent=explain[category];
});

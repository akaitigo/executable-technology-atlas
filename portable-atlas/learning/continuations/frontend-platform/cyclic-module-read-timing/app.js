'use strict';
const data=window.CYCLE_OBSERVATION,$=id=>document.getElementById(id),pretty=x=>JSON.stringify(x,null,2);
for(const r of data.rows){const option=document.createElement('option');option.value=r.id;option.textContent=r.label;$('scenario').append(option);}
const fields=['classification','graph','outcome','immediate','delayed','events','stdout','stderr','process','run','answer-body'],links=['raw','command','fixture-a','fixture-b'];
function clear(message){$('results').hidden=true;$('answer').hidden=true;$('answer').open=false;$('trace-disclosure').open=false;for(const id of fields)$(id).textContent='';for(const id of links)$(id).removeAttribute('href');$('prediction-result').textContent=message;}
$('scenario').addEventListener('change',()=>{$('prediction').value='';$('predicted-value').value='';clear('ケースを変更しました。予想条件をresetしました。');});
$('prediction').addEventListener('change',()=>clear('予想を変更しました。比較するで照合してください。'));
$('predicted-value').addEventListener('input',()=>clear('予想値を変更しました。比較するで照合してください。'));
const result=r=>({exit:r.exit,exception_class:r.exception_class,final_value:r.final_value});
const reasons={immediate:'B:before-readの次はdriver:failed。実ReferenceError、final値なし。A/entry本文のlogには到達していません。',delayed:'Bは関数を用意するだけ。A:init1の後、entryがreadを呼ぶと1。循環が存在しても、この読取は初期化後です。','early-call':'関数に包んでも、B評価中に呼ぶと未初期化Aのvalueを読みReferenceError。callを初期化後へ遅らせる必要があります。',acyclic:'A:init1がB:before-readより先。循環なしの即時readは1で成功しました。','live-update':'entryからread1→A:update2→read2。importはlive bindingを読み、最初にコピーしたsnapshotだけは1を保持しました。'};
$('compare').addEventListener('click',()=>{
 const pred=$('prediction').value,text=$('predicted-value').value,r=data.rows.find(r=>r.id===$('scenario').value);
 if(!/^(?:[0-9])?$/.test(text)){clear('予想入力を拒否。空欄または0〜9の1桁にしてください。Nodeは再実行していません。');return;}
 const cat=r.exception_class==='ReferenceError'?'throws':r.final_value===2?'live':'one',valueMatch=cat==='throws'||(text!==''&&Number(text)===r.final_value);
 clear((!pred?'予想未選択。':pred===cat&&valueMatch?'予想と一致。':'予想と不一致。')+' 観測: '+(cat==='throws'?'ReferenceError・最終値なし':`exit0・最終値${r.final_value}`));$('results').hidden=false;$('answer').hidden=false;
 $('classification').textContent=r.exception_class?`実Node例外 ${r.exception_class}。exit${r.exit}、成功値なし。`:`実Node成功。exit${r.exit}、final ${r.final_value}。`;
 $('graph').textContent=pretty({edges:r.graph,cycle:r.cycle});$('outcome').textContent=pretty(result(r));for(const id of ['immediate','delayed'])$(id).textContent=pretty(result(data.rows.find(x=>x.id===id)));
 $('events').textContent=r.events.map((e,i)=>`${i+1}. ${JSON.stringify(e)}`).join('\n');$('stdout').textContent=r.stdout;$('stderr').textContent=r.stderr||'（空）';$('process').textContent=`child PID ${r.pid} · ${r.process.node} · exit ${r.exit}`;
 $('run').textContent=`run ${data.run_id} · ${data.environment.node} · ${data.environment.platform}/${data.environment.arch} · built-ins`;$('raw').setAttribute('href',`observations/${data.run_id}/raw.json`);$('command').setAttribute('href',`observations/${data.run_id}/command.json`);for(const id of ['a','b'])$('fixture-'+id).setAttribute('href',`fixtures/${r.id}/${id}.mjs`);
 $('answer-body').textContent=reasons[r.id]+' これは明示console logの観測です。engine内部binding作成やDFS状態を採取したとは扱いません。';
});

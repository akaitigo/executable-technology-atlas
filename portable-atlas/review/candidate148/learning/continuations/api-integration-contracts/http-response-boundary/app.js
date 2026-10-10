'use strict';
const PINS={"results":"f754a433441a63d8d6631f599a7ea936aee9d130286416baf7d58f4288322ee2","cases":"1a7ff35c4f346616e0dc58afe63d3aa03c2a7c1ff4bd3d70a4bdd98d759b09d3","source":"6a0744ed6ee329b99936352114920e90fa33eb917c72f507ff1766e322645452"};
const $=id=>document.getElementById(id), text=(id,t)=>$(id).textContent=t, json=x=>JSON.stringify(x,null,2);
const NAMES={'complete':'完全105 byte','short-content-length':'宣言106・本文105 byte','at-limit':'上限ちょうど8192 byte','over-limit':'上限超過8193 byte'};
const OUT={'json-ready':'JSONを次へ渡せる','incomplete-response':'宣言長に届かず止まる','body-limit-exceeded':'本文上限を超えて止まる'};
const GATES={framing:'長さの完了',budget:'本文の上限',media:'媒体',json:'JSON'};
const VERDICTS={pass:'通過',reject:'拒否','not-run':'未検査'};
let data=null,cases=null,source='',selected=null,epoch=0,controller=null;
function clear(){
 selected=null;for(const id of ['result-title','metrics','length-diagram','gates','api-state','runtime-meta','wire-body','comparison','counterexample','answer','source'])text(id,'');
 $('result-section').hidden=true;$('comparison-section').hidden=true;$('source').hidden=true;$('wire-details').open=false;
 for(const id of ['source-button','answer-button'])$(id).disabled=true;
 delete document.body.dataset.case;delete document.body.dataset.outcome;delete $('answer').dataset.match;
}
function prepare(resetPrediction=false){clear();if(resetPrediction)$('prediction').value='';const c=cases?.cases.find(c=>c.id===$('condition').value);text('input',c?json(c):'');$('input-details').open=false;$('play').disabled=!c||!$('prediction').value;document.body.dataset.phase='prepared';text('status','条件と予想を選び、保存した受信を読んでください。');}
function metric(label,key,value){const e=document.createElement('div');e.className='metric';e.dataset.key=key;e.dataset.value=JSON.stringify(value);const l=document.createElement('span');l.textContent=label;const v=document.createElement('strong');v.textContent=value===null?'なし':String(value);e.append(l,v);$('metrics').append(e);}
function svg(tag,attrs,t){const e=document.createElementNS('http://www.w3.org/2000/svg',tag);for(const[k,v]of Object.entries(attrs))e.setAttribute(k,v);if(t!==undefined)e.textContent=t;$('length-diagram').append(e);return e;}
function diagram(r){const scale=470/Math.max(r.declaredLength,r.bodyLength,1);[['declared','宣言した本文',r.declaredLength,45,'#c8d8df'],['received','受信した本文',r.bodyLength,110,'#008579']].forEach(([k,l,v,y,col])=>{svg('text',{x:18,y:y+18},l);svg('rect',{x:145,y,width:v*scale,height:28,fill:col,'data-kind':k,'data-bytes':v});svg('text',{x:145,y:y-7},v+' byte');});svg('text',{x:145,y:174},'不足 '+Math.max(0,r.declaredLength-r.bodyLength)+' byte ／ read('+r.readAmount+') '+r.readCalls+'回');}
function show(){if(!data||!$('prediction').value)return;clear();selected=data.observations.find(o=>o.id===$('condition').value);const o=selected,r=o.response,a=o.assessment;
 document.body.dataset.phase='shown';document.body.dataset.case=o.id;document.body.dataset.outcome=a.outcome;text('result-title',NAMES[o.id]+'：'+OUT[a.outcome]);
 metric('保存HTTP状態','httpStatus',r.status);metric('宣言した長さ byte','declaredLength',r.declaredLength);metric('受信した長さ byte','bodyLength',r.bodyLength);metric('readでの例外','readException',r.readException);metric('完全受信','completeResponse',a.completeResponse);metric('上限8192以内の診断','withinBudget',a.withinBudget);diagram(r);
 for(const s of a.stages){const e=document.createElement('li');e.dataset.gate=s.gate;e.dataset.verdict=s.verdict;e.textContent=GATES[s.gate];const v=document.createElement('span');v.textContent=VERDICTS[s.verdict];e.append(v);$('gates').append(e);}
 text('api-state','実APIの補助観測：read後の残り '+r.apiRemainingAfterRead+' byte、isclosed() = '+r.apiIsClosedAfterRead+'。isclosedは完全受信の一般条件ではありません。');
 text('runtime-meta','保存実行 '+data.startedAt+' ／ '+data.toolchain.python.split('\n')[0]+' ／ http.client SHA-256 '+data.stdlibModules['http.client'].sha256);
 text('wire-body',json(o));$('result-section').hidden=false;
 for(const item of data.observations){const row=document.createElement('tr'),s=item.response,b=item.assessment;row.dataset.case=item.id;row.dataset.assessment=JSON.stringify(b);for(const v of [NAMES[item.id],s.declaredLength+' / '+s.bodyLength,s.readException===null?'なし':json(s.readException),String(b.completeResponse),String(b.withinBudget),OUT[b.outcome],b.exceptionOnlyIncorrect?'完了と誤判断':'完了と判断（この例では一致）']){const td=document.createElement('td');td.textContent=v;row.append(td);}$('comparison').append(row);}
 text('counterexample',a.exceptionOnlyIncorrect?'この条件では、例外なしから完了とする推論が誤りです。JSONとして有効な本文でも、この利用側はJSON検査へ進みません。':'例外なしと長さの完了が一致する条件です。ただし本文上限と業務結果は別の判断です。');$('comparison-section').hidden=false;
 $('source-button').disabled=false;$('answer-button').disabled=false;text('status','固定した保存記録を表示しました。新しいHTTP要求は送っていません。');
}
async function verified(path,pin,signal){const r=await fetch(path,{cache:'no-store',signal});if(!r.ok)throw Error('保存記録を取得できません（'+r.status+'）。');const t=await r.text();const h=Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256',new TextEncoder().encode(t))),x=>x.toString(16).padStart(2,'0')).join('');if(!pin||h!==pin)throw Error('保存記録の内容が固定版と一致しません。');return t;}
async function load(){const n=++epoch;controller?.abort();controller=new AbortController();data=null;cases=null;source='';clear();text('input','');$('input-details').open=false;$('condition').replaceChildren();$('prediction').value='';for(const id of ['condition','prediction','play','reset'])$(id).disabled=true;document.body.dataset.phase='loading';$('status').dataset.error='false';text('status','保存記録を確認しています。');
 try{if(!PINS.results||!PINS.source)throw Error('HTTP実験は未実施です。手期待を実測として表示しません。');const[r,c,s]=await Promise.all([verified('observations/run-01/results.json',PINS.results,controller.signal),verified('cases.json',PINS.cases,controller.signal),verified('observations/run-01/inputs/boundary.py',PINS.source,controller.signal)]);if(n!==epoch)return;const parsed=JSON.parse(r),input=JSON.parse(c);if(parsed.observations.length!==4||input.cases.length!==4||parsed.executionFailure!==null)throw Error('保存記録の構成を確認できません。');data=parsed;cases=input;source=s;for(const c of input.cases){const option=document.createElement('option');option.value=c.id;option.textContent=NAMES[c.id];$('condition').append(option);}for(const id of ['condition','prediction','reset'])$(id).disabled=false;prepare(true);
 }catch(e){if(n!==epoch)return;data=null;cases=null;source='';clear();text('input','');$('condition').replaceChildren();document.body.dataset.phase='error';$('status').dataset.error='true';text('status',e.message);}
}
$('condition').addEventListener('change',()=>prepare(true));$('prediction').addEventListener('change',()=>prepare(false));$('reset').addEventListener('click',()=>prepare(true));$('play').addEventListener('click',show);$('reload').addEventListener('click',load);
$('source-button').addEventListener('click',()=>{text('source',source);$('source').hidden=false;});
$('answer-button').addEventListener('click',()=>{if(!selected)return;const match=$('prediction').value===selected.assessment.outcome;$('answer').dataset.match=String(match);text('answer',(match?'予想と一致しました。':'予想とは異なります。')+' 保存結果：'+OUT[selected.assessment.outcome]+'。宣言 '+selected.response.declaredLength+' byte / 受信 '+selected.response.bodyLength+' byte。JSONに渡す値：'+json(selected.assessment.decodedJSON));});
load();

'use strict';
const $=id=>document.getElementById(id);
const paths={results:'observations/run-01/results.json',source:'observations/run-01/inputs/codec.py'};
const locks={results:'20ffa65689a7e44605af428d6e1111f0f2767e5102dcd596583873de7b3614b6',source:'06fabcc4b72378844cb9fa2e090bdce231b2b97053ec83a50824ef5a3432bfb2'};
const labels=['p1','p2','d1','p4','d2','d3','d4','p8'];
const actions={pass_checks:'検査を通過（変更せず返す）',correct_1to7:'位置1〜7の1ビットを訂正',correct_p8:'位置8の1ビットを訂正',reject_double:'2ビット誤りとして拒否（値を返さない）'};
const presets={none:[],data:[6],parity:[1],overall:[8],double:[1,2],double8:[3,8],triple:[1,2,3],quad:[1,2,3,8]};
const state={message:'1011',errors:[],outside:false,prediction:null,shown:false};
let data=null,lookup=null,generation=0,controller=null,current=null;
function node(tag,text,cls){const e=document.createElement(tag);if(text!==undefined)e.textContent=text;if(cls)e.className=cls;return e;}
function clearResult(){
  current=null;state.shown=false;
  for(const id of ['checks','decision','bit-results','comparison-content','calculation-json','answer'])$(id).replaceChildren();
  $('decision').removeAttribute('data-action');$('comparison-content').removeAttribute('data-available');
  $('answer').hidden=true;$('answer').removeAttribute('data-match');$('answer').removeAttribute('data-outcome');$('result').hidden=true;$('reveal').disabled=true;$('calculation-details').open=false;
  document.querySelectorAll('tr[data-action]').forEach(r=>r.classList.remove('active'));
}
function validate(){
  if(!/^[01]{4}$/.test(state.message))return '送る情報は0と1を4文字で入力してください。';
  if(state.errors.length>2&&!(state.outside&&state.message==='0000'&&[3,4].includes(state.errors.length)))return 'この操作欄では0〜2箇所を選んでください。3・4箇所の比較は専用の例から選べます。';
  return null;
}
function reset(clearPrediction=true){
  clearResult();if(clearPrediction){state.prediction=null;document.querySelectorAll('input[name=prediction]').forEach(e=>e.checked=false);}
  const error=validate();$('input-error').hidden=!error;$('input-error').textContent=error||'';
  $('guarantee-note').textContent=state.outside?'保証外の例です。元の情報を0000に固定しています。3bit以上を正しく検出・訂正する保証はありません。':'ここでは反転が0・1・2箇所の条件を比べます。訂正後の検査が通ることと、元へ戻ることを分けて予想してください。';
  $('guarantee-note').dataset.outside=String(state.outside);
  $('replay').disabled=!data||!!error||!state.prediction;
  $('observation-status').textContent=error?'条件を直してから予想してください。':state.prediction?'予想を選びました。保存した計算結果を表示できます。':'条件を決めて、先に予想してください。';
}
function syncControls(){
  $('message').value=state.message;document.querySelectorAll('input[name=errors]').forEach(e=>e.checked=state.errors.includes(Number(e.value)));
}
function bitsRow(label,word,marked,kind){
  const group=node('section',undefined,'bit-row');group.dataset.kind=kind;group.append(node('h4',label));
  if(word===null){group.append(node('p','訂正後の値はありません。拒否して値を返しません。','withheld'));return group;}
  const row=node('div',undefined,'bits');row.style.setProperty('--bits',word.length);
  for(const [i,bit] of [...word].entries()){
    const cell=node('span',undefined,'bit');cell.dataset.position=i+1;if(marked.includes(i+1))cell.classList.add('changed');
    cell.append(node('small',String(i+1),'position'),node('b',bit,'value'),node('small',labels[i],'role'));row.append(cell);
  }group.append(row);return group;
}
function key(scheme,message,errors){return scheme+'/'+message+'/'+(errors.join(',')||'-');}
function selected(){return lookup.get(key('secded8',state.message,state.errors));}
function display(){
  if(!data||validate()||!state.prediction)return;
  clearResult();const row=selected();if(!row){$('input-error').textContent='この条件の保存した計算結果がありません。条件を選び直してください。';$('input-error').hidden=false;return;}
  current=row;state.shown=true;const d=row.decoder;
  for(const [name,value] of [['シンドローム s',`${d.syndromeBits} = ${d.syndrome}`],['全体パリティ q',String(d.overall)],['反転する位置',d.flip===null?'なし':String(d.flip)]]){const box=node('div');box.append(node('small',name),node('b',value));$('checks').append(box);}
  $('decision').textContent=actions[d.action];$('decision').dataset.action=d.action;
  $('bit-results').append(bitsRow('送信列（教材側が用意）',row.sent,[],'sent'),bitsRow('受信列（復号器への入力）',d.received,row.errors,'received'),bitsRow('処理後の列',d.corrected,d.flip===null?[]:[d.flip],'corrected'));
  const control=lookup.get(key('hamming7',state.message,state.errors));
  if(control&&state.errors.every(p=>p<=7)){
    const c=control.decoder;$('comparison-content').dataset.available='true';
    $('comparison-content').append(node('p',`シンドローム ${c.syndromeBits} = ${c.syndrome} ／ ${actions[c.action]}`,'control-action'),bitsRow('同じ反転位置の7bit受信列',c.received,control.errors,'control-received'),node('p',`返す4bit：${c.decoded} ／ 処理後シンドローム：${c.postSyndrome}`,'control-output'));
  }else{
    $('comparison-content').dataset.available='false';$('comparison-content').append(node('p',state.errors.includes(8)?'7bit方式には位置8がないため、同じ反転位置の対照はありません。位置1・2の例で比べてください。':'この保証外条件の7bit対照は保存していません。位置1・2の例で比べてください。'));
  }
  $('calculation-json').textContent=JSON.stringify(row,null,2);$('result').hidden=false;$('reveal').disabled=false;
  document.querySelector(`tr[data-action=${d.action}]`).classList.add('active');
  $('observation-status').textContent='保存した計算結果です。7bit側と処理の違いを比較し、仕組みを読んでから答え合わせへ進みます。';
}
function reveal(){
  if(!current||!state.shown||!state.prediction)return;
  const row=current,d=row.decoder,truth=row.answerCheck.matchesOriginal;
  const outcome=truth===null?'withhold':truth?'recover':'wrong',match=outcome===state.prediction;
  $('answer').replaceChildren(node('strong',match?'予想と計算結果は一致しました。':'予想と計算結果は異なりました。'));
  $('answer').append(node('p',truth===null?'値は返されませんでした。候補を1つに決めて訂正する代わりに、利用側へ拒否を伝えています。':truth?`返った4bitは ${d.decoded}。元の ${row.message} と一致しました。`:`返った4bitは ${d.decoded}。元の ${row.message} と異なります。「訂正」や「検査通過」という処理名だけでは、回復成功とは言えません。`));
  if(row.category==='outside_guarantee_example')$('answer').append(node('p','これは3bit以上の保証外の例です。この2例から、3bit以上すべての結果を一般化しないでください。','outside-answer'));
  $('answer').append(node('p','元の情報との比較は教材側の答え合わせです。復号器は元の4bitを知らず、受信列の検査値だけで処理しています。'));
  $('answer').dataset.match=String(match);$('answer').dataset.outcome=outcome;$('answer').hidden=false;
}
async function checked(path,expected,signal){
  const r=await fetch(path,{cache:'no-store',signal});if(!r.ok)throw new Error(`保存した記録を読めませんでした (${r.status})。`);
  const bytes=await r.arrayBuffer(),digest=[...new Uint8Array(await crypto.subtle.digest('SHA-256',bytes))].map(x=>x.toString(16).padStart(2,'0')).join('');
  if(digest!==expected)throw new Error('保存した記録の内容が、計算時のものと一致しません。古い結果で補わず、記録を確認してください。');return new TextDecoder().decode(bytes);
}
async function load(){
  const token=++generation;controller?.abort();controller=new AbortController();data=null;lookup=null;
  state.message='1011';state.errors=[];state.outside=false;syncControls();reset(true);$('source-code').replaceChildren();$('coverage-summary').replaceChildren();$('implementation').open=false;
  $('lesson-body').hidden=true;$('load-error').hidden=true;$('load-error').replaceChildren();$('load-status').textContent='保存した計算結果を読んでいます…';document.documentElement.dataset.ready='loading';
  try{
    const [resultText,source]=await Promise.all([checked(paths.results,locks.results,controller.signal),checked(paths.source,locks.source,controller.signal)]);if(token!==generation)return;
    const result=JSON.parse(resultText);
    if(result.executionStatus!=='completed'||result.mainCaseCount!==1056||result.rows.length!==1056||result.outsideGuaranteeExamples.length!==2)throw new Error('必要な計算結果が揃っていません。');
    data=result;lookup=new Map([...data.rows,...data.outsideGuaranteeExamples].map(row=>[row.id,row]));$('source-code').textContent=source;
    $('coverage-summary').textContent='保存した計算：8bit側は16メッセージ×37条件＝592件、7bit側は16×29＝464件。0・1・2箇所の反転を全て含み、3・4箇所の例は別に2件だけ記録しています。';
    reset(true);$('lesson-body').hidden=false;$('load-status').textContent='保存した計算結果と、計算に使った実装を確認しました。';document.documentElement.dataset.ready='true';
  }catch(error){if(token!==generation)return;data=null;lookup=null;clearResult();$('source-code').replaceChildren();$('coverage-summary').replaceChildren();$('lesson-body').hidden=true;$('load-error').hidden=false;$('load-error').textContent=error.message;$('load-status').textContent='記録を確認してから「記録を読み直す」で再試行できます。';document.documentElement.dataset.ready='error';}
}
for(let i=1;i<=8;i++){
  const label=node('label'),input=document.createElement('input');input.type='checkbox';input.name='errors';input.value=i;label.append(input,node('span',`${i} ${labels[i-1]}`));$('error-positions').append(label);
  input.addEventListener('change',()=>{if(!data)return;state.errors=[...document.querySelectorAll('input[name=errors]:checked')].map(e=>Number(e.value));state.outside=false;reset(true);});
}
$('message').addEventListener('input',()=>{if(!data)return;state.message=$('message').value;state.outside=false;reset(true);});
document.querySelectorAll('button[data-preset]').forEach(button=>button.addEventListener('click',()=>{if(!data)return;state.errors=[...presets[button.dataset.preset]];state.outside=['triple','quad'].includes(button.dataset.preset);if(state.outside)state.message='0000';syncControls();reset(true);}));
document.querySelectorAll('input[name=prediction]').forEach(input=>input.addEventListener('change',()=>{if(!data)return;state.prediction=input.value;reset(false);}));
$('replay').addEventListener('click',display);$('reveal').addEventListener('click',reveal);$('reset').addEventListener('click',()=>reset(true));$('reload').addEventListener('click',load);load();

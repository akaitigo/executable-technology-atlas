'use strict';
const S=window.AtlasWasiState,D=window.ATLAS_WASI_DATA;
let state=S.initial();
const $=id=>document.getElementById(id),esc=s=>String(s).replaceAll('&','&amp;').replaceAll('<','&lt;').replaceAll('>','&gt;');
const names={'no-preopen':'ディレクトリを渡さない','granted':'渡して読む','rights-reduced':'開く権限を外す','missing-file':'許可内の名前がない'};
const explanation={descriptor_unavailable:'FD3は事前ディレクトリとして登録されていません。BADF 8の後は、この教材では開く・読む処理へ進んでいません。',bytes_observed:'note.txtを開き、Atlasと改行の6バイトを読み、その次のreadで0バイトのEOFを観測しました。',rights_refusal:'PATH_OPENをbaseから外したため、ファイルを開く処理はNOTCAPABLE 76になりました。ファイルの欠落とは別の結果です。',missing_entry:'このディレクトリ内のファイルを開く権限はありますが、absent.txtという名前がありません。NOENT 44で止まり、readは未到達です。'};
const errno=n=>n===null?'未到達':n===0?'0：成功':n===8?'8：BADF':n===44?'44：NOENT':n===76?'76：NOTCAPABLE':String(n);
function clear(){for(const id of ['flow','result-summary','rights','events','cleanup','provenance','record-json','answer'])$(id).textContent='';$('results').hidden=true;$('answer').hidden=true;$('raw-details').open=false;$('answer-button').disabled=true;}
function output(e){if(!e.output)return '出力値なし';if(e.output.output_used===false)return '失敗時の出力は使用しない';const labels={directory_name_length:'名前のバイト数',guest_name:'ゲスト側の名前',base:'このFDの権限',inheriting:'引き継げる権限',opened_fd:'開いたFD',nread:'読んだバイト数',hex:'16進バイト列',output_used:'成功時の出力を使用'};return Object.entries(e.output).map(([k,v])=>(labels[k]||k)+': '+(v===true?'はい':v===''?'空':v)).join(' ／ ');}
function render(){
 document.querySelectorAll('[data-case]').forEach(b=>b.setAttribute('aria-pressed',String(b.dataset.case===state.id)));document.querySelectorAll('[data-mode]').forEach(b=>b.setAttribute('aria-pressed',String(b.dataset.mode===state.mode)));document.querySelectorAll('input[name=prediction]').forEach(x=>x.checked=x.value===state.prediction);
 $('condition').textContent='選んだ条件：'+names[state.id];clear();for(const id of ['input-error','record-error']){$(id).hidden=true;$(id).textContent='';}
 if(state.error){const id=state.prediction?'record-error':'input-error';$(id).hidden=false;$(id).textContent=state.error;}
 if(!state.shown)return;
 const r=S.validate(D,state.id),o=r.outcome;$('results').hidden=false;
 const steps=[['事前FD',errno(o.prestat_errno)],['ファイルを開く',errno(o.path_open_errno)],['読み出し',o.read_status==='not_reached'?'未到達':'6バイト → EOF'],['後片付け',r.cleanup.file_close_errno!==null?'ファイル・事前FDを閉じる':r.cleanup.preopen_created?'事前FDだけ閉じる':'事前FDなし']];
 $('flow').innerHTML=steps.map(([a,b])=>`<article><small>${a}</small><strong>${esc(b)}</strong></article>`).join('');$('result-summary').textContent=explanation[o.classification];
 if(r.rights_before){$('rights').innerHTML='<h3>権限を二つに分けて読む</h3><div class="rights-grid">'+[['before','変更前',r.rights_before],['after','呼出し時',r.rights_after]].map(([id,label,v])=>`<article data-rights="${id}"><h3>${label}</h3><p class="right-flag">PATH_OPEN：${BigInt(v.base)&8192n?'あり':'なし'}</p><p>このFDの操作（base）<br><code>${v.base}</code></p><p>開いたFDへ渡せる操作（inheriting）<br><code>${v.inheriting}</code></p><p>inheritingのFD_READ：${BigInt(v.inheriting)&2n?'あり':'なし'}</p></article>`).join('')+'</div>';}else $('rights').textContent='権限の照会は未到達です。FDがないことを、権限が少ないことと混同しません。';
 $('events').innerHTML=r.events.map(e=>`<li data-op="${e.op}" data-errno="${e.errno}"><span class="op">${e.sequence+1}. ${e.op}</span><span class="errno">${errno(e.errno)}</span><div class="output">教材のWasm関数へ渡す引数 [${esc(e.args.join(', '))}]<br>${esc(output(e))}</div></li>`).join('');
 $('cleanup').textContent=`後片付け確認：${r.cleanup.complete?'完了':'未確認'}。file close ${r.cleanup.file_close_errno===null?'対象なし':r.cleanup.file_close_errno} ／ preopen close ${r.cleanup.preopen_close_errno===null?'対象なし':r.cleanup.preopen_close_errno}。子プロセス終了と実験用ファイル削除は親の実行ログで確認済みです。`;
 $('provenance').textContent='保存実測 '+D.observed_at+' ／ Node '+r.runtime.node+' ／ uvwasi '+r.runtime.uvwasi+' ／ preview1。呼出し結果をそのまま表示しています。';$('record-json').textContent=JSON.stringify(r,null,2);$('answer-button').disabled=false;
 if(state.answer){$('answer').hidden=false;const match=state.prediction===o.classification;$('answer').innerHTML=`<p class="${match?'good':'wrong'}">予想は${match?'一致':'不一致'}です。</p><p>${explanation[o.classification]}</p><p>この4条件はNodeの有限な実測です。安全な隔離やWASI全体の保証へ広げません。</p>`;}
}
document.querySelectorAll('[data-case]').forEach(b=>b.addEventListener('click',()=>{state=S.change(state,'case',b.dataset.case);render();}));
document.querySelectorAll('[data-mode]').forEach(b=>b.addEventListener('click',()=>{state=S.change(state,'mode',b.dataset.mode);render();}));
document.querySelectorAll('input[name=prediction]').forEach(x=>x.addEventListener('change',()=>{state=S.change(state,'prediction',x.value);render();}));
$('show').addEventListener('click',()=>{state=S.read(state,D);render();});$('reset').addEventListener('click',()=>{state=S.change(state,'reset');render();});$('answer-button').addEventListener('click',()=>{if(state.shown){state.answer=true;render();}});render();

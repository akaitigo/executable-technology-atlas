(function(){'use strict';const R=window.ConfirmGateReader,$=id=>document.getElementById(id);let state=R.initial();
 const explain={
  'no-confirmation-needed':'現在の 2 資源を調べ、確認要求がないため通過します。通過後の削除結果は与えていません。',
  'needs-confirmation':'old-b の確認要求で pending を返します。old-a だけ先に削除することはなく、同 wave の new-config の apply にも進まず戻ります。',
  'already-confirmed':'確認済み flag が true なので、確認必要かの走査を省いて通過します。helper の結果が false に変わった例ではありません。',
  'later-wave-only':'old-later は後続の組です。現在のゲートでは調べず通過します。後続に到達したときの確認や実削除を許可した、という意味ではありません。'};
 const list=ids=>ids.length?ids.join(' → '):'なし';
 function render(){const v=R.view(state),o=v.outcome;
  document.querySelectorAll('[data-case]').forEach(b=>b.setAttribute('aria-pressed',String(b.dataset.case===state.id)));
  $('case-title').textContent=v.item.title;$('input-summary').textContent=`現在は Sync / wave ${v.item.current_wave}。確認済み flag = ${v.item.prune_confirmed}（仮定入力）。`;
  $('input-tasks').innerHTML=[...v.item.current_prunes.map(t=>`<div class="task-seed"><strong>${t.id}</strong><span>現在 wave 0 / prune</span><span>確認必要: ${t.requires_confirmation}</span></div>`),`<div class="task-seed"><strong>new-config</strong><span>現在 wave 0 / apply</span><span>prune 確認の対象外</span></div>`,...v.item.later_prunes.map(t=>`<div class="task-seed"><strong>${t.id}</strong><span>後続 wave ${t.wave} / prune</span><span>確認必要: ${t.requires_confirmation}</span></div>`)].join('');
  document.querySelectorAll('input[type=radio]').forEach(e=>{e.checked=e.value===state[e.name];});
  $('next').disabled=state.step===3;$('answer-button').disabled=state.step!==3||!!state.error;
  $('input-error').hidden=!state.error;$('input-error').textContent=state.error||'';$('progress').textContent=`段階 ${state.step} / 3 · 予想変更で段階と答えを初期化します。`;
  $('stage-status').textContent=['比較前 · 保存結果は未表示です。','段階 1 · 現在の組と後続の組を分けます。','段階 2 · 確認必要かの走査を読みます。','段階 3 · 確認ゲート直後で模型を止めます。'][state.step];
  $('groups').hidden=!v.groupsVisible;$('scan').hidden=!v.scanVisible;$('boundary').hidden=!v.gateVisible;
  $('scan-rows').innerHTML=v.scanVisible?(o.checked_current_ids.length?o.checked_current_ids.map((id,i)=>`<div class="scan-row${id===o.first_blocker?' blocked':''}">${i+1}. ${id}：確認必要 = ${v.item.current_prunes.find(t=>t.id===id).requires_confirmation}${id===o.first_blocker?' → ここで pending を返す':''}</div>`).join(''):'<p class="scan-row">確認済み flag = true → 確認必要かの走査を省略。</p>'):'';
  $('boundary').classList.toggle('pending',v.gateVisible&&o.gate==='pending');
  const values={'gate-value':o.gate,'checked-ids':list(o.checked_current_ids),'first-blocker':o.first_blocker||'なし','continue-value':o.continue_to_prune_loop?'進める（ループは未実行）':'進まない（手前で戻る）','later-checked':list(o.later_prunes_checked),'prunes-started':list(o.current_prunes_started),'apply-started':list(o.current_apply_started),'api-calls':String(o.api_calls),'gate-explanation':explain[state.id]};
  for(const[id,value]of Object.entries(values))$(id).textContent=v.gateVisible?value:'';
  $('answer').hidden=!state.answer;$('answer').innerHTML=state.answer?`<p class="${v.score.gate?'score-yes':'score-no'}">ゲートの予想は${v.score.gate?'一致':'不一致'}。答え：${o.gate}</p><p class="${v.score.blocker?'score-yes':'score-no'}">確認待ち資源の予想は${v.score.blocker?'一致':'不一致'}。答え：${o.first_blocker||'なし'}</p><p>${explain[state.id]}</p><p>模型内の prune / apply / API は未実行です。</p>`:'';
  $('provenance').textContent=`保存模型の実行時刻：${R.data.recorded_at_utc}。この reader は保存結果を読み、模型原票を更新しません。`;
 }
 document.querySelectorAll('[data-case]').forEach(b=>b.addEventListener('click',()=>{state=R.initial(b.dataset.case);render();}));
 document.querySelectorAll('input[type=radio]').forEach(e=>e.addEventListener('change',()=>{state=R.predict(state,e.name,e.value);render();}));
 $('next').addEventListener('click',()=>{state=R.advance(state);render();});$('reset').addEventListener('click',()=>{state=R.initial(state.id);render();});$('answer-button').addEventListener('click',()=>{state=R.reveal(state);render();});render();
})();

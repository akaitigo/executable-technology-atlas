'use strict';
(() => {
  const $ = id => document.getElementById(id);
  let nativeCount = 0, customCount = 0, nameCount = 0, events = [], armed = false;
  function disabled() { return $('disabled').checked; }
  function render() {
    $('native-count').textContent = nativeCount;
    $('custom-count').textContent = customCount;
    $('name-count').textContent = nameCount;
    const focus = document.activeElement;
    $('focusread').textContent = `フォーカス: ${focus.id || focus.tagName.toLowerCase()}（橙色の枠は :focus-visible）`;
    $('events').textContent = events.length ? events.map(e => `${e.at.slice(11,23)} ${e.type} #${e.id} key=${JSON.stringify(e.key)} trusted=${e.trusted} → ${e.native}/${e.custom}/${e.name}`).join('\n') : 'まだイベントはありません。';
    const focusStyle = getComputedStyle(focus);
    $('raw').textContent = JSON.stringify({environment:{userAgent:navigator.userAgent,language:navigator.language,width:innerWidth,height:innerHeight}, mode:$('mode').value, disabled:disabled(), nativeCount, customCount, nameCount, focus:focus.id, focusVisible:focus.matches(':focus-visible'), outlineStyle:focusStyle.outlineStyle, outlineWidth:focusStyle.outlineWidth, nameRepaired:$('name-fix').checked, events});
  }
  function log(e) {
    events.push({at:new Date().toISOString(), type:e.type, id:e.target.id, key:e.key || '', repeat:Boolean(e.repeat), trusted:e.isTrusted, prevented:e.defaultPrevented, native:nativeCount, custom:customCount, name:nameCount});
    events = events.slice(-60); render();
  }
  $('native').addEventListener('click', () => { if (!disabled()) nativeCount++; });
  $('unnamed').addEventListener('click', () => nameCount++);
  function build() {
    const mode = $('mode').value;
    const div = document.createElement('div'); div.id='custom'; div.className='action'; div.textContent='カウントを増やす';
    if (mode !== 'click-only') { div.setAttribute('role','button'); div.tabIndex=0; }
    div.setAttribute('aria-disabled',String(disabled()));
    div.addEventListener('click', () => { if (!disabled()) customCount++; });
    if (mode === 'repaired') {
      for (const type of ['keydown','keyup','blur']) div.addEventListener(type, e => {
        const next = AccessKeyboard.transition(armed,{type:e.type,key:e.key,repeat:e.repeat,disabled:disabled(),focused:document.activeElement===div});
        armed=next.armed; if(next.prevent) e.preventDefault(); if(next.activate) customCount++;
      });
    }
    armed=false; $('mount').replaceChildren(div);
    $('native-declaration').textContent='button / なし（暗黙roleあり） / 0';
    $('custom-declaration').textContent=`div / ${div.getAttribute('role') || 'なし'} / ${div.tabIndex}`;
    const notes = {
      'click-only':'不良例: clickは増えるがTab順に入らず、button roleもない。文字が見えることは操作可能性の証明にならない。',
      'role-only':'不良例: roleとTab到達はあるが、divのEnter/Space既定動作は増やさない。roleは振る舞いを実装しない。',
      repaired:'修正版: role・名前付き文字・Tab到達・Enter/Space処理・focus-visible・disabledの拒否をそろえた。native buttonより保守する動作が多い。'
    };
    $('mode-note').textContent=notes[mode];
    $('implementation').textContent = mode==='click-only' ? '<div onclick="increment()">カウントを増やす</div>\n// role、Tab、キーボード処理がない' : mode==='role-only' ? '<div role="button" tabindex="0" onclick="increment()">カウントを増やす</div>\n// Enter / Space処理がない' : '<div role="button" tabindex="0" aria-disabled="false">カウントを増やす</div>\n// click: 無効でなければ動作\n// keydown Enter: repeatでなければ動作\n// keydown Space: preventDefault + 保留\n// keyup Space: focusとenabledを確認して動作\n// blur: 保留取消 / :focus-visible: 可視枠\n// 実コード: lesson.js + keyboard.js';
    render();
  }
  $('mode').addEventListener('change', () => { customCount=0; build(); });
  $('disabled').addEventListener('change', () => { $('native').disabled=disabled(); $('custom').setAttribute('aria-disabled',String(disabled())); armed=false; render(); });
  $('reset').addEventListener('click', () => { nativeCount=customCount=nameCount=0; events=[]; armed=false; render(); });
  $('name-fix').addEventListener('change', () => { if($('name-fix').checked) $('name-text').removeAttribute('aria-hidden'); else $('name-text').setAttribute('aria-hidden','true'); render(); });
  $('predict').addEventListener('click', () => { $('prediction-result').textContent=$('prediction').value ? '予想を保存。まずTabとクリックで比べてみよう。' : '先に予想を選んでください。'; });
  $('check-answer').addEventListener('click', () => {
    const answers={native:'適切。単純な操作は名前付きnative buttonを優先。標準のrole・Tab・キー処理を利用できる。',complete:'条件付きで適切。カスタムが必要なら動作まで実装する。単純な操作ではnative buttonを優先。',role:'不足。roleだけではTab到達もEnter/Spaceも追加されない。',tab:'不足。Tab到達だけではrole/nameとEnter/Spaceの振る舞いがそろわない。'};
    $('feedback').textContent=answers[$('answer').value] || '修正を選んでください。';
  });
  for (const type of ['focusin','focusout','keydown','keyup','click','change']) document.addEventListener(type, log);
  build();
})();

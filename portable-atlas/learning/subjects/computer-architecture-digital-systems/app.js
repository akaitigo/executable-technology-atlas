'use strict';
const observation = window.CACHE_OBSERVATION;
const cases = observation.result.cases;
const $ = id => document.getElementById(id);
const esc = value => String(value).replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const names = {conflict:'同index競合 · 0 → 16 → 0 → 16',spatial:'同blockのoffset · spatial locality',offset_conflict:'offsetを含む同index競合',one_line:'境界 · 1B / 1行 / address255',upper_boundary:'境界 · 64B / line16B',empty:'境界 · 空trace',invalid_capacity:'拒否 · capacity12B',invalid_line:'拒否 · line3B',line_exceeds_capacity:'拒否 · lineがcapacityより大きい',invalid_address:'拒否 · address256'};
let selected = 'conflict', step = 0, prediction = null;
$('cache-case').innerHTML = Object.keys(cases).map(key => `<option value="${key}">${names[key]}</option>`).join('');
$('cache-environment').innerHTML = [observation.started_at,`${observation.environment.implementation} ${observation.environment.python}`,`${observation.environment.os} ${observation.environment.architecture}`,'LOGICAL / NO CYCLE MEASUREMENT'].map(x=>`<span>${esc(x)}</span>`).join('');

function table(lines, width, active) {
  return lines.map((line,index)=>`<tr class="${index === active ? 'active' : ''}"><td>${index}</td><td>${line.valid ? 1 : 0}</td><td>${line.tag === null ? '—' : line.tag}</td><td>${line.block === null ? '—' : `${line.block} / ${line.block*width}..${line.block*width+width-1}`}</td><td class="${line.valid ? '' : 'empty'}">${line.valid ? line.bytes.join(' ') : 'empty'}</td></tr>`).join('');
}

function diagram(event, lines, width) {
  if (!event) return '<p class="fine">まだreadしていない。全行invalidの状態から始める。</p>';
  const show = lines.slice(0, 8);
  const height = 125 + show.length * 37;
  const boxes = show.map((line,index)=>`<rect x="285" y="${98+index*37}" width="300" height="31" rx="4" fill="${index===event.index?'#efb668':'#e5ede3'}"/><text x="298" y="${119+index*37}" font-size="13">index ${index}: ${line.valid ? `tag ${line.tag} / block ${line.block} / ${line.block*width}..${line.block*width+width-1}` : 'invalid / empty'}</text>`).join('');
  return `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 630 ${height}" width="630" height="${height}" aria-label="address ${event.address}から指定index ${event.index}への配置図"><g font-family="monospace" fill="#233a36"><rect x="22" y="20" width="185" height="48" rx="6" fill="#dce9df"/><text x="35" y="48" font-size="17">address ${event.address}</text><path d="M210 45 H270" stroke="#233a36" stroke-width="2"/><text x="292" y="38" font-size="15">block ${event.block} → index ${event.index}</text><text x="292" y="63" font-size="14">tag ${event.tag}, offset ${event.offset}</text>${boxes}<text x="22" y="115" font-size="13">指定行は一つだけ</text><text x="22" y="138" font-size="13">${event.hit?'HIT':'MISS'} / eviction ${event.evicted_block === null?'none':event.evicted_block}</text>${lines.length>8?`<text x="292" y="${height-8}" font-size="12">diagramは先頭8行。全行はtable/rawで表示。</text>`:''}</g></svg>`;
}

function prefixSummary(trace) {
  const events = trace.slice(0, step);
  return {hits: events.filter(e=>e.hit).length, misses: events.filter(e=>!e.hit).length, evictions: events.filter(e=>e.evicted_block!==null).length, wrong: events.filter(e=>!e.data_correct).length};
}

function renderPolicy(key, run, width) {
  const event = step ? run.trace[step-1] : null;
  $(''+key+'-lines').innerHTML = table(event ? event.after : run.initial_lines, width, event ? event.index : -1);
  if (!event) {
    $(key+'-decision').textContent = '開始状態：valid=0。まだhit/miss判定なし。';
    $(key+'-result').textContent = '返却byte：未読';
    $(key+'-result').className = 'result';
  } else {
    const old = event.before[event.index];
    $(key+'-decision').textContent = `read前 index${event.index}: valid=${old.valid?1:0}, tag=${old.tag===null?'—':old.tag}。要求tag=${event.tag} / ${event.decision_reason}。${event.hit?'HIT':'MISS'}、eviction=${event.evicted_block===null?'なし':event.evicted_block}。空行=${event.empty_lines_before}、memory fetch=${event.memory_bytes_fetched}B。${event.tag_check_bypassed?'tag比較を省略した誤判定。':''}`;
    $(key+'-result').textContent = `返却byte ${event.observed_byte} / 期待 ${event.expected_byte} · ${event.data_correct?'一致':'不一致'}`;
    $(key+'-result').className = 'result'+(event.data_correct?'':' wrong');
  }
  const totals = prefixSummary(run.trace);
  $(key+'-counts').textContent = `ここまで ${step} read · ${totals.hits} hit / ${totals.misses} miss / ${totals.evictions} eviction / ${totals.wrong} wrong byte${step ? ` · hit率 ${Math.round(totals.hits/step*100)}%` : ' · hit率は未定義'}`;
}

function render() {
  const item = cases[selected], input = item.input;
  $('cache-input').textContent = `capacity ${input.capacity_bytes}B / line ${input.line_bytes}B / address ${input.address_bits}bit / input [${input.addresses.join(', ')}]`;
  const rejected = item.status === 'rejected';
  $('cache-error').hidden = !rejected;
  $('cache-prev').disabled = rejected || step === 0;
  $('cache-next').disabled = rejected || step === item.normal.trace.length;
  if (rejected) {
    $('cache-error').textContent = `inputを拒否：${item.error.field} — ${item.error.message}。read開始前に停止、結果/traceなし。`;
    $('cache-step').textContent = 'REJECTED · 無効inputを正常0 missとして扱わない';
    $('cache-address').textContent = '';
    $('cache-diagram').textContent = '';
    ['normal','broken'].forEach(key=>{ $(key+'-lines').innerHTML=''; $(key+'-decision').textContent='read未実行'; $(key+'-result').textContent='結果なし'; $(key+'-result').className='result'; $(key+'-counts').textContent='集計なし'; });
    $('cache-trace').innerHTML = '';
  } else {
    const run = item.normal, event = step ? run.trace[step-1] : null, geo = run.geometry;
    $('cache-step').textContent = step ? `READ ${step} / ${run.trace.length} · address ${event.address} → ${event.hit?'HIT':'MISS'}` : `START · ${geo.line_count}行がinvalid${run.trace.length===0?' / 空trace：0 read、hit率未定義':''}`;
    if (event) {
      const bits = event.address.toString(2).padStart(8,'0');
      const t=geo.tag_bits, i=geo.index_bits;
      $('cache-address').innerHTML = `address ${event.address} = ${bits}<br>` + [['tag',bits.slice(0,t),t,event.tag],['index',bits.slice(t,t+i),i,event.index],['offset',bits.slice(t+i),geo.offset_bits,event.offset]].map(([key,text,count,value])=>`<span class="bit-field bit-${key}"><b>${text||'∅'}</b><small>${key}: ${count}bit / ${value}</small></span>`).join('');
    } else $('cache-address').textContent = `tag ${geo.tag_bits}bit / index ${geo.index_bits}bit / offset ${geo.offset_bits}bit。0bit fieldは値0。`;
    renderPolicy('normal',item.normal,input.line_bytes);
    renderPolicy('broken',item.broken,input.line_bytes);
    $('cache-diagram').innerHTML = diagram(event,event ? event.after : run.initial_lines,input.line_bytes);
    $('cache-trace').innerHTML = run.trace.map(e=>`<tr class="${e.step===step?'active':''}"><td><button data-step="${e.step}">${e.step}へ</button></td><td>${e.address}</td><td>${e.block}</td><td>${e.index}</td><td>${e.tag}</td><td>${e.offset}</td><td>${e.hit?'HIT':'MISS'}</td><td>${e.evicted_block===null?'—':e.evicted_block}</td></tr>`).join('');
    $('cache-trace').querySelectorAll('button').forEach(button=>button.addEventListener('click',()=>{step=Number(button.dataset.step);render();}));
  }
  $('cache-prediction').textContent = prediction===null ? '予想を選び、2回目のreadまで進めよう。' : selected==='conflict' && step>=2 ? `予想「${prediction}」。実判定はMISS。空3行でもblock4はindex0へ来る。初回block4は未読miss、再訪block0/4も競合でmissする。` : `予想「${prediction}」。中心inputの2回目readで比べよう。`;
}
$('cache-case').addEventListener('change',event=>{selected=event.target.value;step=0;render();});
$('cache-reset').addEventListener('click',()=>{step=0;render();});
$('cache-prev').addEventListener('click',()=>{step=Math.max(0,step-1);render();});
$('cache-next').addEventListener('click',()=>{step=Math.min(cases[selected].normal.trace.length,step+1);render();});
$('cache-last').addEventListener('click',()=>{step=cases[selected].normal?cases[selected].normal.trace.length:0;render();});
[['cache-predict-hit','hit'],['cache-predict-miss','miss']].forEach(([id,value])=>$(id).addEventListener('click',()=>{prediction=value;$('cache-predict-hit').setAttribute('aria-pressed',value==='hit');$('cache-predict-miss').setAttribute('aria-pressed',value==='miss');render();}));
render();

const $ = id => document.getElementById(id);
const positions = {config:[40,100],price:[235,100],invoice:[430,100],report:[650,100],audit:[650,235]};
function graph(r){
 const g=r.input.graph, changed=r.input.changed, affected=r.affected||[];
 let s='<svg viewBox="0 0 850 320" role="img" aria-label="利用側から依存先への矢印。影響は逆方向"><defs><marker id="arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0 0L10 5L0 10" fill="#536f7b"/></marker></defs>';
 for(const [a,ds] of Object.entries(g))for(const b of ds){const p=positions[a],q=positions[b];if(a==='report'&&b==='price')s+=`<path d="M${p[0]+65} ${p[1]} Q430 -20 ${q[0]+65} ${q[1]}" fill="none" stroke="#536f7b" stroke-width="2" marker-end="url(#arrow)"/>`;else s+=`<line x1="${p[0]}" y1="${p[1]+30}" x2="${q[0]+130}" y2="${q[1]+30}" stroke="#536f7b" stroke-width="2" marker-end="url(#arrow)"/>`;}
 for(const n of Object.keys(g)){const [x,y]=positions[n],c=changed.includes(n),a=affected.includes(n);s+=`<rect x="${x}" y="${y}" width="130" height="70" rx="12" fill="${c?'#fff0d6':a?'#d8eefb':'#ebeff1'}" stroke="#4c6b7a"/><text x="${x+65}" y="${y+27}" text-anchor="middle" font-size="19">${n}</text><text x="${x+65}" y="${y+52}" text-anchor="middle" font-size="13">${c?'変更':a?'影響':'独立／未選択'}</text>`;}
 return s+'</svg>';
}
function table(rows){return '<table><tr><th>要求 / test</th><th>実値 / 期待</th><th>結果</th></tr>'+rows.map(x=>`<tr><td>${x.requirement}<br>${x.test}</td><td>${x.actual} / ${x.expected}</td><td class="${x.pass?'good':'bad'}">${x.pass?'PASS':'FAIL'}</td></tr>`).join('')+'</table>'+(rows.length?'':'<p>選択0：品質保証を意味しません。</p>');}
$('run').addEventListener('click',async()=>{
 $('predictionEcho').textContent='あなたの予想：'+($('prediction').value||'未記入');
 try{
 const res=await fetch('/api?case='+encodeURIComponent($('case').value));if(!res.ok)throw new Error('HTTP '+res.status);const r=await res.json();
 $('raw').textContent=JSON.stringify(r,null,2);$('graph').innerHTML=graph(r);
 if(r.rejected){$('summary').textContent='拒否：'+r.rejected;$('values').innerHTML='';$('naive').innerHTML='未実行';$('closure').innerHTML='未実行';$('oracle').textContent='入力を拒否：選択・挙動の証明なし';$('binding').textContent='保存baseline '+r.input.receipt+' / 現在 '+r.input.currentBaseline;return;}
 const fail=r.closure.filter(x=>!x.pass).length;
 $('summary').textContent=`影響 ${r.affected.length} module ／ closure ${r.closure.length} test ／ 失敗 ${fail} ／ naive見逃し ${r.missedByNaive.length}`;
 $('values').innerHTML='<tr><th>module</th><th>version 前 → 後</th><th>実値 前 → 後</th></tr>'+Object.keys(r.values.before).map(n=>`<tr><td>${n}</td><td>${r.versions.before[n]} → ${r.versions.after[n]}</td><td>${r.values.before[n]} → ${r.values.after[n]}</td></tr>`).join('');
 $('naive').innerHTML=table(r.naive);$('closure').innerHTML=table(r.closure);$('binding').textContent='baseline SHA-256：'+r.input.receipt;
 $('oracle').textContent='独立全path oracle：'+(r.oracle.matches?'一致':'不一致')+' ／ 経路 '+r.oracle.paths.map(p=>p.join(' → ')).join('、');
 }catch(e){$('summary').textContent='実行エラー：'+e.message;}
});

const $=id=>document.getElementById(id);
const presets={stable:[2,.1,false],oscillation:[2,.5,false],boundary:[2,2/3,false],divergence:[2,.8,false],saturation:[2,.1,true]};
const names={stable:'単調に近づく',oscillation:'減衰振動',boundary:'安定境界：振動が消えない',divergence:'発散：振動が拡大する'};
const fmt=x=>x===null?'未適用':Number(x).toPrecision(6);
let baseline;
function plot(rows,control=false){
  const W=520,H=240,L=62,R=15,T=18,B=38;
  const values=rows.flatMap(r=>control?[r.u,r.u_requested,0]:[r.y,r.continuous_unsaturated,1,0]);
  let low=Math.min(...values),high=Math.max(...values);if(low===high)high=low+1;
  const margin=(high-low)*.08;low-=margin;high+=margin;
  const x=t=>L+t/rows.at(-1).t*(W-L-R),y=v=>H-B-(v-low)/(high-low)*(H-T-B);
  const path=key=>rows.map((r,i)=>`${i?'L':'M'}${x(r.t).toFixed(2)},${y(r[key]).toFixed(2)}`).join(' ');
  let grid='';for(let i=0;i<5;i++){const v=low+(high-low)*i/4;grid+=`<path d="M${L},${y(v)}H${W-R}" stroke="#dce6ec"/><text x="${L-6}" y="${y(v)+4}" text-anchor="end">${v.toPrecision(3)}</text>`;}
  const main=control?'u':'y',other=control?'u_requested':'continuous_unsaturated';
  const circles=!control&&rows[0].discrete_oracle!==undefined?rows.map(r=>`<circle cx="${x(r.t)}" cy="${y(r.discrete_oracle)}" r="2.1" fill="none" stroke="#278874"/>`).join(''):'';
  return `<svg class="plot" viewBox="0 0 ${W} ${H}" role="img" aria-label="${control?'uと要求入力':'yと連続時間解析解・離散Oracle'}の時系列plot"><g font-size="11" fill="#526f81">${grid}<text x="${L}" y="${H-16}">0</text><text x="${W-R}" y="${H-16}" text-anchor="end">${fmt(rows.at(-1).t)} s</text><text x="12" y="15">${main}</text></g>${!control?`<path d="M${L},${y(1)}H${W-R}" stroke="#71818b" stroke-dasharray="3 5"/>`:''}<path d="${path(other)}" fill="none" stroke="#b77226" stroke-width="2" stroke-dasharray="5 4"/><path d="${path(main)}" fill="none" stroke="#236ea6" stroke-width="2.5"/>${circles}</svg>`;
}
async function calculate(params){const res=await fetch('/api/simulate?'+new URLSearchParams(params));const data=await res.json();if(!res.ok)throw Error(data.error);return data;}
async function run(){
  $('status').textContent='Pythonで計算中…';
  try{
    const p={gain:$('gain').value,dt:$('dt').value,steps:$('steps').value};if($('clip').checked)p.limit=$('limit').value;
    const prediction=$('prediction').value;
    const data=await calculate(p),s=data.summary;
    if(!baseline)baseline=await calculate({gain:2,dt:.1,steps:40});
    $('baseline').innerHTML=plot(baseline.samples);$('selected').innerHTML=plot(data.samples);$('input-plot').innerHTML=plot(data.samples,true);
    $('selected-title').textContent=`選択：K=${p.gain} / h=${p.dt} / ${p.limit?'clip ±'+p.limit:'clipなし'}`;
    $('metrics').innerHTML=[['線形Eulerの係数 a',s.linear_factor_a],['最終 y',s.final_y],['最終偏差 r−y',s.final_error],['飽和した更新',s.saturated_updates]].map(([label,v])=>`<div class="metric">${label}<strong>${fmt(v)}</strong></div>`).join('');
    const actual=p.limit&&s.saturated_updates>0?'saturation':s.linear_euler_class;
    const outcome=actual==='saturation'?'入力上限が作動。線形の安定性分類はclipした系の判定には使いません。':names[actual];
    const match=prediction==='unsure'?'予測を選んで再実行すると照合できます。':prediction===actual?'予測と今回のモデル結果が一致しました。':'予測と異なりました。aの符号・大きさと入力uを確認してください。';
    $('answer').textContent=`答え：${outcome} ${match} P制御だけでは目標1に一致するとは限りません。`;
    $('oracle').textContent=`離散Oracle：${s.oracle} / 最大scaled誤差 ${fmt(s.max_scaled_oracle_error)} / ${s.oracle_pass===null?'解析Oracle未適用':s.oracle_pass?'許容値1e−12以内':'照合失敗'}。これは連続解との近似誤差とは別です。`;
    $('execution').textContent=`実行：Python ${data.execution.python} / ${data.execution.observed_at} / source SHA256 ${data.execution.source_sha256.slice(0,16)}…`;
    $('raw').href=data.execution.raw_path;
    $('samples').textContent=JSON.stringify([...data.samples.slice(0,5),data.samples.at(-1)],null,2);
    $('status').textContent='Python計算完了・生JSONを専用module内に保存';
  }catch(error){$('status').textContent='計算できません：'+error.message;}
}
$('controls').addEventListener('submit',e=>{e.preventDefault();run();});
document.querySelectorAll('[data-preset]').forEach(b=>b.addEventListener('click',()=>{const [k,h,clip]=presets[b.dataset.preset];$('gain').value=k;$('dt').value=h;$('clip').checked=clip;$('steps').value=40;$('limit').value=.35;$('status').textContent='条件を変更しました。予測してから「Pythonで計算」を押してください。';}));
run();

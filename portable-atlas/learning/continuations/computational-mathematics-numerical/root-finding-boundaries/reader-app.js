(() => {
  'use strict';
  const S=window.RootBoundaryState,D=window.ROOT_BOUNDARY_DATA,E=window.ROOT_BOUNDARY_EXPECTED;
  const $=id=>document.getElementById(id), esc=v=>String(v).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const text=v=>v===null?'未定義／未到達':v===true?'満たす':v===false?'満たさない':String(v);
  const labels={CONTINUE:'更新を続ける',EXACT_ROOT:'厳密な根',BRACKET_WIDTH_MET:'区間幅の条件を満たす',LOCAL_TOLERANCES_MET:'残差と更新幅の両条件を満たす',ZERO_DERIVATIVE:'根でない点で導関数0',ITERATION_LIMIT:'更新上限に到達',INVALID_BRACKET:'符号変化しない区間を拒否'};
  const titles={'cubic-cycle':'f(x)=x³−2x+2 ／ 区間[−2,0] ／ Newton初期0','cubic-local':'f(x)=x³−2x+2 ／ 区間[−2,0] ／ Newton初期−2','zero-derivative':'f(x)=x²−2 ／ 区間[1,2] ／ Newton初期0','bad-bracket':'f(x)=x²−2 ／ 区間[2,3] ／ Newton初期1','exact-endpoint':'f(x)=x² ／ 区間[0,1] ／ Newton初期0'};
  const notes={
    'cubic-cycle':'Newton法は0→1→0→1→0。専用の循環検出でなく更新4回の上限で止まりました。返却0の残差は2で、根ではありません。二分法は幅1/8で停止し、現在区間の中点−29/16から区間内の根までの距離は1/16以下です。残差1349/4096は別の量です。',
    'cubic-local':'同じ式・同じ上限でも、Newton初期−2は2回で残差とstepがともに1/16以下です。初期値の影響を示す有限例で、どの開始点でもこの速度で収束する保証ではありません。二分法は前条件と同じ区間列です。',
    'zero-derivative':'Newton初期0ではf=−2で根ではなく、f′=0のため更新できません。更新0・stepはnullです。二分法は3回で幅1/8へ。導関数0の停止は方程式全体に根がないという判定ではありません。',
    'bad-bracket':'二分法の端点値は2と7で同符号。反復を開始せず返却候補はnullです。Newton法は区間を引数に取りません。k=2では残差1/144だけ合格し、step1/12は不合格。k=3で両条件を満たします。',
    'exact-endpoint':'最初の0は厳密な根なので、両方法とも更新0です。Newton法はf=0を導関数0より先に判定します。stepが0だったのではなく、更新をしていないためnullです。二分法の保持区間は[0,0]になります。'};
  const bkeys=[['k','更新数'],['a','左端 a'],['b','右端 b'],['probe','直前のprobe'],['estimate','現在区間の中点'],['f','中点の f'],['residual','残差 |f|'],['width','区間幅'],['radius','半幅上界'],['status','この境界の判断']];
  const nkeys=[['k','更新数'],['x','現在の x'],['f','f(x)'],['df','導関数 f′'],['delta','符号付き変化'],['step','更新幅 |delta|'],['residual','残差 |f|'],['residual_met','残差の条件'],['step_met','更新幅の条件'],['status','この境界の判断']];
  let state=S.initial();
  for(const method of ['bisection','newton']){
    $('predict-'+method).innerHTML='<option value="">選んでください</option>'+Object.entries(labels).filter(([k])=>k!=='CONTINUE').map(([k,v])=>`<option value="${k}">${v}</option>`).join('');
  }
  function dispatch(action){state=S.transition(state,action,D,E);render();}
  function fields(id,entries){document.querySelector('#'+id+' .fields').innerHTML=entries.map(([key,label,value])=>`<dt>${esc(label)}</dt><dd data-field="${key}">${esc(text(value))}</dd>`).join('');}
  function table(method,rows,keys){
    const caption=method==='bisection'?'二分法の全境界':'Newton法の全境界';
    $(method+'-table').innerHTML=`<caption>${caption}</caption><thead><tr>${keys.map(([,label])=>`<th>${esc(label)}</th>`).join('')}</tr></thead><tbody>${rows.map((row,i)=>`<tr data-k="${row.k}" class="${i===state.indices[method]?'selected':''}">${keys.map(([key])=>`<td data-key="${key}">${esc(text(row[key]))}</td>`).join('')}</tr>`).join('')}</tbody>`;
  }
  function diagram(br,nr){
    const num=s=>{const [a,b='1']=s.split('/');return Number(a)/Number(b);};
    const px=x=>90+(x+2)*120;
    let html='<line x1="90" y1="65" x2="690" y2="65" stroke="#96aaa4"/><line x1="90" y1="135" x2="690" y2="135" stroke="#96aaa4"/>';
    for(let v=-2;v<=3;v++)html+=`<text x="${px(v)}" y="28" text-anchor="middle">${v}</text>`;
    html+='<text x="12" y="61">二分法</text><text x="12" y="132">Newton</text>';
    if(br){html+=`<line data-role="bracket" data-a="${br.a}" data-b="${br.b}" x1="${px(num(br.a))}" y1="65" x2="${px(num(br.b))}" y2="65" stroke="#135c46" stroke-width="10"/><circle data-role="midpoint" data-value="${br.estimate}" cx="${px(num(br.estimate))}" cy="65" r="7" fill="#135c46"/><text x="100" y="98">保持区間とその中点（k=${br.k}）</text>`;}else html+='<text x="150" y="69">開始拒否：保持区間・候補なし</text>';
    if(nr)html+=`<circle data-role="newton-point" data-value="${nr.x}" cx="${px(num(nr.x))}" cy="135" r="7" fill="#1b598c"/><text x="100" y="170">現在の更新点（k=${nr.k}）／線は軌道ではありません</text>`;
    $('diagram').innerHTML=html;
  }
  function render(){
    $('case').value=state.case_id;$('record-mode').value=state.mode;
    $('predict-bisection').value=state.prediction_bisection;$('predict-newton').value=state.prediction_newton;
    $('condition').textContent=titles[state.case_id];
    $('results').hidden=true;$('provenance').textContent='';$('limits').textContent='';$('answer').textContent='';$('answer').hidden=true;$('raw').textContent='';$('raw-details').open=false;$('diagram').innerHTML='';
    for(const method of ['bisection','newton']){const box=$(method);box.querySelector('.terminal').textContent='';box.querySelector('.fields').textContent='';box.querySelector('.position').textContent='';$(method+'-table').textContent='';}
    document.querySelector('#bisection .validation').textContent='';$('error').textContent=state.error;
    if(!state.shown)return;
    $('results').hidden=false;
    const shown=state.shown,c=shown.payload;
    $('provenance').textContent=`保存計算 ${shown.observed_at_utc} ／ ${shown.run_id} ／ SHA256 ${shown.result_sha256}`;
    $('limits').textContent='幅≤1/8 ／ 残差≤1/16 かつ更新幅≤1/16 ／ 最大4更新。カードは選択中の境界、停止理由は終端結果です。';
    for(const method of ['bisection','newton']){
      const out=c[method],idx=state.indices[method],row=out.rows[idx]||null,keys=method==='bisection'?bkeys:nkeys,box=$(method);
      box.querySelector('.terminal').textContent=`終端：${labels[out.status]} ／ ${out.updates}更新 ／ 返却候補 ${text(out.estimate)}`;
      box.querySelector('.position').textContent=row?`境界 ${idx} / ${out.rows.length-1}`:'反復境界なし';
      $(method+'-prev').disabled=!row||idx===0;$(method+'-next').disabled=!row||idx===out.rows.length-1;
      fields(method,keys.map(([key,label])=>[key,label,row?row[key]:null]));table(method,out.rows,keys);
    }
    const v=c.bisection.validation;
    document.querySelector('#bisection .validation').textContent=`初期端点 [${v.a}, ${v.b}] ／ f(a)=${v.fa}, f(b)=${v.fb} ／ 開始条件 ${v.bracket_valid?'成立':'不成立'} ／ 端点の根 ${v.endpoint_root===null?'なし':v.endpoint_root}`;
    diagram(c.bisection.rows[state.indices.bisection]||null,c.newton.rows[state.indices.newton]||null);
    $('raw').textContent=JSON.stringify(c,null,2);
    if(state.answer){$('answer').hidden=false;$('answer').textContent=`予想との比較：二分法 ${state.prediction_bisection===c.bisection.status?'一致':'不一致'}、Newton法 ${state.prediction_newton===c.newton.status?'一致':'不一致'}。 ${notes[state.case_id]}`;}
  }
  $('case').addEventListener('change',e=>dispatch({type:'case',value:e.target.value}));
  $('record-mode').addEventListener('change',e=>dispatch({type:'mode',value:e.target.value}));
  for(const method of ['bisection','newton']){
    $('predict-'+method).addEventListener('change',e=>dispatch({type:'prediction',method,value:e.target.value}));
    $(method+'-prev').addEventListener('click',()=>dispatch({type:'step',method,delta:-1}));
    $(method+'-next').addEventListener('click',()=>dispatch({type:'step',method,delta:1}));
  }
  $('load').addEventListener('click',()=>dispatch({type:'load'}));$('reset').addEventListener('click',()=>dispatch({type:'reset'}));$('show-answer').addEventListener('click',()=>dispatch({type:'answer'}));
  window.ROOT_READER={snapshot:()=>JSON.parse(JSON.stringify(state))};render();
})();

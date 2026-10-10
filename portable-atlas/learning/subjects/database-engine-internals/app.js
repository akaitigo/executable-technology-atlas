// SPDX-License-Identifier: Apache-2.0
(() => {
  const {raw, run} = window.ENGINE_LESSON;
  const copy = [
    {title:'Indexなしの等価条件', note:'通常のtable scanが計画されました。この名前から実際の訪問行数や処理時間は分かりません。', input:'表 samples', path:'table SCAN'},
    {title:'Index追加後の同じ等価条件', note:'bucketの等価条件でsamples_bucket_idxを使うSEARCH。結果は前と同じ16行です。', input:'bucket index', path:'index SEARCH'},
    {title:'Indexはあるが、条件を式へ変更', note:'bucket + 0はこのfixtureの答えを変えませんが、通常のbucket indexによるSEARCHではなくSCANになりました。', input:'表 samples', path:'table SCAN'},
  ];
  let current = 0;
  document.getElementById('version').textContent = run.runtime.sqlite_version;
  document.getElementById('resultRows').innerHTML = raw.cases[0].rows.map(row => '<tr>'+row.map(v=>'<td>'+v+'</td>').join('')+'</tr>').join('');
  function choose(index) {
    current = index;
    const item = raw.cases[index];
    document.querySelectorAll('[data-case]').forEach(button => button.setAttribute('aria-pressed', String(Number(button.dataset.case)===index)));
    document.getElementById('caseTitle').textContent = copy[index].title;
    document.getElementById('caseNumber').textContent = '0'+(index+1)+' / 03';
    document.getElementById('query').textContent = item.query+'\nparameters: '+JSON.stringify(item.parameters);
    document.getElementById('indexState').textContent = index ? raw.setup.index_sql : 'CREATE INDEX前の同じ表・同じ256行';
    document.getElementById('answer').hidden = true;
  }
  document.querySelectorAll('[data-case]').forEach(button=>button.addEventListener('click',()=>choose(Number(button.dataset.case))));
  document.getElementById('reveal').addEventListener('click',()=>{
    const item = raw.cases[current], detail = item.plan.rows[0][3], mode = detail.split(' ')[0];
    document.getElementById('answer').hidden = false;
    document.getElementById('planMode').textContent = mode;
    document.getElementById('verdict').textContent = document.getElementById('prediction').value===mode ? '予想と一致' : '予想と異なる計画';
    document.getElementById('rawPlan').textContent = item.explain_query+'\n'+JSON.stringify(item.plan.rows[0]);
    document.getElementById('explanation').textContent = copy[current].note;
    document.getElementById('flowInput').textContent = copy[current].input;
    document.getElementById('flowPath').textContent = copy[current].path;
  });
  choose(0);
})();

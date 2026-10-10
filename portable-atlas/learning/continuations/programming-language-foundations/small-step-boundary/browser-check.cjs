'use strict';
// Atlas: use only root's supplied page. No browser/context/tab/server creation or close.
const fs=require('fs'),path=require('path'),crypto=require('crypto'),assert=require('assert/strict');
const ROOT=__dirname, sha=b=>crypto.createHash('sha256').update(b).digest('hex');
const sourceNames=['index.html','lesson.js','style.css','reference.html','bundle.json','SKILL.md'];
const hashes=()=>Object.fromEntries(sourceNames.map(n=>[n,sha(fs.readFileSync(path.join(ROOT,n)))]));
const ids=['zero-value','arithmetic-complete','arithmetic-budget','application-value','not-callable-stuck'];
function term(t){if(t.kind==='Int')return String(t.value);if(t.kind==='Var')return t.name;if(t.kind==='Fn')return '(fn '+t.param+' → '+term(t.body)+')';if(t.kind==='Call')return term(t.fn)+'('+term(t.arg)+')';return '('+term(t.left)+' + '+term(t.right)+')';}
module.exports=async function({page,baseURL,outDir}){
  fs.mkdirSync(outDir,{recursive:true});const start=Date.now(),viewport=page.viewportSize(),routes=[];
  const report={project:'Atlas',passed:false,errors:[],checks:[],dom:[],captures:[],pointer_actions:[],keyboard_actions:[],api_actions:[],references:[],response_order_probes:[],source_before:hashes(),
    bounds:{operation_entry_budget_ms:90000,description:'Cooperative check at operation entries; individual awaits/navigation use 6/10 seconds. Cleanup separate. Not a hard whole-run deadline.'},
    ownership:{provided_page_only:true,created_browser:0,created_context:0,created_tab:0,created_server:0,closed_shared_resource:0}};
  const bundle=JSON.parse(fs.readFileSync(path.join(ROOT,'bundle.json'),'utf8'));
  const observation=bundle.run_text?JSON.parse(bundle.run_text):null;
  const results=observation?observation.records.filter(x=>x.kind==='case-result'):[];
  const base=baseURL.endsWith('/')?baseURL:baseURL+'/';const url=base+'index.html',bundleURL=base+'bundle.json';
  function guard(){assert(Date.now()-start<=90000,'cooperative operation-entry budget exceeded');}
  function note(name,detail){report.checks.push({name,passed:true,detail});}
  async function pointer(selector){
    guard();const loc=page.locator(selector);await loc.scrollIntoViewIfNeeded({timeout:6000});
    const p=await loc.evaluate(el=>{for(const r of el.getClientRects()){const x=(Math.max(0,r.left)+Math.min(innerWidth,r.right))/2,y=(Math.max(0,r.top)+Math.min(innerHeight,r.bottom))/2;const hit=document.elementFromPoint(x,y);if(x>=0&&x<innerWidth&&y>=0&&y<innerHeight&&hit&&(el===hit||el.contains(hit)))return{x,y,tag:hit.tagName};}throw Error('no visible hit rectangle');});
    await page.mouse.click(p.x,p.y);report.pointer_actions.push({selector,...p});
  }
  async function text(value){await pointer('#prediction');await page.keyboard.type(value);report.keyboard_actions.push({selector:'#prediction',method:'keyboard.type',value});}
  async function fresh(){guard();await page.goto(url,{waitUntil:'domcontentloaded',timeout:10000});await page.waitForFunction(()=>typeof fetch==='function');}
  async function cleared(label){guard();assert(await page.locator('#result').isHidden());assert(await page.locator('#answer').isHidden());assert.equal(await page.locator('#raw').textContent(),'');assert.equal(await page.locator('#comparison tbody tr').count(),0);assert(await page.locator('#answer-button').isDisabled());note(label);await state(label);}
  async function load(){guard();await text('規則の歩数と観測行を分けて考える');await pointer('#read-button');await page.locator('#result').waitFor({state:'visible',timeout:6000});}
  async function answer(){await pointer('#answer-button');await page.locator('#answer').waitFor({state:'visible',timeout:6000});assert((await page.locator('#answer').textContent()).includes('規則適用'));}
  async function state(label){guard();const actual=await page.evaluate(()=>{
    const q=id=>document.getElementById(id),visible=e=>!!e&&getComputedStyle(e).display!=='none'&&!e.hidden;
    return{selected:document.querySelector('input[name=case]:checked').value,prediction:q('prediction').value,
      result_visible:visible(q('result')),answer_visible:visible(q('answer')),message:q('message').textContent,title:q('phase-title').textContent,
      rule:q('rule-text').textContent,table:[...q('comparison').querySelectorAll('tbody tr')].map(tr=>[...tr.cells].map(td=>td.textContent)),
      events:[...q('big-events').querySelectorAll('tbody tr')].map(tr=>[...tr.cells].map(td=>td.textContent)),
      diagram_texts:[...q('diagram').querySelectorAll('text')].map(x=>x.textContent),diagram:q('diagram').outerHTML,
      diagram_lines:q('diagram').querySelectorAll('line').length,diagram_boxes:q('diagram').querySelectorAll('rect').length,
      raw:q('raw').textContent?JSON.parse(q('raw').textContent):null,answer:q('answer').textContent,
      disabled:Object.fromEntries(['previous-case','next-case','previous-step','next-step','answer-button'].map(id=>[id,q(id).disabled])),
      viewport:{width:innerWidth,height:innerHeight,scrollWidth:document.documentElement.scrollWidth},visible_body:document.body.innerText};
    });actual.label=label;report.dom.push(actual);return actual;}
  async function inspect(label,index){const a=await state(label),r=results.find(x=>x.case_id===a.selected);assert(r);assert.deepEqual(a.raw,r);
    const s=r.small_step,final=index===s.states.length-1,t=index?s.transitions[index-1]:null;
    const rows=[['現在の項',term(s.states[index])],['適用した歩数',String(index)],['残りの予算',String(s.budget-index)],['停止分類',final?s.status:'途中'],['小ステップの整数結果',final&&s.value!==null?String(s.value):'値の結果なし'],['未適用の次規則',final&&s.unapplied_next_rule?s.unapplied_next_rule.join(' → ')+'（未実行）':'なし'],['旧評価器の最終結果',final?(r.big_step.error?r.big_step.error.code:String(r.big_step.value)):'最終状態で表示'],['旧評価器のnode-enter',final?String(r.big_step.evaluations):'最終状態で表示'],['旧評価器の観測event数',final?String(r.big_step.trace.length):'最終状態で表示']];
    assert.deepEqual(a.table,rows);assert(a.title.includes(`状態 ${index} / ${s.states.length-1}`));
    assert.equal(a.diagram_lines,index?1:0);assert.equal(a.diagram_boxes,index?2:1);
    assert(a.diagram_texts.includes(term(s.states[index])));if(t){assert(a.diagram_texts.includes(term(t.before)));assert(a.rule.includes(t.rule_chain.join(' → ')));assert(a.rule.includes(t.redex_path));}else assert(a.diagram_texts.includes('初期の項（適用0歩）'));
    assert.deepEqual(a.events,final?r.big_step.trace.map(e=>[String(e.step),e.action,e.node_path]):[]);
    assert.equal(a.disabled['previous-step'],index===0);assert.equal(a.disabled['next-step'],final);assert.equal(a.disabled['answer-button'],!final);
    assert(a.viewport.scrollWidth<=a.viewport.width);note(label,{case_id:r.case_id,state:index,final});return a;
  }
  async function toFinal(r){for(let i=1;i<r.small_step.states.length;i++)await pointer('#next-step');}
  async function capture(name,selector){guard();if(selector){await page.locator(selector).evaluate(e=>e.scrollIntoView({block:'start'}));report.api_actions.push({method:'element.scrollIntoView',selector,block:'start'});}else{await page.evaluate(()=>scrollTo(0,0));report.api_actions.push({method:'window.scrollTo',x:0,y:0});}
    const file=name+'.png';await page.screenshot({path:path.join(outDir,file),fullPage:false,timeout:6000});const bytes=fs.readFileSync(path.join(outDir,file));report.captures.push({file,sha256:sha(bytes),viewport:page.viewportSize(),full_page:false});}
  async function route(pattern,handler){guard();await page.route(pattern,handler);routes.push([pattern,handler]);}
  async function unroute(pattern,handler){await page.unroute(pattern,handler);const i=routes.findIndex(x=>x[0]===pattern&&x[1]===handler);if(i>=0)routes.splice(i,1);}
  async function clickedDownload(selector){guard();let receive,timer;const promise=new Promise((resolve,reject)=>{receive=resolve;timer=setTimeout(()=>reject(Error('download event timeout')),6000);});promise.catch(()=>{});page.once('download',receive);try{await pointer(selector);return await promise;}finally{clearTimeout(timer);page.removeListener('download',receive);}}
  try{
    assert(observation&&observation.collection_complete&&results.length===5,'saved complete calculation required');
    await page.setViewportSize({width:1280,height:800});report.api_actions.push({method:'setViewportSize',width:1280,height:800});await fresh();await capture('1280-entry');await cleared('initial result and answer absent');
    for(let i=0;i<results.length;i++){
      if(i)await pointer(`input[value="${ids[i]}"]`);await load();const r=results[i];
      for(let j=0;j<r.small_step.states.length;j++){if(j)await pointer('#next-step');await inspect('primary-'+ids[i]+'-'+j,j);}
      await answer();const a=await state('answer-'+ids[i]);assert(a.answer.includes(r.small_step.status));assert(a.answer.includes(String(r.big_step.trace.length)+'観測event'));
      if(i===2){assert(a.answer.includes('もう1歩なら10'));assert(a.answer.includes('適用していません'));}if(i===4)assert(a.answer.includes('引数1+2は未還元'));
      await capture('1280-'+ids[i],i===3?'#answer':'#diagram');
      if(i===1){await pointer('#previous-step');assert(await page.locator('#answer').isHidden());assert(await page.locator('#result').isVisible());await inspect('visible-answer-backward-state',2);await pointer('#next-step');await inspect('forward-state',3);}
    }
    await pointer('#previous-case');await cleared('visible answer -> previous condition clears all');assert.equal(await page.locator('#prediction').inputValue(),'');await load();await toFinal(results[3]);await answer();await pointer('#next-case');await cleared('visible answer -> next condition clears all');
    await load();await answer();await pointer('#prediction');await page.keyboard.type('追記');report.keyboard_actions.push({method:'keyboard.type',value:'追記'});await cleared('visible answer -> prediction edit clears all');
    await pointer('#reset-button');await load();await answer();await pointer('input[value="arithmetic-complete"]');await cleared('visible answer -> radio condition clears all');await load();await toFinal(results[1]);await answer();await pointer('#reset-button');await cleared('visible answer -> reset clears all');assert(await page.locator('#previous-case').isDisabled());
    await load();await answer();
    const unavailable=r=>r.fulfill({status:503,contentType:'text/plain',body:'Atlas test fixture unavailable'});await route(bundleURL,unavailable);await pointer('#read-button');await page.waitForFunction(()=>document.getElementById('message').textContent.includes('HTTP 503'));await cleared('HTTP failure clears old results');await state('http-503');await capture('1280-http-failure','#message');await unroute(bundleURL,unavailable);await pointer('#read-button');await page.locator('#result').waitFor({state:'visible'});await inspect('HTTP restored',0);
    const changed=r=>r.fulfill({status:200,contentType:'application/json',body:JSON.stringify({...bundle,unexpected:'modified'})});await route(bundleURL,changed);await pointer('#read-button');await page.waitForFunction(()=>document.getElementById('message').textContent.includes('digest'));await cleared('changed digest rejected');await unroute(bundleURL,changed);await pointer('#read-button');await page.locator('#result').waitFor({state:'visible'});await inspect('digest restored',0);
    await fresh();await page.evaluate(()=>{const original=window.fetch;let once=true;window.__probe={kind:'old-success-after-reset',events:[]};window.fetch=(...args)=>{if(String(args[0]).includes('bundle.json')&&once){once=false;__probe.events.push({event:'old-fetch-start',at:performance.now()});return original(args[0],{cache:'no-store'}).then(r=>new Promise(resolve=>{__probe.release=()=>{__probe.events.push({event:'old-success-delivered',at:performance.now()});resolve(r);};}));}return original(...args);};});await text('遅い成功');await pointer('#read-button');await page.waitForFunction(()=>typeof window.__probe.release==='function',null,{timeout:6000});await pointer('#reset-button');await page.evaluate(()=>{__probe.events.push({event:'reset-completed',at:performance.now()});__probe.release();});await page.waitForTimeout(100);await cleared('old success ignored after reset');await state('stale-success-reset');
    const successOrder=await page.evaluate(()=>({kind:__probe.kind,events:__probe.events}));assert.deepEqual(successOrder.events.map(x=>x.event),['old-fetch-start','reset-completed','old-success-delivered']);assert(successOrder.events[2].at>=successOrder.events[1].at);report.response_order_probes.push(successOrder);
    await fresh();await page.evaluate(()=>{const original=window.fetch;let once=true;window.__probe={kind:'old-error-after-new-success',events:[]};window.fetch=(...args)=>{if(String(args[0]).includes('bundle.json')&&once){once=false;__probe.events.push({event:'old-fetch-start',at:performance.now()});return new Promise((resolve,reject)=>{__probe.release=()=>{__probe.events.push({event:'old-error-delivered',at:performance.now()});reject(Error('old failure'));};});}return original(...args);};});await text('遅い失敗');await pointer('#read-button');await pointer('input[value="arithmetic-complete"]');await load();await page.evaluate(()=>{__probe.events.push({event:'new-success-visible',at:performance.now()});__probe.release();});await page.waitForTimeout(100);await inspect('old error ignored after new success',0);
    const errorOrder=await page.evaluate(()=>({kind:__probe.kind,events:__probe.events}));assert.deepEqual(errorOrder.events.map(x=>x.event),['old-fetch-start','new-success-visible','old-error-delivered']);assert(errorOrder.events[2].at>=errorOrder.events[1].at);report.response_order_probes.push(errorOrder);
    await page.setViewportSize({width:390,height:844});report.api_actions.push({method:'setViewportSize',width:390,height:844});await fresh();await capture('390-entry');await pointer('input[value="arithmetic-budget"]');await load();await toFinal(results[2]);await inspect('390-budget-final',2);await capture('390-budget-diagram','#diagram');await capture('390-budget-table','#comparison');
    await answer();await pointer('#previous-step');assert(await page.locator('#answer').isHidden());assert(await page.locator('#result').isVisible());await inspect('390-backward',1);await pointer('#next-step');await inspect('390-forward',2);
    // Local HTML navigation is actual pointer and visible DOM; Markdown is a download.
    guard();await Promise.all([page.waitForURL(base+'reference.html',{timeout:10000}),pointer('a[href="reference.html"]')]);assert((await page.locator('body').innerText()).includes('AtlasのCallArgはFn限定'));report.references.push({kind:'local-html-visible-dom',url:page.url(),body:await page.locator('body').innerText()});
    const official='https://softwarefoundations.cis.upenn.edu/plf-current/Smallstep.html';const block=r=>r.fulfill({status:200,contentType:'text/html; charset=utf-8',body:'<!doctype html><html lang="ja"><body><h1>Atlas 外部通信を遮断したローカル案内</h1><p>公式本文は取得・表示していません。</p></body></html>'});await route(official,block);
    await Promise.all([page.waitForURL(official,{waitUntil:'domcontentloaded',timeout:10000}),pointer('#official-source')]);const notice=await page.locator('body').innerText();assert(notice.includes('公式本文は取得・表示していません'));report.references.push({kind:'external-pointer-local-block-notice',url:official,body:notice,external_body_read:false,external_network:false});await unroute(official,block);await fresh();
    const download=await clickedDownload('a[href="SKILL.md"]');const downloaded=path.join(outDir,'SKILL.download.md');await download.saveAs(downloaded);const actual=fs.readFileSync(downloaded),expected=fs.readFileSync(path.join(ROOT,'SKILL.md'));assert.deepEqual(actual,expected);report.references.push({kind:'actual-pointer-download-not-DOM',href:'SKILL.md',bytes:actual.length,sha256:sha(actual)});
    report.passed=true;
  }catch(error){report.errors.push({name:error.name,message:error.message,stack:error.stack});}
  finally{
    for(const[pattern,handler]of routes.reverse()){try{await page.unroute(pattern,handler);}catch(e){report.errors.push({cleanup:'unroute',message:e.message});}}
    try{if(viewport)await page.setViewportSize(viewport);report.viewport_restored=true;}catch(e){report.errors.push({cleanup:'viewport',message:e.message});}
    report.source_after=hashes();report.source_unchanged=JSON.stringify(report.source_before)===JSON.stringify(report.source_after);report.page_preserved=!page.isClosed();report.elapsed_ms=Date.now()-start;report.passed=report.passed&&report.errors.length===0&&report.source_unchanged&&report.page_preserved;
    fs.writeFileSync(path.join(outDir,'report.json'),JSON.stringify(report,null,2)+'\n');
  }
  return report;
};

/* Atlas: use only the parent's existing page; no browser, context, tab or server lifecycle. */
'use strict';
const fs=require('node:fs'),path=require('node:path'),crypto=require('node:crypto'),assert=require('node:assert/strict');
module.exports=async function({page,baseURL,outDir}){
 const lesson='formal-fairness-starvation',root=__dirname,base=baseURL.endsWith('/')?baseURL:baseURL+'/',oldViewport=page.viewportSize();
 fs.mkdirSync(outDir,{recursive:true});const reportFile=path.join(outDir,'report.json');if(fs.existsSync(reportFile))throw Error('Atlas: output report already exists');
 const begin=Date.now(),budget=45000,report={project:'Atlas',lesson,started_at:new Date().toISOString(),passed:false,budget_ms:budget,base_url:base,source_before:{},source_after:{},checks:[],dom:[],pointer_actions:[],keyboard_actions:[],api_actions:[],faults:[],captures:[],references:[],errors:[],new_browser:0,new_context:0,new_tab:0,new_server:0,new_target_execution:0,cleanup:{routes_removed:false,hooks_restored:false,viewport_restored:false,page_left_open:true}};
 const routes=[],read=n=>fs.readFileSync(path.join(root,n)),sha=b=>crypto.createHash('sha256').update(b).digest('hex'),note=(name,detail=true)=>report.checks.push({name,passed:true,detail});
 const guard=()=>{if(Date.now()-begin>=budget)throw Error('Atlas: 45 second checker budget reached; no retry');};
 const timeout=(max=3000)=>{guard();return Math.max(1,Math.min(max,budget-(Date.now()-begin)));};
 const onError=e=>report.errors.push({kind:'pageerror',message:String(e)});page.on('pageerror',onError);
 let hookInstalled=false,sourceNames=[];
 function bind(){return Object.fromEntries(sourceNames.map(n=>[n,sha(read(n))]));}
 function preserveInputs(names){sourceNames=[...new Set(names)];report.source_before=bind();report.checker_sha256=sha(fs.readFileSync(__filename));for(const n of sourceNames){const dest=path.join(outDir,'tested-source',n);fs.mkdirSync(path.dirname(dest),{recursive:true});fs.writeFileSync(dest,read(n));}}
 async function pointer(selector){guard();const e=page.locator(selector);await e.scrollIntoViewIfNeeded({timeout:timeout()});const b=await e.boundingBox();assert.ok(b,selector+' has bounds');const x=b.x+b.width/2,y=b.y+b.height/2;await page.mouse.move(x,y);await page.mouse.click(x,y);report.pointer_actions.push({selector,x,y,viewport:page.viewportSize()});}
 async function predict(text='Atlas の予想'){await pointer('#prediction');await page.keyboard.insertText(text);report.keyboard_actions.push({kind:'insertText',selector:'#prediction',text});}
 async function viewport(width,height){guard();await page.setViewportSize({width,height});report.api_actions.push({kind:'viewport',width,height});}
 async function goto(relative='index.html'){guard();const url=new URL(relative,base).href;const response=await page.goto(url,{waitUntil:'load',timeout:timeout(6000)});report.api_actions.push({kind:'same-page-navigation',url});return response;}
 async function snapshot(label,extra={}){
  guard();const actual=await page.evaluate(()=>{
   const ids={};for(const e of document.querySelectorAll('[id]')){const visible=!!e.getClientRects().length&&getComputedStyle(e).visibility!=='hidden';ids[e.id]={text:e.textContent,visible,disabled:'disabled' in e?e.disabled:null,value:'value' in e?e.value:null,open:'open' in e?e.open:null,aria_pressed:e.getAttribute('aria-pressed')};}
   const tables=Object.fromEntries([...document.querySelectorAll('tbody[id]')].map(t=>[t.id,[...t.querySelectorAll('tr')].map(r=>[...r.cells].map(c=>c.textContent))]));
   const svg=[...document.querySelectorAll('svg')].map(e=>({id:e.id,outer_html:e.outerHTML,text:[...e.querySelectorAll('text')].map(t=>t.textContent),circles:[...e.querySelectorAll('circle')].map(c=>Object.fromEntries([...c.attributes].map(a=>[a.name,a.value])))}));
   const raw=document.getElementById('raw')?.textContent||'';let parsed=null;try{if(raw)parsed=JSON.parse(raw);}catch{}
   return {url:location.href,body_text:document.body.innerText,ids,tables,svg,raw_text:raw,raw_parsed:parsed,heading_order:[...document.querySelectorAll('h2')].map(e=>e.textContent),choices:[...document.querySelectorAll('#choices button,input[name="case"]')].map(e=>({case:e.dataset.case||e.value,checked:e.checked??null,pressed:e.getAttribute('aria-pressed')})),width:document.documentElement.scrollWidth,viewport:innerWidth};
  });const row={label,viewport:page.viewportSize(),...extra,...actual};report.dom.push(row);return row;
 }
 async function clearCheck(label,{navigationDisabled=false,predictionEmpty=false}={}){const d=await snapshot(label);assert.equal(d.ids.result.visible,false);assert.equal(d.ids.answer.visible,false);assert.equal(d.ids['answer-button'].disabled,true);assert.equal(d.raw_text,'');assert.equal(d.ids.verdict.text,'');assert.equal(d.ids['fairness-table'].text,'');for(const key of ['diagram','step-table','choices','interpretation','obligations'])if(d.ids[key])assert.equal(d.ids[key].text,'',key+' cleared');if(navigationDisabled){assert.equal(d.ids.previous.disabled,true);assert.equal(d.ids.next.disabled,true);}if(predictionEmpty)assert.equal(d.ids.prediction.value,'');note(label);return d;}
 async function shot(name,selector='#result'){guard();await page.locator(selector).scrollIntoViewIfNeeded({timeout:timeout()});const file=path.join(outDir,name+'.png');await page.screenshot({path:file,fullPage:false,animations:'disabled',timeout:timeout(6000)});const b=fs.readFileSync(file);report.captures.push({file:path.basename(file),sha256:sha(b),width:b.readUInt32BE(16),height:b.readUInt32BE(20),viewport:page.viewportSize(),actual_capture:true});}
 async function overflow(label){const d=await snapshot(label);assert.ok(d.width<=d.viewport+1,'page width '+d.width+' exceeds '+d.viewport);note(label,{width:d.width,viewport:d.viewport});}
 async function shown(){await page.locator('#result').waitFor({state:'visible',timeout:timeout()});}
 async function answer(){await pointer('#answer-button');assert.equal(await page.locator('#answer').isVisible(),true);await snapshot('answer-visible');}
 async function hook(){guard();await page.evaluate(()=>{
  if(window.__atlasNineChecker)throw Error('checker hook already exists');const original=crypto.subtle.digest,originalFetch=window.fetch;
  const h={original,originalFetch,originalData:window.ATLAS_DATA_TEXT,armed:false,held:false,done:0,release:null,reject:null};
  crypto.subtle.digest=function(...args){if(h.armed){h.armed=false;h.held=true;return new Promise((resolve,reject)=>{h.release=()=>original.apply(crypto.subtle,args).then(v=>{h.done++;resolve(v);});h.reject=()=>{h.done++;reject(Error('Atlas controlled stale digest rejection'));};});}return original.apply(crypto.subtle,args).then(v=>{h.done++;return v;});};window.__atlasNineChecker=h;
 });hookInstalled=true;report.api_actions.push({kind:'page-local-digest-hook',source_files_edited:false});}
 async function armDigest(){await page.evaluate(()=>{const h=window.__atlasNineChecker;h.armed=true;h.held=false;h.done=0;h.release=null;h.reject=null;});report.faults.push({kind:'hold-next-digest'});}
 async function held(){await page.waitForFunction(()=>window.__atlasNineChecker?.held,null,{timeout:timeout()});}
 async function releaseDigest(success,done){await page.evaluate(async ok=>{const h=window.__atlasNineChecker;if(ok)await h.release();else h.reject();},success);await page.waitForFunction(n=>window.__atlasNineChecker.done>=n,done,{timeout:timeout()});await page.evaluate(()=>new Promise(r=>setTimeout(r,0)));report.faults.push({kind:success?'release-stale-success':'release-stale-error'});}
 async function reference(relative,expectedFile=relative){
  guard();const url=new URL(relative,base).href;
  if(expectedFile){
   const response=await page.request.get(url,{timeout:timeout(5000)});assert.ok(response.ok(),'reference HTTP '+relative);const bytes=await response.body();assert.deepEqual(bytes,read(expectedFile),'HTTP body bytes '+relative);
   report.api_actions.push({kind:'HTTP-reference-delivery',url});report.references.push({href:relative,url,method:'page.request HTTP GET; delivery bytes, not visible DOM or hand-click',status:response.status(),headers:response.headers(),response_sha256:sha(bytes),response_bytes:bytes.length,body_text:bytes.toString('utf8'),visible_dom_checked:false});
  }else{
   const response=await goto(relative);assert.ok(response&&response.ok(),'HTML reference '+relative);const body=await response.text(),visible=await page.locator('body').innerText({timeout:timeout()});assert.ok(visible.trim().length>20,'HTML reference body visible '+relative);
   report.references.push({href:relative,url:page.url(),method:'same-page goto for HTML reference; not a hand-clicked link',status:response.status(),headers:response.headers(),response_sha256:sha(Buffer.from(body)),visible_text:visible,visible_dom_checked:true});
  }
 }
 async function clickedReference(relative){
  await goto();const url=new URL(relative,base).href,response=await page.request.get(url,{timeout:timeout()});assert.ok(response.ok());const bytes=await response.body();assert.deepEqual(bytes,read(relative));const headers=response.headers(),type=(headers['content-type']||'').split(';')[0];
  report.api_actions.push({kind:'reference HTTP headers and bytes before real click',url,content_type:type});
  if(type==='application/octet-stream'||(headers['content-disposition']||'').includes('attachment')){
   // A download intentionally aborts navigation. Do not create a competing waitForURL.
   const event=page.waitForEvent('download',{timeout:timeout(4000)});await pointer(`a[href="${relative}"]`);const download=await event;
   const f=path.join(outDir,'clicked-'+path.basename(relative));await download.saveAs(f);const saved=fs.readFileSync(f);assert.deepEqual(saved,read(relative));report.references.push({href:relative,method:'real pointer click; Playwright download event, not document DOM',headers,download_file:path.basename(f),bytes:saved.length,sha256:sha(saved),visible_dom_checked:false});
  }else if(type.startsWith('text/')){
   const navigation=page.waitForURL(url,{waitUntil:'load',timeout:timeout(4000)});await pointer(`a[href="${relative}"]`);await navigation;
   const text=await page.locator('body').innerText({timeout:timeout()});assert.equal(text.trim(),read(relative).toString('utf8').trim());await snapshot('clicked document '+relative);report.references.push({href:relative,method:'real pointer click; same-page document navigation',headers,visible_text:text,visible_dom_checked:true});
  }else throw Error('Atlas: unsupported reference MIME '+type);
  await goto();note('real clicked reference '+relative);
 }
 try{
  const status=JSON.parse(read('status.json')),runPath=status.observation,run=JSON.parse(read(runPath)),cases=run.records.filter(c=>c.kind==='lasso');
  preserveInputs(['index.html','lesson.js','style.css','data.js','expected.json','CONTRACT.md','RUN_CONDITIONS.md','SOURCES.md','fairness.py','SKILL.md','README.md','COVERAGE.md','RESULTS.md','browser-check.cjs',runPath]);
  function steps(c){return [{segment:'initial',from:c.prefix_states[0]},...c.prefix_rows,...c.cycle_rows];}
  async function stage(c,n,primary=false){const s=steps(c)[n],d=await snapshot(c.id+'/'+n,{case_id:c.id,stage:n,primary});assert.deepEqual(d.raw_parsed,s);assert.equal(d.ids.result.visible,true);assert.equal(d.ids.answer.visible,false);assert.equal(d.ids.previous.disabled,n===0);assert.equal(d.ids.next.disabled,n===steps(c).length-1);assert.equal(d.ids['answer-button'].disabled,n!==steps(c).length-1);
   assert.deepEqual(d.tables['step-table'],['Next0','Next1','Enter1'].map(t=>[t,s.enabled?String(s.enabled[t]):'遷移前のため未表示',s.executed?String(s.executed[t]):'まだ選択していない']));
   for(const v of s.from)assert.ok(d.ids.diagram.text.includes(v===null?'free':String(v)));if(s.to)for(const v of s.to)assert.ok(d.ids.diagram.text.includes(v===null?'free':String(v)));
   assert.equal(d.ids['phase-title'].text,s.segment==='initial'?'初期状態':`${s.segment==='prefix'?'導入 prefix':'反復 cycle'} ${s.ordinal+1}：${s.action}`);
   if(s.nonstutter_choices)assert.equal(d.ids.choices.text,'出発状態で選べた非停滞の動作：'+s.nonstutter_choices.join(' / '));note(c.id+' stage '+n+' saved values match');return d;
  }
  async function choose(c){await pointer('#case-'+c.id);await clearCheck('case change clears displayed results',{navigationDisabled:true,predictionEmpty:true});}
  async function load(c,primary=false){await pointer('#load');await shown();await stage(c,0,primary);}
  async function end(c,primary=false){for(let n=1;n<steps(c).length;n++){await pointer('#next');await stage(c,n,primary);}await answer();const d=await snapshot('answer/'+c.id,{case_id:c.id});assert.deepEqual(d.tables['fairness-table'].map(x=>x.slice(1)),c.fair.map((v,i)=>[String(v),String(c.fair_starvation_counterexample[i])]));assert.deepEqual(JSON.parse(d.ids.obligations.text),c.progress_obligations);assert.ok(d.ids.verdict.text.includes('P1の要求が満たされない = '+c.p1_starves));return d;}
  await viewport(1280,900);await goto();await shot('1280-entry','header');await clearCheck('initial',{navigationDisabled:true,predictionEmpty:true});assert.equal(await page.locator('#load').isDisabled(),true);
  for(const c of cases){await choose(c);await predict('Atlas '+c.id+'：機会と選択を分けて予想');await load(c,true);await end(c,true);if(c.id==='holder-stutter')await shot('1280-holder-answer','#answer');if(c.id==='p0-keeps-winning')await shot('1280-p0-cycle','#answer');if(c.id==='earlier-entry-does-not-satisfy-later-request')await shot('1280-later-request','#answer');await pointer('#previous');await stage(c,steps(c).length-2);await pointer('#next');await stage(c,steps(c).length-1);await answer();}
  note('all 6 prefix/cycle and 24 fairness outcomes checked');
  const holder=cases[2];await choose(holder);await predict('入室がずっと無効');await load(holder);await end(holder);
  for(let i=0;i<4;i++){await pointer('#regime-'+run.records[2].fairness_order[i]);await clearCheck('regime change from displayed answer',{navigationDisabled:true,predictionEmpty:true});await predict('対象の仕様を変更');await load(holder);const d=await end(holder);assert.ok(d.ids.verdict.text.includes('この列を許す = '+holder.fair[i]));assert.ok(d.ids.verdict.text.includes('公平だが飢餓する反例 = '+holder.fair_starvation_counterexample[i]));}
  await predict(' 予想を更新');await clearCheck('prediction changed from visible answer',{navigationDisabled:true});await load(holder);await end(holder);await pointer('#reset');await clearCheck('reset after visible answer',{navigationDisabled:true,predictionEmpty:true});
  await hook();const first=cases[0];await predict('資料確認');await load(first);await end(first);
  await page.evaluate(()=>{window.ATLAS_DATA_TEXT=undefined;});report.faults.push({kind:'page-local missing data'});await pointer('#load');await page.waitForFunction(()=>document.getElementById('load-status').dataset.kind==='error',null,{timeout:timeout()});await clearCheck('missing data clears prior answer',{navigationDisabled:true});await shot('1280-data-failure','#load-status');
  await page.evaluate(()=>{window.ATLAS_DATA_TEXT=window.__atlasNineChecker.originalData+' ';});report.faults.push({kind:'page-local digest mismatch'});await pointer('#load');await page.waitForFunction(()=>document.getElementById('load-status').textContent.includes('ダイジェスト'),null,{timeout:timeout()});await clearCheck('changed data clears prior answer',{navigationDisabled:true});await page.evaluate(()=>{window.ATLAS_DATA_TEXT=window.__atlasNineChecker.originalData;});await load(first);await end(first);note('data restored without source changes');
  await armDigest();await pointer('#load');await held();await clearCheck('waiting digest clears visible old answer',{navigationDisabled:true});await pointer('#reset');await releaseDigest(true,1);await clearCheck('old success after reset',{navigationDisabled:true,predictionEmpty:true});
  await predict('旧失敗の排除');await armDigest();await pointer('#load');await held();await choose(holder);await predict('新しい保持中停滞');await load(holder);const fresh=await page.locator('#raw').textContent();await releaseDigest(false,2);assert.equal(await page.locator('#raw').textContent(),fresh);await snapshot('old failure cannot replace newer result');note('both stale response paths');
  await viewport(390,844);await shot('390-entry','header');await choose(holder);await predict('強公平性だけでは解放を要求しない');await load(holder);await end(holder);await overflow('390 result width');await shot('390-holder-answer','#answer');await pointer('#previous');await stage(holder,steps(holder).length-2);await shot('390-state','#diagram');await pointer('#next');await stage(holder,steps(holder).length-1);await answer();await pointer('#reset');await clearCheck('mobile reset after visible answer',{navigationDisabled:true,predictionEmpty:true});
  assert.equal(report.dom.filter(d=>d.primary).length,cases.reduce((n,c)=>n+steps(c).length,0));
  for(const f of ['SOURCES.md','CONTRACT.md','expected.json','fairness.py','SKILL.md','README.md','COVERAGE.md'])await reference(f);await goto();note('7 reference HTTP bodies; not document DOM or hand-click');await clickedReference('inputs/prerequisite-model.py');await clickedReference('SKILL.md');
  assert.equal(report.errors.length,0);report.passed=true;
 }catch(error){report.errors.push({kind:'checker-failure',message:String(error.stack||error)});try{await snapshot('failure-state');}catch{}}
 finally{
  for(const [pattern,handler]of routes){try{await page.unroute(pattern,handler);}catch(e){report.errors.push({kind:'route-cleanup',message:String(e)});}}
  report.cleanup.routes_removed=routes.length===0||!report.errors.some(e=>e.kind==='route-cleanup');
  if(hookInstalled){try{await page.evaluate(()=>{const h=window.__atlasNineChecker;if(h){if(h.held&&h.reject)h.reject();crypto.subtle.digest=h.original;window.fetch=h.originalFetch;window.ATLAS_DATA_TEXT=h.originalData;delete window.__atlasNineChecker;}});report.cleanup.hooks_restored=true;}catch(e){report.errors.push({kind:'hook-cleanup',message:String(e)});}}else report.cleanup.hooks_restored=true;
  try{if(oldViewport)await page.setViewportSize(oldViewport);report.cleanup.viewport_restored=true;}catch(e){report.errors.push({kind:'viewport-cleanup',message:String(e)});}
  page.off('pageerror',onError);try{report.source_after=bind();report.sources_unchanged=JSON.stringify(report.source_before)===JSON.stringify(report.source_after);assert.ok(report.sources_unchanged);}catch(e){report.errors.push({kind:'source-binding',message:String(e)});}
  report.passed=report.passed&&report.errors.length===0;report.finished_at=new Date().toISOString();report.elapsed_ms=Date.now()-begin;report.select_option_calls=0;fs.writeFileSync(reportFile,JSON.stringify(report,null,2)+'\n');
 }
 return report;
};

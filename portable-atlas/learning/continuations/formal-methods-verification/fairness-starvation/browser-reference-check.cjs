/* Atlas: use only the parent's existing page; no browser, context, tab or server lifecycle. */
'use strict';
const fs=require('node:fs'),path=require('node:path'),crypto=require('node:crypto'),assert=require('node:assert/strict');
module.exports=async function({page,baseURL,outDir}){
 const lesson='formal-fairness-starvation',root=__dirname,base=baseURL.endsWith('/')?baseURL:baseURL+'/',oldViewport=page.viewportSize();
 fs.mkdirSync(outDir,{recursive:true});const reportFile=path.join(outDir,'report.json');if(fs.existsSync(reportFile))throw Error('Atlas: output report already exists');
 const begin=Date.now(),budget=15000,report={project:'Atlas',lesson,started_at:new Date().toISOString(),passed:false,budget_ms:budget,base_url:base,source_before:{},source_after:{},checks:[],dom:[],pointer_actions:[],keyboard_actions:[],api_actions:[],faults:[],captures:[],references:[],errors:[],new_browser:0,new_context:0,new_tab:0,new_server:0,new_target_execution:0,cleanup:{routes_removed:false,hooks_restored:false,viewport_restored:false,page_left_open:true}};
 const routes=[],read=n=>fs.readFileSync(path.join(root,n)),sha=b=>crypto.createHash('sha256').update(b).digest('hex'),note=(name,detail=true)=>report.checks.push({name,passed:true,detail});
 const guard=()=>{if(Date.now()-begin>=budget)throw Error('Atlas: 15 second checker budget reached; no retry');};
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
  report.scope='reference delivery supplement only; prior full learning checks and eight images retained';
  report.prior_report='../browser-qa/three-lessons-2026-10-06/runs/formal-fairness-starvation-20261006t201216-full-01/report.json';
  report.prior_report_sha256='8195b986ca30f39f00e3645697745e1d5b2235446b7e08ab322fe613423a08b0';
  preserveInputs(['index.html','lesson.js','style.css','data.js','SKILL.md','inputs/prerequisite-model.py','browser-reference-check.cjs']);
  await viewport(1280,900);await clickedReference('inputs/prerequisite-model.py');await clickedReference('SKILL.md');
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

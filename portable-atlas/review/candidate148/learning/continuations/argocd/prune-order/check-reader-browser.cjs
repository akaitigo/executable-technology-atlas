'use strict';
// rootから専有枠が付与された後だけ手動で実行する。既存browser/profileへ接続しない。
const fs=require('node:fs'),path=require('node:path'),os=require('node:os'),crypto=require('node:crypto'),assert=require('node:assert/strict');
const {pathToFileURL}=require('node:url');
const {chromium}=require('playwright');
const root=__dirname,stamp=new Date().toISOString().replaceAll(':','').replaceAll('.','');
const out=path.join(root,'observations','reader-browser-'+stamp);
const hash=file=>crypto.createHash('sha256').update(fs.readFileSync(file)).digest('hex');
const bound=['index.html','reader-app.js','reader-state.js','reader-data.js','check-reader-browser.cjs','observations/model-check.json','hand-oracle.json','fixtures.json'];
const binding=()=>Object.fromEntries(bound.map(name=>[name,hash(path.join(root,name))]));
fs.mkdirSync(out);const profile=fs.mkdtempSync(path.join(root,'owned-reader-profile-'));
const report={kind:'real-browser-reader-check',started_at_utc:new Date().toISOString(),started_load:os.loadavg(),
  source_before:binding(),checks:[],pointer_actions:[],keyboard_actions:[],captures:[],errors:[],external_requests_blocked:[],
  browser_instances:1,mode:'既存Chromium headless / sandbox有効 / 専用一時profile / file:// / DevTools pipe',
  live_argocd:false,kubernetes:false,docker:false,numerical_model_rerun:false,own_context_closed:false,profile_removed:false};
let context;
const note=(name,detail)=>report.checks.push({name,detail,pass:true});
async function pointer(page,selector){
 const locator=page.locator(selector);await locator.scrollIntoViewIfNeeded();const box=await locator.boundingBox();
 assert.ok(box&&box.width>0&&box.height>0);const x=box.x+box.width/2,y=box.y+box.height/2;
 await page.mouse.move(x,y);await page.mouse.click(x,y);report.pointer_actions.push({selector,x,y,viewport:page.viewportSize()});
}
async function cleared(page,label,predictionsCleared){
 assert.equal(await page.locator('#answer').isVisible(),false);assert.equal(await page.locator('#answer').textContent(),'');
 assert.equal(await page.locator('#plan').isVisible(),false);assert.equal(await page.locator('#answer-button').isDisabled(),true);
 assert.deepEqual(await page.locator('.resource-state').allTextContents(),['未着手','未着手','未着手']);
 assert.ok((await page.locator('.observation').allTextContents()).every(x=>x==='結果・live観測はまだ表示していません。'));
 assert.match(await page.locator('#stage-status').innerText(),/比較前/);
 if(predictionsCleared){assert.equal(await page.locator('input:checked').count(),0);assert.equal(await page.locator('#next').isDisabled(),true);}
 note(label,{stage:0,answer_empty:true,observations_cleared:true,predictions_cleared:predictionsCleared});
}
async function choose(page,id){await pointer(page,`[data-case="${id}"]`);await cleared(page,'場面変更 '+id,true);}
async function run(page,order,stop){
 await pointer(page,`input[name="order"][value="${order}"]`);await pointer(page,`input[name="stop"][value="${stop}"]`);
 let count=0;while(!await page.locator('#next').isDisabled()){assert.ok(count++<6);await pointer(page,'#next');}
 await pointer(page,'#answer-button');assert.equal(await page.locator('#answer').isVisible(),true);
}
async function resource(page,id){return page.locator(`[data-resource="${id}"] .resource-state`).innerText();}
async function noOverflow(page,label){
 const layout=await page.evaluate(()=>({viewport:innerWidth,document:document.documentElement.scrollWidth,
  overflow:[...document.querySelectorAll('main,section,fieldset,.resource,.batch,.case')].filter(e=>{const b=e.getBoundingClientRect();return b.left < -1 || b.right > innerWidth+1;}).map(e=>e.id||e.className)}));
 assert.ok(layout.document<=layout.viewport,JSON.stringify(layout));assert.equal(layout.overflow.length,0,JSON.stringify(layout));note(label,layout);
}
async function capture(page,name,selector=null){
 const file=path.join(out,name+'.png');
 if(selector)await page.locator(selector).screenshot({path:file,animations:'disabled',timeout:10000});
 else await page.screenshot({path:file,fullPage:true,animations:'disabled',timeout:10000});
 report.captures.push({file:path.relative(root,file),sha256:hash(file),viewport:page.viewportSize(),region:selector||'full-page',real_browser_capture:true});
}
(async()=>{
 try{
  context=await chromium.launchPersistentContext(profile,{executablePath:path.join(os.homedir(),'Library/Caches/ms-playwright/chromium_headless_shell-1200/chrome-headless-shell-mac-arm64/chrome-headless-shell'),
    chromiumSandbox:true,headless:true,viewport:{width:1280,height:900},deviceScaleFactor:1,locale:'ja-JP',timezoneId:'Asia/Tokyo',acceptDownloads:false,
    artifactsDir:out,downloadsPath:path.join(out,'downloads'),timeout:15000});
  report.browser_version=context.browser()?.version();
  await context.route('**/*',route=>{const url=route.request().url();if(url.startsWith('file:'))return route.continue();report.external_requests_blocked.push(url);return route.abort();});
  const page=context.pages()[0]||await context.newPage();page.setDefaultTimeout(5000);
  page.on('pageerror',error=>report.errors.push({kind:'pageerror',message:String(error)}));
  await page.goto(pathToFileURL(path.join(root,'index.html')).href,{waitUntil:'load',timeout:10000});
  await cleared(page,'初期表示',true);
  await run(page,'low,mid,high','consumed');
  assert.match(await page.locator('#answer').innerText(),/開始順の予想は一致/);assert.equal(await resource(page,'high'),'Synced');
  assert.match(await page.locator('[data-resource="high"] .observation').innerText(),/未観測/);note('通常apply：開始順と最終Health未観測',true);
  await noOverflow(page,'1280pxのページと主要部品');await capture(page,'desktop-apply-full');
  await pointer(page,'input[name="order"][value="high,mid,low"]');await cleared(page,'開始順の予想変更で結果を初期化',false);
  assert.equal(await page.locator('input[name="order"][value="high,mid,low"]').evaluate(e=>e===document.activeElement),true);
  await page.keyboard.press('ArrowDown');report.keyboard_actions.push({key:'ArrowDown',purpose:'radio変更後のfocus維持と次の選択'});
  assert.equal(await page.locator('input[name="order"]:checked').inputValue(),'low');
  assert.equal(await page.locator('input[name="order"][value="low"]').evaluate(e=>e===document.activeElement),true);
  note('予想radioのfocus維持と実キーボード選択',true);
  await run(page,'high,mid,low','consumed');assert.match(await page.locator('#answer').innerText(),/開始順の予想は不一致/);note('誤った予想は不一致',true);
  await pointer(page,'input[name="stop"][value="wait"]');await cleared(page,'終端予想変更で結果を初期化',false);
  await choose(page,'prune-descending');await run(page,'high,mid,low','consumed');
  assert.deepEqual(await page.locator('[data-resource="high"] .wave-value').allTextContents(),['8','-3']);
  assert.deepEqual(await page.locator('[data-resource="low"] .wave-value').allTextContents(),['-3','8']);
  assert.match(await page.locator('[data-resource="low"] .observation').innerText(),/未観測/);note('逆waveの値と最後の消滅未観測',true);
  await capture(page,'desktop-prune-comparison','#comparison');
  await choose(page,'prune-failed');await run(page,'high,mid','failed');
  assert.equal(await resource(page,'mid'),'SyncFailed');assert.equal(await resource(page,'low'),'未着手');note('途中失敗で後続未着手',true);
  await choose(page,'mixed-same-wave-failed');await run(page,'old','failed');
  assert.equal(await resource(page,'old'),'SyncFailed');assert.equal(await resource(page,'new'),'未着手');assert.equal(await resource(page,'later'),'未着手');
  note('同waveのprune失敗でapplyも未着手',true);await capture(page,'desktop-same-wave-failure','#comparison');
  await pointer(page,'#reset');await cleared(page,'失敗後resetで全状態を初期化',true);
  await choose(page,'apply-ascending');await run(page,'low,mid,high','consumed');assert.match(await page.locator('#stage-status').innerText(),/計画を最後/);
  note('失敗から正常への切替で失敗表示が残らない',true);
  await page.setViewportSize({width:390,height:844});await choose(page,'prune-waiting');await run(page,'high','wait');
  assert.equal(await resource(page,'high'),'Pruned');assert.equal(await resource(page,'mid'),'未着手');assert.equal(await resource(page,'low'),'未着手');
  assert.match(await page.locator('[data-resource="high"] .observation').innerText(),/liveあり・削除中/);
  assert.match(await page.locator('#stage-status').innerText(),/削除待ち/);note('390px：削除待ちと未着手を区別',true);
  await noOverflow(page,'390pxのページと主要部品');
  await capture(page,'mobile-prune-wait-full');await capture(page,'mobile-prune-wait-comparison','#comparison');await capture(page,'mobile-prune-wait-answer','#answer');
  await pointer(page,'#reset');await cleared(page,'390pxのreset後に答えと削除待ちが残らない',true);
  assert.equal(report.errors.length,0,JSON.stringify(report.errors));report.status='pass';
 }catch(error){report.status='fail';report.errors.push({kind:'test_failure',message:String(error.stack||error).replaceAll(os.homedir(),'~')});process.exitCode=1;}
 finally{
  if(context){try{await context.close();report.own_context_closed=true;}catch(error){report.errors.push({kind:'cleanup',message:String(error)});process.exitCode=1;}}
  if(!context||report.own_context_closed){fs.rmSync(profile,{recursive:true,force:true});report.profile_removed=true;}
  report.source_after=binding();report.sources_unchanged=JSON.stringify(report.source_before)===JSON.stringify(report.source_after);
  report.finished_at_utc=new Date().toISOString();report.finished_load=os.loadavg();
  fs.writeFileSync(path.join(out,'report.json'),JSON.stringify(report,null,2)+'\n');
  console.log(JSON.stringify({run:path.relative(root,out),status:report.status,checks:report.checks.length,pointer_actions:report.pointer_actions.length,captures:report.captures.length,own_context_closed:report.own_context_closed,profile_removed:report.profile_removed,errors:report.errors},null,2));
 }
})();

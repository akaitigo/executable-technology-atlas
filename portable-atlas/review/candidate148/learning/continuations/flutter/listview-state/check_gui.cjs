'use strict';
// 枠付与後だけ実行する。通常のブラウザーポインターで保存観測readerを確認。
const fs=require('node:fs'),path=require('node:path'),os=require('node:os');
const crypto=require('node:crypto'),assert=require('node:assert/strict');
const {spawn}=require('node:child_process');
const {chromium}=require('playwright');
const root=__dirname,qa=path.join(root,'ui-qa');fs.mkdirSync(qa,{recursive:true});
const dir=path.join(qa,'run-'+new Date().toISOString().replaceAll(':','').replaceAll('.',''));fs.mkdirSync(dir);
const profile=fs.mkdtempSync(path.join(qa,'owned-profile-'));
const hash=data=>crypto.createHash('sha256').update(data).digest('hex');
const fileNames=['index.html','app.js','style.css','serve.py','check_gui.py','check_gui.cjs'];
const hashes=()=>Object.fromEntries(fileNames.map(name=>[name,hash(fs.readFileSync(path.join(root,name)))]));
const rawPath=path.join(root,'probe/observations/attempt-01/actual.json');
const raw=JSON.parse(fs.readFileSync(rawPath,'utf8'));
const report={startedAt:new Date().toISOString(),kind:'actual_chromium_gui_saved_flutter_reader',flutterLiveExecution:false,
  nativeTestsRepeated:false,modelReconstruction:false,browserSandbox:true,browserInstances:1,ownProfile:true,
  driverNice:os.getPriority(),checks:[],pointerActions:0,screenshots:[],errors:[],externalRequestsBlocked:[],
  sourcesBefore:hashes(),originalObservationSha256:hash(fs.readFileSync(rawPath)),
  browserClosed:false,profileRemoved:false,serverStopped:false,passed:false};
let context,server,url;
const save=()=>fs.writeFileSync(path.join(dir,'report.json'),JSON.stringify(report,null,2)+'\n');
const add=(name,detail)=>report.checks.push({name,passed:true,detail});
const clean=error=>String(error.stack||error).replaceAll(os.homedir(),'~');
async function click(page,selector){await page.locator(selector).click();report.pointerActions++;}
async function hidden(page,selector){assert.equal(await page.locator(selector).isVisible(),false,selector);}
async function shot(page,name,selector){
  const file=path.join(dir,name+'.png');
  if(selector)await page.locator(selector).screenshot({path:file,animations:'disabled',timeout:10000});
  else await page.screenshot({path:file,animations:'disabled',timeout:10000});
  report.screenshots.push({file:name+'.png',sha256:hash(fs.readFileSync(file)),viewport:page.viewportSize(),target:selector||'viewport',kind:'actual_Chromium_capture_of_saved_observation_reader'});
}
async function readRows(page,selector){return page.locator(selector+' .row-card').evaluateAll(cards=>cards.map(card=>({
  itemId:card.querySelector('.row-heading b').textContent.replace('項目 ',''),
  stateId:card.querySelector('.identity').textContent.replace('State ',''),
  mountedFor:card.querySelector('.origin').textContent.replace('生成時：',''),
  count:Number(card.querySelector('.count').firstChild.textContent)})));}
const project=rows=>rows.map(({itemId,stateId,mountedFor,count})=>({itemId,stateId,mountedFor,count}));
async function assertRows(page,condition,phase){
  const measured=raw.cases.find(c=>c.id===condition).stages.find(s=>s.phase===phase);
  assert.deepEqual(await readRows(page,'#selected-rows'),project(measured.rows));
  assert.equal(await page.locator('#raw-observation').textContent(),JSON.stringify(measured,null,2));
}
async function resetState(page,condition,clearPrediction=true){
  await hidden(page,'#answer');await hidden(page,'#comparison');await hidden(page,'#boundary');
  assert.equal(await page.locator('#answer').textContent(),'');
  assert.equal(await page.locator('#answer').getAttribute('data-match'),null);
  assert.equal(await page.locator('#comparison-rows').textContent(),'');
  assert.equal(await page.locator('#reveal').isDisabled(),true);
  assert.equal(await page.locator('#timeline button:enabled').count(),0);
  assert.equal(await page.locator('#phase-label').innerText(),'準備 A=1 / B=2');
  if(clearPrediction)assert.equal(await page.locator('input[name=prediction]:checked').count(),0);
  await assertRows(page,condition,'prepared');
}
async function clearedFailure(page){
  await hidden(page,'#lesson-body');await hidden(page,'#answer');await hidden(page,'#comparison');
  for(const id of ['selected-rows','comparison-rows','answer','raw-observation','source-code','boundary','event-summary','phase-label'])assert.equal(await page.locator('#'+id).textContent(),'');
  assert.equal(await page.locator('#answer').getAttribute('data-match'),null);
  assert.equal(await page.locator('#replay').isDisabled(),true);assert.equal(await page.locator('#reveal').isDisabled(),true);
  assert.equal(await page.locator('#timeline button:enabled').count(),0);
}
async function overflow(page,label){const size=await page.evaluate(()=>({viewport:innerWidth,content:document.documentElement.scrollWidth}));assert.ok(size.content<=size.viewport,JSON.stringify(size));add(label,size);}
async function startServer(){
  server=spawn('/usr/bin/python3',['-B','serve.py','--port','0'],{cwd:root,stdio:['ignore','pipe','pipe']});
  server.stderr.on('data',chunk=>{report.serverStderr=(report.serverStderr||'')+chunk.toString();});
  return new Promise((resolve,reject)=>{const timer=setTimeout(()=>reject(new Error('server 5秒上限')),5000);let output='';
    server.stdout.on('data',chunk=>{output+=chunk.toString();if(output.includes('\n')){clearTimeout(timer);resolve(output.trim().split('\n')[0]);}});
    server.once('error',reject);server.once('exit',code=>{if(!output){clearTimeout(timer);reject(new Error('server exit '+code));}});});
}
async function main(){
 try{
  assert.ok(report.driverNice>=10,'nice10適用必須');url=await startServer();const origin=new URL(url).origin;report.loopbackOrigin=origin;
  context=await chromium.launchPersistentContext(profile,{executablePath:path.join(os.homedir(),'Library/Caches/ms-playwright/chromium_headless_shell-1200/chrome-headless-shell-mac-arm64/chrome-headless-shell'),headless:true,chromiumSandbox:true,viewport:{width:1280,height:900},deviceScaleFactor:1,locale:'ja-JP',timezoneId:'Asia/Tokyo',acceptDownloads:false,timeout:15000,artifactsDir:dir});
  await context.route('**/*',route=>{if(new URL(route.request().url()).origin===origin)return route.continue();report.externalRequestsBlocked.push(route.request().url());return route.abort();});
  const page=context.pages()[0]||await context.newPage();page.setDefaultTimeout(5000);
  page.on('pageerror',error=>report.errors.push({type:'pageerror',message:clean(error)}));
  await page.goto(url,{waitUntil:'load'});await page.waitForSelector('html[data-ready=true]');
  assert.match(await page.locator('.notice').innerText(),/ライブ実行ではありません/);
  await resetState(page,'withLookup');assert.equal(await page.locator('#replay').isDisabled(),true);
  add('読込と未予想時の操作制限','実測と実行時ソースのdigestを照合、予想前は再生不可');await shot(page,'desktop-introduction');
  for(const [condition,prediction] of [['withLookup','follows'],['withoutLookup','fresh']]){
    await click(page,`input[name=condition][value=${condition}]`);await resetState(page,condition);
    await click(page,`input[name=prediction][value=${prediction}]`);await click(page,'#replay');
    for(const phase of ['initial','prepared','reordered','far','returned']){
      await click(page,`#timeline button[data-phase=${phase}]`);await assertRows(page,condition,phase);
      const other=condition==='withLookup'?'withoutLookup':'withLookup';
      assert.deepEqual(await readRows(page,'#comparison-rows'),project(raw.cases.find(c=>c.id===other).stages.find(s=>s.phase===phase).rows));
      if(phase!=='reordered')assert.equal(await page.locator('#reveal').isDisabled(),true);
    }
    await click(page,'#timeline button[data-phase=reordered]');await click(page,'#reveal');
    assert.match(await page.locator('#answer').innerText(),/予想と実測は一致/);
    add(condition+'の5時点・対照・答え合わせ','原票とDOMの項目/State/回数/生成時IDを独立比較');
  }
  await shot(page,'desktop-comparison','#observe');await shot(page,'desktop-answer','#answer-section');
  await click(page,'input[name=prediction][value=position]');await resetState(page,'withoutLookup',false);
  assert.equal(await page.locator('input[name=prediction]:checked').getAttribute('value'),'position');
  await click(page,'#replay');await click(page,'#reveal');assert.match(await page.locator('#answer').innerText(),/異なりました/);
  add('予想変更と不一致の答え','古い一致の答えを消し、新しい予想だけ保持');
  await click(page,'#timeline button[data-phase=returned]');await hidden(page,'#answer');assert.equal(await page.locator('#answer').textContent(),'');
  assert.match(await page.locator('#boundary').innerText(),/新しいState・0回/);await shot(page,'desktop-returned','#observe');
  await click(page,'input[name=condition][value=withLookup]');await resetState(page,'withLookup');add('条件変更で全学習結果reset','予想・再生・対照・答えを消す');
  await click(page,'input[name=prediction][value=follows]');await click(page,'#replay');await click(page,'#reveal');await click(page,'#reset');
  await resetState(page,'withLookup');assert.equal(await page.locator('#replay').isDisabled(),true);add('明示reset','予想も消し準備時点へ戻す');
  await click(page,'#implementation summary');assert.equal(await page.locator('#source-code').textContent(),fs.readFileSync(path.join(root,'probe/observations/attempt-01/inputs/probe/lib/listview_probe.dart'),'utf8'));
  assert.equal(await page.locator('.source-links a').count(),3);await click(page,'#implementation summary');add('実行時ソースと原典','固定snapshotを表示。外部リンクは開かない');
  await overflow(page,'1280pxの横はみ出しなし');
  await page.setViewportSize({width:390,height:844});await click(page,'input[name=prediction][value=follows]');await click(page,'#replay');await click(page,'#reveal');
  await assertRows(page,'withLookup','reordered');await overflow(page,'390pxの横はみ出しなし');
  await shot(page,'mobile-prediction','#predict');await shot(page,'mobile-comparison','#observe');await shot(page,'mobile-answer','#answer-section');add('390pxの実ポインター操作','選択・再生・答え合わせ');
  await page.setViewportSize({width:1280,height:900});
  const pattern='**/probe/observations/attempt-01/actual.json';
  await page.route(pattern,route=>route.fulfill({status:503,body:'temporarily unavailable'}));
  await click(page,'#reload');await page.waitForSelector('html[data-ready=error]');await clearedFailure(page);assert.match(await page.locator('#load-error').innerText(),/503/);await shot(page,'reload-http-failure');
  add('答え表示後の再読込失敗','503をブラウザー応答に注入。原票未変更。古い行/対照/答え/ソースを消す');
  await page.unroute(pattern);await click(page,'#reload');await page.waitForSelector('html[data-ready=true]');await resetState(page,'withLookup');add('失敗後の再試行','新しい正常原票を読み、予想なしの準備時点');
  await page.route(pattern,route=>route.fulfill({status:200,contentType:'application/json',body:'{}'}));
  await click(page,'#reload');await page.waitForSelector('html[data-ready=error]');await clearedFailure(page);assert.match(await page.locator('#load-error').innerText(),/digestが一致しません/);await shot(page,'reload-digest-failure');
  await page.unroute(pattern);await click(page,'#reload');await page.waitForSelector('html[data-ready=true]');add('digest不一致と回復','変更された応答では再生せず、古い実測にも戻らない');
  let held,requests=0,release;
  const heldPromise=new Promise(resolve=>{release=resolve;});
  await page.route(pattern,async route=>{requests++;if(requests===1){held=route;await heldPromise;try{await route.fulfill({status:200,contentType:'application/json',body:'{}'});}catch(error){report.supersededRequest=clean(error);}}else await route.continue();});
  await click(page,'#reload');await page.waitForFunction(()=>document.documentElement.dataset.ready==='loading');
  for(let i=0;!held&&i<20;i++)await new Promise(resolve=>setTimeout(resolve,10));assert.ok(held);await clearedFailure(page);
  await click(page,'#reload');await page.waitForSelector('html[data-ready=true]');release();await page.waitForTimeout(80);
  assert.equal(await page.locator('html').getAttribute('data-ready'),'true');await hidden(page,'#load-error');await resetState(page,'withLookup');await page.unroute(pattern);
  add('連続再読込の古い応答を無視','旧requestの遅れた不一致応答で、新しい成功結果を上書きしない');
  let oldSuccess,successRequests=0,releaseSuccess;
  const successHold=new Promise(resolve=>{releaseSuccess=resolve;});
  await page.route(pattern,async route=>{successRequests++;if(successRequests===1){oldSuccess=route;await successHold;try{await route.fulfill({status:200,contentType:'application/json',body:fs.readFileSync(rawPath,'utf8')});}catch(error){report.supersededSuccess=clean(error);}}else await route.fulfill({status:503,body:'current request unavailable'});});
  await click(page,'#reload');await page.waitForFunction(()=>document.documentElement.dataset.ready==='loading');
  for(let i=0;!oldSuccess&&i<20;i++)await new Promise(resolve=>setTimeout(resolve,10));assert.ok(oldSuccess);
  await click(page,'#reload');await page.waitForSelector('html[data-ready=error]');releaseSuccess();await page.waitForTimeout(80);
  assert.equal(await page.locator('html').getAttribute('data-ready'),'error');await clearedFailure(page);assert.match(await page.locator('#load-error').innerText(),/503/);
  await page.unroute(pattern);await click(page,'#reload');await page.waitForSelector('html[data-ready=true]');await resetState(page,'withLookup');
  add('旧successが後続errorを覆わない','旧requestをAbortし、後続の503を古い正常値で隠さない。復帰後も予想なし');
  const privateResponse=await page.request.get(origin+'/probe/observations/attempt-01/local/package_config.json');assert.equal(privateResponse.status(),404);add('配信範囲制限','SDK/cache参照設定は404');
  assert.equal(report.errors.length,0);assert.equal(report.externalRequestsBlocked.length,0);report.passed=true;
 }catch(error){report.errors.push({type:'test_failure',message:clean(error)});process.exitCode=1;}
 finally{
  if(context){try{await context.close();report.browserClosed=true;}catch(error){report.errors.push({type:'cleanup',message:clean(error)});process.exitCode=1;}}
  if(!context||report.browserClosed){fs.rmSync(profile,{recursive:true,force:true});report.profileRemoved=!fs.existsSync(profile);}
  if(server){if(server.exitCode!==null||server.signalCode!==null)report.serverStopped=true;else{server.kill('SIGTERM');await Promise.race([new Promise(resolve=>server.once('exit',()=>{report.serverStopped=true;resolve();})),new Promise(resolve=>setTimeout(resolve,4000))]);}}
  report.sourcesAfter=hashes();report.sourcesUnchanged=JSON.stringify(report.sourcesBefore)===JSON.stringify(report.sourcesAfter);
  report.originalObservationUnchanged=report.originalObservationSha256===hash(fs.readFileSync(rawPath));
  report.finishedAt=new Date().toISOString();report.passed=report.passed&&report.sourcesUnchanged&&report.originalObservationUnchanged&&report.browserClosed&&report.profileRemoved&&report.serverStopped&&report.errors.length===0;
  save();console.log(JSON.stringify({run:path.relative(root,dir),passed:report.passed,checks:report.checks.length,pointerActions:report.pointerActions,screenshots:report.screenshots.length,browserClosed:report.browserClosed,profileRemoved:report.profileRemoved,serverStopped:report.serverStopped,errors:report.errors},null,2));if(!report.passed)process.exitCode=1;
 }
}
main();

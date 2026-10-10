'use strict';
// Atlas: run only after the shared browser slot has been assigned.
const fs=require('node:fs'),path=require('node:path'),os=require('node:os');
const crypto=require('node:crypto'),assert=require('node:assert/strict');
const {spawn}=require('node:child_process');
const {chromium}=require('playwright');
const root=__dirname,qa=path.join(root,'qa');
const dir=path.join(qa,'run-'+new Date().toISOString().replaceAll(':','').replaceAll('.',''));fs.mkdirSync(dir);
const profile=fs.mkdtempSync(path.join(qa,'owned-profile-'));
const hash=data=>crypto.createHash('sha256').update(data).digest('hex');
const names=['index.html','app.js','style.css','serve.py','check_gui.py','check_gui.cjs'];
const hashes=()=>Object.fromEntries(names.map(name=>[name,hash(fs.readFileSync(path.join(root,name)))]));
const rawPath=path.join(root,'observations/run-01/results.json'),raw=JSON.parse(fs.readFileSync(rawPath,'utf8'));
const measured=new Map([...raw.rows,...raw.outsideGuaranteeExamples].map(row=>[row.id,row]));
const sourcePath=path.join(root,'observations/run-01/inputs/codec.py');
const report={Atlas:'SECDED reader GUI check',startedAt:new Date().toISOString(),kind:'actual_Chromium_capture_of_saved_finite_calculations',realChannelOrHardware:false,
 calculationRepeated:false,browserSandbox:true,browserInstances:1,ownProfile:true,driverNice:os.getPriority(),checks:[],pointerActions:0,keyboardActions:0,screenshots:[],errors:[],externalRequestsBlocked:[],
 sourcesBefore:hashes(),calculationSha256:hash(fs.readFileSync(rawPath)),browserClosed:false,profileRemoved:false,serverStopped:false,passed:false};
let context,server,url;
const add=(name,detail)=>report.checks.push({name,passed:true,detail});
const clean=e=>String(e.stack||e).replaceAll(os.homedir(),'~');
async function click(page,selector){await page.locator(selector).click();report.pointerActions++;}
async function typeMessage(page,text){await click(page,'#message');await page.keyboard.press('Meta+A');await page.keyboard.type(text);report.keyboardActions+=2;}
async function hidden(page,selector){assert.equal(await page.locator(selector).isVisible(),false,selector);}
async function shot(page,name,selector){
 const file=path.join(dir,name+'.png');
 if(selector)await page.locator(selector).screenshot({path:file,animations:'disabled',timeout:10000});
 else await page.screenshot({path:file,animations:'disabled',timeout:10000});
 report.screenshots.push({file:name+'.png',sha256:hash(fs.readFileSync(file)),viewport:page.viewportSize(),target:selector||'viewport',kind:'actual_Chromium_capture_of_saved_calculation_reader'});
}
async function cleared(page,clearPrediction=true){
 await hidden(page,'#result');await hidden(page,'#answer');
 for(const id of ['checks','decision','bit-results','comparison-content','calculation-json','answer'])assert.equal(await page.locator('#'+id).textContent(),'');
 assert.equal(await page.locator('#decision').getAttribute('data-action'),null);assert.equal(await page.locator('#comparison-content').getAttribute('data-available'),null);
 for(const attr of ['data-match','data-outcome'])assert.equal(await page.locator('#answer').getAttribute(attr),null);
 assert.equal(await page.locator('#reveal').isDisabled(),true);assert.equal(await page.locator('tr.active').count(),0);
 if(clearPrediction)assert.equal(await page.locator('input[name=prediction]:checked').count(),0);
}
async function failed(page){
 await cleared(page);await hidden(page,'#lesson-body');
 for(const id of ['source-code','coverage-summary'])assert.equal(await page.locator('#'+id).textContent(),'');
 assert.equal(await page.locator('#replay').isDisabled(),true);
}
async function readBits(page,selector){return (await page.locator(selector+' .bit .value').allTextContents()).join('');}
async function rowMatches(page,message,errors){
 const key='secded8/'+message+'/'+(errors.join(',')||'-'),row=measured.get(key),d=row.decoder;assert.ok(row,key);
 assert.deepEqual(await page.locator('#checks b').allTextContents(),[`${d.syndromeBits} = ${d.syndrome}`,String(d.overall),d.flip===null?'なし':String(d.flip)]);
 assert.equal(await page.locator('#decision').getAttribute('data-action'),d.action);
 assert.equal(await readBits(page,'[data-kind=sent]'),row.sent);assert.equal(await readBits(page,'[data-kind=received]'),d.received);
 if(d.corrected===null){assert.equal(await page.locator('[data-kind=corrected] .bit').count(),0);assert.match(await page.locator('[data-kind=corrected]').innerText(),/値を返しません/);}
 else assert.equal(await readBits(page,'[data-kind=corrected]'),d.corrected);
 assert.equal(await page.locator('#calculation-json').textContent(),JSON.stringify(row,null,2));
 const control=measured.get('hamming7/'+message+'/'+(errors.join(',')||'-'));
 if(control){assert.equal(await page.locator('#comparison-content').getAttribute('data-available'),'true');assert.equal(await readBits(page,'[data-kind=control-received]'),control.decoder.received);assert.equal(await page.locator('.control-output').textContent(),`返す4bit：${control.decoder.decoded} ／ 処理後シンドローム：${control.decoder.postSyndrome}`);}
 else {assert.equal(await page.locator('#comparison-content').getAttribute('data-available'),'false');assert.equal(await page.locator('[data-kind=control-received]').count(),0);}
 assert.equal(await page.locator('tr.active').getAttribute('data-action'),d.action);return row;
}
async function show(page,preset,message,prediction){
 if(await page.locator('#message').inputValue()!==message)await typeMessage(page,message);
 await click(page,`button[data-preset=${preset}]`);await cleared(page);await click(page,`input[name=prediction][value=${prediction}]`);await click(page,'#replay');
}
async function answerMatches(page,row,prediction){
 await click(page,'#reveal');const truth=row.answerCheck.matchesOriginal,outcome=truth===null?'withhold':truth?'recover':'wrong';
 assert.equal(await page.locator('#answer').getAttribute('data-outcome'),outcome);assert.equal(await page.locator('#answer').getAttribute('data-match'),String(outcome===prediction));
}
async function overflow(page,label){const size=await page.evaluate(()=>({viewport:innerWidth,content:document.documentElement.scrollWidth}));assert.ok(size.content<=size.viewport,JSON.stringify(size));add(label,size);}
async function startServer(){
 server=spawn('/usr/bin/python3',['-B','serve.py','--port','0'],{cwd:root,stdio:['ignore','pipe','pipe']});
 server.stderr.on('data',b=>report.serverStderr=(report.serverStderr||'')+b.toString());
 return new Promise((resolve,reject)=>{let output='';const timer=setTimeout(()=>reject(new Error('Server startup timeout')),5000);
 server.stdout.on('data',b=>{output+=b.toString();if(output.includes('\n')){clearTimeout(timer);resolve(output.trim().split('\n')[0]);}});server.once('error',reject);server.once('exit',code=>{if(!output){clearTimeout(timer);reject(new Error('Server exit '+code));}});});
}
async function main(){
 const deadline=setTimeout(()=>{report.errors.push({type:'timeout',message:'Atlas GUI batch exceeded 90 seconds'});if(context)context.close().catch(()=>{});if(server)server.kill('SIGTERM');},90000);deadline.unref();
 try{
  assert.ok(report.driverNice>=10,'nice 10 mandatory');url=await startServer();const origin=new URL(url).origin;report.loopbackOrigin=origin;
  context=await chromium.launchPersistentContext(profile,{executablePath:path.join(os.homedir(),'Library/Caches/ms-playwright/chromium_headless_shell-1200/chrome-headless-shell-mac-arm64/chrome-headless-shell'),headless:true,chromiumSandbox:true,viewport:{width:1280,height:900},deviceScaleFactor:1,locale:'ja-JP',timezoneId:'Asia/Tokyo',acceptDownloads:false,timeout:15000,artifactsDir:dir});
  await context.route('**/*',route=>{if(new URL(route.request().url()).origin===origin)return route.continue();report.externalRequestsBlocked.push(route.request().url());return route.abort();});
  const page=context.pages()[0]||await context.newPage();page.setDefaultTimeout(5000);page.on('pageerror',e=>report.errors.push({type:'pageerror',message:clean(e)}));
  await page.goto(url,{waitUntil:'load'});await page.waitForSelector('html[data-ready=true]');await cleared(page);assert.equal(await page.locator('#replay').isDisabled(),true);
  assert.match(await page.locator('header').innerText(),/Atlas/);assert.match(await page.locator('.notice').innerText(),/有限な模型/);assert.match(await page.locator('.notice').innerText(),/保存した計算結果/);
  add('読込と予想前の制限','計算と実行時実装をhash照合。readerと実通信を区別');await shot(page,'desktop-introduction');
  const cases=[['none','1011',[],'recover'],['data','1011',[6],'recover'],['parity','1011',[1],'recover'],['overall','1011',[8],'recover'],['double','0000',[1,2],'withhold'],['double8','0000',[3,8],'withhold']];
  for(const [preset,message,errors,prediction] of cases){await show(page,preset,message,prediction);const row=await rowMatches(page,message,errors);await answerMatches(page,row,prediction);add(preset+'の計算表示',row.id);if(['data','overall','double','double8'].includes(preset))await shot(page,'desktop-'+preset,'#observe');}
  await click(page,'#outside-options summary');
  for(const [preset,errors] of [['triple',[1,2,3]],['quad',[1,2,3,8]]]){
   await show(page,preset,'0000','wrong');const row=await rowMatches(page,'0000',errors);await answerMatches(page,row,'wrong');assert.equal(await page.locator('#guarantee-note').getAttribute('data-outside'),'true');assert.match(await page.locator('#answer').innerText(),/1000/);
   add('保証外 '+preset,row.id);await shot(page,'desktop-'+preset,'#observe');await shot(page,'answer-'+preset,'#answer-section');
  }
  await click(page,'input[name=prediction][value=recover]');await cleared(page,false);assert.equal(await page.locator('input[name=prediction]:checked').getAttribute('value'),'recover');
  await click(page,'#replay');const quad=await rowMatches(page,'0000',[1,2,3,8]);await answerMatches(page,quad,'recover');assert.match(await page.locator('#answer').innerText(),/異なりました/);add('予想変更と不一致','古い答えを消し、新しい予想だけ保持');
  await click(page,'button[data-preset=none]');await cleared(page);assert.equal(await page.locator('#guarantee-note').getAttribute('data-outside'),'false');
  await typeMessage(page,'10x');await cleared(page);assert.match(await page.locator('#input-error').innerText(),/0と1を4文字/);assert.equal(await page.locator('#replay').isDisabled(),true);
  await typeMessage(page,'1111');await click(page,'input[name=errors][value="4"]');await click(page,'input[name=errors][value="7"]');await click(page,'input[name=prediction][value=withhold]');await click(page,'#replay');const custom=await rowMatches(page,'1111',[4,7]);await answerMatches(page,custom,'withhold');
  await click(page,'input[name=errors][value="5"]');await cleared(page);assert.match(await page.locator('#input-error').innerText(),/0〜2箇所/);assert.equal(await page.locator('#replay').isDisabled(),true);
  await click(page,'input[name=errors][value="5"]');await hidden(page,'#input-error');await click(page,'input[name=prediction][value=withhold]');await click(page,'#replay');await rowMatches(page,'1111',[4,7]);await click(page,'#reveal');await click(page,'#reset');await cleared(page);assert.equal(await page.locator('#replay').isDisabled(),true);
  add('入力失敗・回復・明示reset','非2進文字と3箇所選択を拒否し、古い列と答えを消す。正常条件へ回復');
  await click(page,'#implementation summary');assert.equal(await page.locator('#source-code').textContent(),fs.readFileSync(sourcePath,'utf8'));assert.equal(await page.locator('.source-links a').count(),2);await shot(page,'desktop-source','#sources');await click(page,'#implementation summary');add('一次資料と実行時実装','保存した実装と全文一致。外部リンクは開かない');
  await overflow(page,'1280pxの横はみ出しなし');await page.setViewportSize({width:390,height:844});
  await show(page,'double','0000','withhold');const mobile=await rowMatches(page,'0000',[1,2]);await answerMatches(page,mobile,'withhold');await overflow(page,'390pxの横はみ出しなし');
  await shot(page,'mobile-prediction','#predict');await shot(page,'mobile-double','#observe');await shot(page,'mobile-answer','#answer-section');add('390pxの操作','文字入力・条件・予想・表示・答えを実ポインターとキーで操作');
  await page.setViewportSize({width:1280,height:900});const pattern='**/observations/run-01/results.json';
  await page.route(pattern,route=>route.fulfill({status:503,body:'unavailable'}));await click(page,'#reload');await page.waitForSelector('html[data-ready=error]');await failed(page);assert.match(await page.locator('#load-error').innerText(),/503/);await shot(page,'reload-http-failure');add('成功から取得失敗','503時に以前の列・対照・答え・実装を消す');
  await page.unroute(pattern);await click(page,'#reload');await page.waitForSelector('html[data-ready=true]');await cleared(page);add('取得失敗からの回復','予想なしで再開');
  await show(page,'data','1011','recover');await answerMatches(page,await rowMatches(page,'1011',[6]),'recover');
  await page.route(pattern,route=>route.fulfill({status:200,contentType:'application/json',body:'{}'}));await click(page,'#reload');await page.waitForSelector('html[data-ready=error]');await failed(page);assert.match(await page.locator('#load-error').innerText(),/計算時のものと一致しません/);await shot(page,'reload-digest-failure');
  await page.unroute(pattern);await click(page,'#reload');await page.waitForSelector('html[data-ready=true]');await cleared(page);add('内容不一致と回復','変わった応答を使わず、保存した計算は不変');
  for(const oldKind of ['error','success']){
   let held,requests=0,release;const hold=new Promise(resolve=>release=resolve);
   await page.route(pattern,async route=>{requests++;if(requests===1){held=route;await hold;try{await route.fulfill(oldKind==='error'?{status:503,body:'old error'}:{status:200,contentType:'application/json',body:fs.readFileSync(rawPath,'utf8')});}catch(e){report['superseded_'+oldKind]=clean(e);}}else if(oldKind==='error')await route.continue();else await route.fulfill({status:503,body:'current error'});});
   await click(page,'#reload');await page.waitForSelector('html[data-ready=loading]');for(let i=0;!held&&i<20;i++)await new Promise(r=>setTimeout(r,10));assert.ok(held);await failed(page);
   await click(page,'#reload');await page.waitForSelector(oldKind==='error'?'html[data-ready=true]':'html[data-ready=error]');release();await page.waitForTimeout(100);
   assert.equal(await page.locator('html').getAttribute('data-ready'),oldKind==='error'?'true':'error');if(oldKind==='error'){await cleared(page);await hidden(page,'#load-error');}else{await failed(page);assert.match(await page.locator('#load-error').innerText(),/503/);}
   await page.unroute(pattern);await click(page,'#reload');await page.waitForSelector('html[data-ready=true]');await cleared(page);add('旧'+oldKind+'が後続応答を覆わない','Abortを含む通常経路。generationだけを単独強制する試験ではない');
  }
  assert.equal((await page.request.get(origin+'/expected.json')).status(),404);add('配信範囲','許可した教材ファイルだけ配信');
  assert.equal(report.errors.length,0);assert.equal(report.externalRequestsBlocked.length,0);report.passed=true;
 }catch(e){report.errors.push({type:'test_failure',message:clean(e)});process.exitCode=1;}
 finally{
  clearTimeout(deadline);
  if(context){try{await context.close();report.browserClosed=true;}catch(e){report.errors.push({type:'cleanup',message:clean(e)});}}
  if(!context||report.browserClosed){fs.rmSync(profile,{recursive:true,force:true});report.profileRemoved=!fs.existsSync(profile);}
  if(server){if(server.exitCode!==null||server.signalCode!==null)report.serverStopped=true;else{server.kill('SIGTERM');await Promise.race([new Promise(resolve=>server.once('exit',()=>{report.serverStopped=true;resolve();})),new Promise(resolve=>setTimeout(resolve,4000))]);}}
  report.sourcesAfter=hashes();report.sourcesUnchanged=JSON.stringify(report.sourcesBefore)===JSON.stringify(report.sourcesAfter);report.calculationUnchanged=report.calculationSha256===hash(fs.readFileSync(rawPath));
  report.finishedAt=new Date().toISOString();report.passed=report.passed&&report.sourcesUnchanged&&report.calculationUnchanged&&report.browserClosed&&report.profileRemoved&&report.serverStopped&&report.errors.length===0;
  fs.writeFileSync(path.join(dir,'report.json'),JSON.stringify(report,null,2)+'\n');console.log(JSON.stringify({Atlas:'SECDED GUI',run:path.relative(root,dir),passed:report.passed,checks:report.checks.length,pointerActions:report.pointerActions,screenshots:report.screenshots.length,browserClosed:report.browserClosed,profileRemoved:report.profileRemoved,serverStopped:report.serverStopped,errors:report.errors},null,2));if(!report.passed)process.exitCode=1;
 }
}
main();

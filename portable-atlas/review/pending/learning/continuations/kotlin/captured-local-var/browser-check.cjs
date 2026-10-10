"use strict";
// Only the owned static server and existing Chromium/Playwright are used. No compiler or JVM.
const fs=require("node:fs"),path=require("node:path"),os=require("node:os"),http=require("node:http"),crypto=require("node:crypto"),assert=require("node:assert/strict");
const {chromium}=require('playwright');
const root=__dirname,stamp=new Date().toISOString().replaceAll(":","").replaceAll(".","");
const out=path.join(root,"browser-qa","run-"+stamp);fs.mkdirSync(out,{recursive:true});
const profile=fs.mkdtempSync(path.join(out,"owned-profile-"));
const reportName="observations/20261006T062456931814Z/run.json";
const original=JSON.parse(fs.readFileSync(path.join(root,reportName),"utf8"));
const hash=file=>crypto.createHash("sha256").update(fs.readFileSync(file)).digest("hex");
const sourceFiles=["index.html","lesson.js","browser-check.cjs","expected.json",reportName];
const binding=()=>Object.fromEntries(sourceFiles.map(n=>[n,hash(path.join(root,n))]));
const record={started_at:new Date().toISOString(),real_browser:true,native_compiler_execution:false,source_before:binding(),checks:[],pointer_actions:[],captures:[],controlled_faults:[],blocked_requests:[],errors:[],browser_closed:false,own_profile_removed:false,own_server_closed:false,visual_review:"not performed by this script"};
let context,server,origin,held=[],nextHeldResolve=null,fault="pass";
const note=(label,detail)=>record.checks.push({label,passed:true,detail});
async function pointer(page,selector){
 const item=page.locator(selector);await item.scrollIntoViewIfNeeded();const b=await item.boundingBox();assert.ok(b);
 const x=b.x+b.width/2,y=b.y+b.height/2;await page.mouse.move(x,y);await page.mouse.click(x,y);
 record.pointer_actions.push({selector,x,y,viewport:page.viewportSize()});
}
async function hiddenAndEmpty(page){
 assert.equal(await page.locator("#result").isVisible(),false);
 assert.equal(await page.locator("#answer").isVisible(),false);
 for(const selector of ["#raw","#output","#verdict","#explanation","#comparison"])assert.equal(await page.locator(selector).textContent(),"",selector);
 assert.equal(await page.locator("#raw-details").getAttribute("open"),null);
 assert.equal(await page.locator("#answer-button").isDisabled(),true);
}
async function choose(page,op,input,prediction){
 await pointer(page,'button[data-case="'+op+'"]');await hiddenAndEmpty(page);
 assert.equal(await page.locator('input[name="prediction"]:checked').count(),0);
 if(!op.endsWith("-rejected"))await pointer(page,'input[name="input"][value="'+input+'"]');
 await pointer(page,'input[name="prediction"][value="'+prediction+'"]');
}
async function load(page){
 await pointer(page,"#load");await page.locator("#result").waitFor({state:"visible"});
 assert.equal(await page.locator("#answer").isVisible(),false);
}
async function inspect(page,op,input){
 await pointer(page,"#raw-details summary");
 const actual=JSON.parse(await page.locator("#raw").innerText());
 const compile=original.compiles.find(r=>r.id===(op.endsWith("-rejected")?op:"local-control-and-snapshot"));
 const runtime=op.endsWith("-rejected")?null:original.runs.find(r=>r.mode===op&&r.input===input);
 assert.deepEqual(actual,{compile,runtime});
 const chosen=await page.locator('input[name="input"]:checked').inputValue();
 const rows=await page.locator("#comparison tr").evaluateAll(items=>items.map(row=>[...row.cells].map(cell=>cell.textContent)));
 const table=chosen==="ada"?[
  ["変更のないlocal var / Ada","正常終了 ／ RESULT=3 ／ CONTROL_FINAL=Ada"],
  ["書換前のval snapshot / Ada","正常終了 ／ SNAPSHOT=Ada ／ CAPTURED_NOW=<null> ／ RESULT=3"],
  ["書換後のlocalを直接利用","compile拒否・runtimeなし"]
 ]:[
  ["変更のないlocal var / null","正常終了 ／ RESULT=SKIPPED ／ CONTROL_FINAL=<null>"],
  ["書換前のval snapshot / null","正常終了 ／ SNAPSHOT=<null> ／ CAPTURED_NOW=Ada ／ RESULT=SKIPPED"],
  ["書換後のlocalを直接利用","compile拒否・runtimeなし"]
 ];
 assert.deepEqual(rows,table);
 return actual;
}
async function overflow(page,label){
 const dims=await page.evaluate(()=>({viewport:innerWidth,width:document.documentElement.scrollWidth,outside:[...document.querySelectorAll("main,section,fieldset,button,.result-grid,pre")].filter(e=>{if(!e.getClientRects().length)return false;const b=e.getBoundingClientRect();return b.left< -1||b.right>innerWidth+1;}).map(e=>e.id||e.className)}));
 assert.ok(dims.width<=dims.viewport,JSON.stringify(dims));assert.equal(dims.outside.length,0,JSON.stringify(dims));note(label,dims);
}
async function shot(page,name,fullPage=false){
 const file=path.join(out,name+".png");await page.screenshot({path:file,fullPage,animations:"disabled",timeout:10000});
 const bytes=fs.readFileSync(file);record.captures.push({path:path.relative(root,file),sha256:hash(file),viewport:page.viewportSize(),full_page:fullPage,width:bytes.readUInt32BE(16),height:bytes.readUInt32BE(20)});
}
async function holdNext(page,delayedError=false){
 fault=delayedError?"hold-error":"hold";const ready=new Promise(resolve=>{nextHeldResolve=resolve;});await pointer(page,"#load");await ready;fault="pass";
}
async function releaseLast(){
 const item=held.shift();assert.ok(item);item.release();await item.finished;
}
(async()=>{
try{
 server=http.createServer((req,res)=>{
  try{
   const requested=decodeURIComponent(new URL(req.url,"http://localhost").pathname);
   const file=path.resolve(root,"."+requested+(requested==="/"?"index.html":""));
   if(file!==root&&!file.startsWith(root+path.sep)){res.writeHead(403);res.end();return;}
   if(!fs.existsSync(file)||!fs.statSync(file).isFile()){res.writeHead(404);res.end();return;}
   const mime={".html":"text/html; charset=utf-8",".js":"text/javascript; charset=utf-8",".json":"application/json; charset=utf-8",".md":"text/plain; charset=utf-8",".kt":"text/plain; charset=utf-8"}[path.extname(file)]||"application/octet-stream";
   res.writeHead(200,{"Content-Type":mime,"Cache-Control":"no-store"});res.end(fs.readFileSync(file));
  }catch(error){res.writeHead(500);res.end();}
 });
 await new Promise((resolve,reject)=>{server.once("error",reject);server.listen(0,"127.0.0.1",resolve);});
 origin="http://127.0.0.1:"+server.address().port;record.owned_loopback_origin=origin;
 context=await chromium.launchPersistentContext(profile,{
  executablePath:path.join(os.homedir(),"Library/Caches/ms-playwright/chromium_headless_shell-1200/chrome-headless-shell-mac-arm64/chrome-headless-shell"),
  headless:true,chromiumSandbox:true,viewport:{width:1280,height:900},deviceScaleFactor:1,locale:"ja-JP",timezoneId:"Asia/Tokyo",acceptDownloads:false,
  timeout:15000,downloadsPath:path.join(out,"downloads"),artifactsDir:out});
 record.browser_version=context.browser()?.version()||"persistent context";
 await context.route("**/*",async route=>{
  const url=route.request().url();
  if(!url.startsWith(origin+"/")){record.blocked_requests.push(url);await route.abort();return;}
  if(url.endsWith("/"+reportName)){
   if(fault==="http"){record.controlled_faults.push({kind:"HTTP503",url:reportName});await route.fulfill({status:503,body:"controlled unavailable"});return;}
   if(fault==="digest"){record.controlled_faults.push({kind:"digest mismatch",url:reportName});await route.fulfill({status:200,contentType:"application/json",body:"{}"});return;}
   if(fault==="hold"||fault==="hold-error"){
    const delayedError=fault==="hold-error";
    const item={};item.finished=new Promise(resolve=>{item.finish=resolve;});
    held.push(item);const release=new Promise(resolve=>{item.release=resolve;});nextHeldResolve?.();nextHeldResolve=null;
    await release;try{await route.fulfill({status:delayedError?503:200,contentType:"application/json",body:delayedError?"controlled delayed error":fs.readFileSync(path.join(root,reportName))});}
    catch(error){item.cancelled_delivery=String(error).slice(0,200);}
    record.controlled_faults.push({kind:delayedError?"delayed error released":"delayed response released",cancelled_delivery:item.cancelled_delivery||null});item.finish();return;
   }
  }
  await route.continue();
 });
 const page=context.pages()[0]||await context.newPage();page.setDefaultTimeout(5000);
 page.on("pageerror",error=>record.errors.push({kind:"pageerror",message:String(error)}));
 await page.goto(origin+"/",{waitUntil:"load",timeout:10000});
 await hiddenAndEmpty(page);assert.equal(await page.locator("#load").isDisabled(),true);note("予想前は保存結果・答えを表示せず読取ボタン無効",true);
 const order=await page.locator("section h2").allTextContents();
 assert.match(order[0],/^1\./);assert.match(order[1],/^2\./);assert.match(order[2],/^3\./);assert.match(order[3],/^4\./);note("読む順番：予想→保存原票と正常/異常比較→原典/実装→答え/限界",order);
 for(const op of ["local-control","captured-snapshot"]){
  for(const input of ["ada","null"]){
   const kind="runtime-normal";
   await choose(page,op,input,kind);await load(page);const actual=await inspect(page,op,input);
   await pointer(page,"#answer-button");assert.match(await page.locator("#verdict").innerText(),/は一致/);
   assert.equal(await page.locator("#load-error").isVisible(),false);
   assert.equal(await page.locator("#runtime-result").innerText(),"正常終了");
   note(op+"/"+input+"：実pointer操作・元原票一致・段階/予想照合",{exit:actual.runtime.exit_code});
  }
 }
 for(const op of ["captured-write-rejected"]){
  await choose(page,op,"ada","compile-rejection");
  assert.equal(await page.locator("#input-fieldset").evaluate(fieldset=>fieldset.disabled),true);
  assert.equal(await page.locator('input[name="input"][value="ada"]').isDisabled(),true);
  assert.equal(await page.locator('input[name="input"][value="null"]').isDisabled(),true);
  await load(page);const actual=await inspect(page,op,"ada");await pointer(page,"#answer-button");assert.match(await page.locator("#verdict").innerText(),/は一致/);
  assert.equal(await page.locator("#runtime-result").innerText(),"実行していない");assert.equal(actual.compile.artifact_created,false);
  note(op+"：拒否後のruntimeを作らずJARなしを表示",true);
 }
 await pointer(page,'input[name="prediction"][value="runtime-normal"]');await hiddenAndEmpty(page);note("予想変更で旧結果・原票・答えを消去",true);
 await load(page);await pointer(page,"#answer-button");assert.match(await page.locator("#verdict").innerText(),/は異なりました/);note("異なる予想は不一致と表示",true);
 await choose(page,"captured-snapshot","ada","runtime-normal");await load(page);await pointer(page,"#answer-button");
 await overflow(page,"1280px：横はみ出しなし");await shot(page,"desktop-snapshot-full",true);
 await page.locator("#result .result-grid").scrollIntoViewIfNeeded();await shot(page,"desktop-snapshot-result");
 await page.locator("#answer-section").scrollIntoViewIfNeeded();await shot(page,"desktop-snapshot-answer");
 await choose(page,"captured-write-rejected","ada","compile-rejection");await load(page);
 fault="http";await pointer(page,"#load");await page.locator("#load-error").waitFor({state:"visible"});
 await hiddenAndEmpty(page);assert.match(await page.locator("#load-error").innerText(),/HTTP 503/);
 assert.match(await page.locator("#load-error").innerText(),/NPEの観測ではありません/);note("HTTP取得失敗はcompile拒否と分離・直前結果を消去",true);
 await page.locator("#operation-section").scrollIntoViewIfNeeded();await shot(page,"desktop-acquisition-error");
 fault="digest";await pointer(page,"#load");await page.locator("#load-error").waitFor({state:"visible"});
 await hiddenAndEmpty(page);assert.match(await page.locator("#load-error").innerText(),/SHA-256/);note("取得できてもdigest不一致なら結果へ変換しない",true);
 fault="pass";await load(page);assert.equal(await page.locator("#load-error").isVisible(),false);note("取得復帰後は正規原票から再表示",true);
 await pointer(page,"#reset");await hiddenAndEmpty(page);assert.equal(await page.locator("#load-error").isVisible(),false);assert.equal(await page.locator('input[name="prediction"]:checked').count(),0);
 assert.equal(await page.locator('button[data-case="local-control"]').getAttribute("aria-pressed"),"true");assert.equal(await page.locator("#load").isDisabled(),true);note("resetで条件・予想・エラー・結果を初期化",true);
 await choose(page,"local-control","ada","runtime-normal");await holdNext(page);await pointer(page,"#reset");await releaseLast();await page.waitForTimeout(150);
 await hiddenAndEmpty(page);assert.equal(await page.locator("#load").isDisabled(),true);note("読込み中reset：遅延した旧応答を表示しない",true);
 await choose(page,"local-control","ada","runtime-normal");await holdNext(page);
 await choose(page,"captured-snapshot","null","runtime-normal");await load(page);await inspect(page,"captured-snapshot","null");await releaseLast();await page.waitForTimeout(150);
 assert.deepEqual(JSON.parse(await page.locator("#raw").textContent()).runtime,original.runs.find(r=>r.mode==="captured-snapshot"&&r.input==="null"));
 note("読込み中に条件変更：新条件表示後の旧応答でも上書きしない",true);
 await holdNext(page,true);await choose(page,"local-control","null","runtime-normal");await load(page);await inspect(page,"local-control","null");
 await releaseLast();await page.waitForTimeout(150);assert.equal(await page.locator("#load-error").isVisible(),false);assert.equal(await page.locator("#result").isVisible(),true);
 assert.deepEqual(JSON.parse(await page.locator("#raw").textContent()).runtime,original.runs.find(r=>r.mode==="local-control"&&r.input==="null"));
 note("旧遅延errorが新条件の正常取得を消さない",true);
 await holdNext(page);await pointer(page,'input[name="prediction"][value="runtime-npe"]');await releaseLast();await page.waitForTimeout(150);
 await hiddenAndEmpty(page);assert.equal(await page.locator("#load").isDisabled(),false);note("読込み中に予想変更：遅延した旧応答で答えを復活させない",true);
 await page.setViewportSize({width:390,height:844});
 await choose(page,"captured-write-rejected","ada","compile-rejection");await load(page);await inspect(page,"captured-write-rejected","ada");await pointer(page,"#raw-details summary");await pointer(page,"#answer-button");
 await overflow(page,"390px：横はみ出しなし");await shot(page,"mobile-refusal-full",true);
 await page.locator("#result .result-grid").scrollIntoViewIfNeeded();await shot(page,"mobile-refusal-result");
 await page.locator("#answer-section").scrollIntoViewIfNeeded();await shot(page,"mobile-refusal-answer");
 await choose(page,"captured-snapshot","ada","runtime-normal");await load(page);await pointer(page,"#answer-button");assert.equal(await page.locator("#runtime-result").innerText(),"正常終了");note("390pxでも実pointerでsnapshotの正常終了と答えを表示",true);
 await pointer(page,"#reset");await hiddenAndEmpty(page);note("390pxでもreset後に古い結果を残さない",true);
 assert.equal(record.errors.length,0);record.passed=true;
}catch(error){record.passed=false;record.errors.push({kind:"test-failure",message:String(error.stack||error).replaceAll(os.homedir(),"~")});process.exitCode=1;}
finally{
 for(const item of held)item.release?.();
 if(context){try{await context.close();record.browser_closed=true;}catch(error){record.errors.push({kind:"close",message:String(error)});process.exitCode=1;}}
 if(!context||record.browser_closed){fs.rmSync(profile,{recursive:true,force:true});record.own_profile_removed=true;}
 if(server){await new Promise(resolve=>{server.close(()=>{record.own_server_closed=true;resolve();});server.closeAllConnections?.();});}
 record.source_after=binding();record.sources_unchanged=JSON.stringify(record.source_before)===JSON.stringify(record.source_after);
 record.finished_at=new Date().toISOString();fs.writeFileSync(path.join(out,"report.json"),JSON.stringify(record,null,2)+"\n");
 console.log(JSON.stringify({report:path.relative(root,path.join(out,"report.json")),passed:record.passed,checks:record.checks.length,pointer_actions:record.pointer_actions.length,captures:record.captures.length,browser_closed:record.browser_closed,own_server_closed:record.own_server_closed,own_profile_removed:record.own_profile_removed,errors:record.errors},null,2));
}
})();

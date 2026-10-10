"use strict";
// Owned loopback + sandboxed existing Chromium only. No Kotlin/JVM execution.
const fs=require("node:fs"),path=require("node:path"),os=require("node:os"),http=require("node:http"),crypto=require("node:crypto"),assert=require("node:assert/strict");
const {chromium}=require('playwright');
const root=__dirname,stamp=new Date().toISOString().replaceAll(":","").replaceAll(".","");
const out=path.join(root,"browser-qa","run-"+stamp);fs.mkdirSync(out,{recursive:true});
const profile=fs.mkdtempSync(path.join(out,"owned-profile-"));
const reportName="evidence/evidence/diagnostics/java-nullability-enhancement-process-pilot.json";
const expectedName="evidence/labs/java-nullability-enhancement-process-pilot/expected.json";
const original=JSON.parse(fs.readFileSync(path.join(root,reportName),"utf8"));
const hash=file=>crypto.createHash("sha256").update(fs.readFileSync(file)).digest("hex");
const sourceFiles=["index.html","lesson.mjs","evidence-model.mjs","browser-check.cjs","provenance.json",reportName,expectedName];
const binding=()=>Object.fromEntries(sourceFiles.map(n=>[n,hash(path.join(root,n))]));
const record={started_at:new Date().toISOString(),real_browser:true,native_compiler_execution:false,source_before:binding(),checks:[],pointer_actions:[],captures:[],controlled_faults:[],blocked_requests:[],errors:[],browser_closed:false,own_profile_removed:false,own_server_closed:false,visual_review:"not performed by script"};
let context,server,origin,held=[],nextHeldResolve=null,fault="pass";
const note=(label,detail)=>record.checks.push({label,passed:true,detail});
async function pointer(page,selector){const item=page.locator(selector);await item.scrollIntoViewIfNeeded();const b=await item.boundingBox();assert.ok(b);const x=b.x+b.width/2,y=b.y+b.height/2;await page.mouse.move(x,y);await page.mouse.click(x,y);record.pointer_actions.push({selector,x,y,viewport:page.viewportSize()});}
async function hiddenAndEmpty(page){
 for(const id of ["result","answer"])assert.equal(await page.locator("#"+id).isVisible(),false);
 for(const id of ["raw","record","expected","digest-note","verdict","explanation","comparison"])assert.equal(await page.locator("#"+id).textContent(),"");
 assert.equal(await page.locator("#raw-details").getAttribute("open"),null);assert.equal(await page.locator("#answer-button").isDisabled(),true);
}
async function choose(page,id,prediction){await pointer(page,'button[data-case="'+id+'"]');await hiddenAndEmpty(page);assert.equal(await page.locator('input[name="prediction"]:checked').count(),0);await pointer(page,'input[name="prediction"][value="'+prediction+'"]');}
async function load(page){await pointer(page,"#load");await page.locator("#result").waitFor({state:"visible"});assert.equal(await page.locator("#answer").isVisible(),false);}
async function inspect(page,id){
 await pointer(page,"#raw-details summary");const raw=JSON.parse(await page.locator("#raw").innerText());
 const expected=id==="rejection"?{compile:original.compile.rejection}:{compile:original.compile.kotlin,runtime:original.runtime_cases.find(r=>r.name===id),...(id==="failure"?{bytecode_oracle:original.bytecode_oracle,contract_violation_judgement:original.oracle.runtime_contract_violation_observed_as_direct_jvm_npe}:{})};
 assert.deepEqual(raw,expected);
 const rows=await page.locator("#comparison tr").evaluateAll(items=>items.map(row=>[...row.cells].map(cell=>cell.textContent)));
 assert.deepEqual(rows,[
  ["通常の文字列","runtime正常 / exit 0",'固定stdout "RESULT=5\\n"'],
  ["空文字列","runtime正常 / exit 0",'固定stdout "RESULT=0\\n"'],
  ["契約を破る戻り値","runtime失敗 / exit 1","NPE部分文字列の照合true（元記録）"],
  ["null引数","compile拒否・JARなし・runtimeなし","NULL_FOR_NONNULL_TYPE"]
 ]);
 assert.match(await page.locator("#provenance").innerText(),/元の実行日時は未保存/);
 if(id==="rejection"){assert.equal("runtime" in raw,false);assert.match(await page.locator("#record").innerText(),/runtime記録なし/);}
 else if(id==="failure"){assert.match(await page.locator("#digest-note").innerText(),/全文は未保存/);assert.match(await page.locator("#expected").innerText(),/部分文字列/);}
 else{assert.match(await page.locator("#digest-note").innerText(),/保存stdout全文の再生ではありません/);assert.match(await page.locator("#digest-note").innerText(),/digest一致を確認/);}
 return raw;
}
async function overflow(page,label){const d=await page.evaluate(()=>({viewport:innerWidth,width:document.documentElement.scrollWidth,outside:[...document.querySelectorAll("main,section,fieldset,button,.evidence-grid,pre")].filter(e=>{if(!e.getClientRects().length)return false;const b=e.getBoundingClientRect();return b.left< -1||b.right>innerWidth+1;}).map(e=>e.id||e.className)}));assert.ok(d.width<=d.viewport,JSON.stringify(d));assert.equal(d.outside.length,0,JSON.stringify(d));note(label,d);}
async function shot(page,name,fullPage=false){const file=path.join(out,name+".png");await page.screenshot({path:file,fullPage,animations:"disabled",timeout:10000});const b=fs.readFileSync(file);record.captures.push({path:path.relative(root,file),sha256:hash(file),viewport:page.viewportSize(),full_page:fullPage,width:b.readUInt32BE(16),height:b.readUInt32BE(20)});}
async function holdNext(page,error=false){fault=error?"hold-error":"hold";const ready=new Promise(resolve=>nextHeldResolve=resolve);await pointer(page,"#load");await ready;fault="pass";}
async function releaseLast(){const item=held.shift();assert.ok(item);item.release();await item.finished;}
(async()=>{try{
 server=http.createServer((req,res)=>{try{const requested=decodeURIComponent(new URL(req.url,"http://localhost").pathname);const file=path.resolve(root,"."+requested+(requested==="/"?"index.html":""));if(file!==root&&!file.startsWith(root+path.sep)){res.writeHead(403);res.end();return;}if(!fs.existsSync(file)||!fs.statSync(file).isFile()){res.writeHead(404);res.end();return;}const mime={".html":"text/html; charset=utf-8",".mjs":"text/javascript; charset=utf-8",".json":"application/json; charset=utf-8",".md":"text/plain; charset=utf-8",".java":"text/plain; charset=utf-8",".kt":"text/plain; charset=utf-8"}[path.extname(file)]||"application/octet-stream";res.writeHead(200,{"Content-Type":mime,"Cache-Control":"no-store"});res.end(fs.readFileSync(file));}catch(error){res.writeHead(500);res.end();}});
 await new Promise((resolve,reject)=>{server.once("error",reject);server.listen(0,"127.0.0.1",resolve);});origin="http://127.0.0.1:"+server.address().port;record.owned_loopback_origin=origin;
 context=await chromium.launchPersistentContext(profile,{executablePath:path.join(os.homedir(),"Library/Caches/ms-playwright/chromium_headless_shell-1200/chrome-headless-shell-mac-arm64/chrome-headless-shell"),headless:true,chromiumSandbox:true,viewport:{width:1280,height:900},deviceScaleFactor:1,locale:"ja-JP",timezoneId:"Asia/Tokyo",acceptDownloads:false,timeout:15000,downloadsPath:path.join(out,"downloads"),artifactsDir:out});
 record.browser_version=context.browser()?.version()||"persistent context";
 await context.route("**/*",async route=>{const url=route.request().url();if(!url.startsWith(origin+"/")){record.blocked_requests.push(url);await route.abort();return;}
  if(url.endsWith("/"+reportName)){
   if(fault==="missing"){record.controlled_faults.push({kind:"HTTP404"});await route.fulfill({status:404,body:"controlled missing"});return;}
   if(fault==="digest"){record.controlled_faults.push({kind:"digest mismatch"});await route.fulfill({status:200,contentType:"application/json",body:"{}"});return;}
   if(fault==="hold"||fault==="hold-error"){const error=fault==="hold-error",item={};item.finished=new Promise(resolve=>item.finish=resolve);held.push(item);const release=new Promise(resolve=>item.release=resolve);nextHeldResolve?.();nextHeldResolve=null;await release;try{await route.fulfill({status:error?503:200,contentType:"application/json",body:error?"controlled delayed error":fs.readFileSync(path.join(root,reportName))});}catch(e){item.cancelled_delivery=String(e).slice(0,150);}record.controlled_faults.push({kind:error?"delayed error released":"delayed success released",cancelled_delivery:item.cancelled_delivery||null});item.finish();return;}
  }await route.continue();
 });
 const page=context.pages()[0]||await context.newPage();page.setDefaultTimeout(5000);page.on("pageerror",e=>record.errors.push({kind:"pageerror",message:String(e)}));
 await page.goto(origin+"/",{waitUntil:"load",timeout:10000});await hiddenAndEmpty(page);assert.equal(await page.locator("#load").isDisabled(),true);note("予想前は結果と答えを出さない",true);
 const order=await page.locator("section h2").allTextContents();assert.equal(order.length,4);order.forEach((v,i)=>assert.ok(v.startsWith((i+1)+".")));note("予想→記録と期待照合→原典実装→答え解釈の読む順",order);
 for(const [id,kind] of [["normal","normal"],["boundary","normal"],["failure","runtime-failure"],["rejection","compile-rejection"]]){await choose(page,id,kind);await load(page);await inspect(page,id);await pointer(page,"#answer-button");assert.match(await page.locator("#verdict").innerText(),/は一致/);note(id+"：実pointer操作・元JSONと比較表一致・証拠境界表示",true);}
 await pointer(page,'input[name="prediction"][value="normal"]');await hiddenAndEmpty(page);note("予想変更で旧結果・答え・原票を消去",true);await load(page);await pointer(page,"#answer-button");assert.match(await page.locator("#verdict").innerText(),/は異なりました/);note("誤った予想は不一致を表示",true);
 await choose(page,"failure","runtime-failure");await load(page);await inspect(page,"failure");await pointer(page,"#raw-details summary");await pointer(page,"#answer-button");await overflow(page,"1280px横はみ出しなし");await shot(page,"desktop-failure-full",true);await page.locator("#result .evidence-grid").scrollIntoViewIfNeeded();await shot(page,"desktop-failure-evidence");await page.locator("#answer-section").scrollIntoViewIfNeeded();await shot(page,"desktop-failure-answer");
 fault="missing";await pointer(page,"#load");await page.locator("#load-error").waitFor({state:"visible"});await hiddenAndEmpty(page);assert.match(await page.locator("#load-error").innerText(),/HTTP 404/);assert.match(await page.locator("#load-error").innerText(),/NPEの観測ではありません/);note("欠落404は資料取得失敗として旧結果を消去",true);await page.locator("#operation-section").scrollIntoViewIfNeeded();await shot(page,"desktop-missing-evidence");
 fault="digest";await pointer(page,"#load");await page.locator("#load-error").waitFor({state:"visible"});await hiddenAndEmpty(page);assert.match(await page.locator("#load-error").innerText(),/SHA-256/);note("改変JSONはdigest不一致で表示しない",true);
 fault="pass";await load(page);assert.equal(await page.locator("#load-error").isVisible(),false);note("取得復旧で正しい記録だけを再表示",true);
 await pointer(page,"#reset");await hiddenAndEmpty(page);assert.equal(await page.locator("#load-error").isVisible(),false);assert.equal(await page.locator('input[name="prediction"]:checked').count(),0);assert.equal(await page.locator('button[data-case="normal"]').getAttribute("aria-pressed"),"true");note("resetは条件と予想も初期化",true);
 await choose(page,"normal","normal");await holdNext(page);await pointer(page,"#reset");await releaseLast();await page.waitForTimeout(150);await hiddenAndEmpty(page);assert.equal(await page.locator("#load").isDisabled(),true);note("読込み中reset後に旧successが結果を戻さない",true);
 await choose(page,"normal","normal");await holdNext(page);await choose(page,"failure","runtime-failure");await load(page);await inspect(page,"failure");await releaseLast();await page.waitForTimeout(150);assert.deepEqual(JSON.parse(await page.locator("#raw").textContent()).runtime,original.runtime_cases.find(r=>r.name==="failure"));note("新条件の表示後に旧successが上書きしない",true);
 await holdNext(page,true);await choose(page,"boundary","normal");await load(page);await inspect(page,"boundary");await releaseLast();await page.waitForTimeout(150);assert.equal(await page.locator("#load-error").isVisible(),false);assert.equal(await page.locator("#result").isVisible(),true);assert.deepEqual(JSON.parse(await page.locator("#raw").textContent()).runtime,original.runtime_cases.find(r=>r.name==="boundary"));note("旧errorは新条件の正常取得を消さない",true);
 await holdNext(page);await pointer(page,'input[name="prediction"][value="runtime-failure"]');await releaseLast();await page.waitForTimeout(150);await hiddenAndEmpty(page);assert.equal(await page.locator("#load").isDisabled(),false);note("予想変更中の旧successは答えを復活させない",true);
 await page.setViewportSize({width:390,height:844});await choose(page,"rejection","compile-rejection");await load(page);await inspect(page,"rejection");await pointer(page,"#raw-details summary");await pointer(page,"#answer-button");await overflow(page,"390px横はみ出しなし");await shot(page,"mobile-rejection-full",true);await page.locator("#result .evidence-grid").scrollIntoViewIfNeeded();await shot(page,"mobile-rejection-evidence");await page.locator("#answer-section").scrollIntoViewIfNeeded();await shot(page,"mobile-rejection-answer");
 await choose(page,"normal","normal");await load(page);await inspect(page,"normal");await pointer(page,"#answer-button");note("390pxでも正常経路と期待digest照合を操作できる",true);await pointer(page,"#reset");await hiddenAndEmpty(page);note("390pxのresetも旧結果を残さない",true);
 assert.equal(record.errors.length,0);record.passed=true;
}catch(error){record.passed=false;record.errors.push({kind:"test-failure",message:String(error.stack||error).replaceAll(os.homedir(),"~")});process.exitCode=1;}
finally{
 for(const item of held)item.release?.();if(context){try{await context.close();record.browser_closed=true;}catch(e){record.errors.push({kind:"close",message:String(e)});process.exitCode=1;}}
 if(!context||record.browser_closed){fs.rmSync(profile,{recursive:true,force:true});record.own_profile_removed=true;}
 if(server){await new Promise(resolve=>{server.close(()=>{record.own_server_closed=true;resolve();});server.closeAllConnections?.();});}
 record.source_after=binding();record.sources_unchanged=JSON.stringify(record.source_before)===JSON.stringify(record.source_after);record.finished_at=new Date().toISOString();fs.writeFileSync(path.join(out,"report.json"),JSON.stringify(record,null,2)+"\n");
 console.log(JSON.stringify({report:path.relative(root,path.join(out,"report.json")),passed:record.passed,checks:record.checks.length,pointer_actions:record.pointer_actions.length,captures:record.captures.length,browser_closed:record.browser_closed,own_server_closed:record.own_server_closed,own_profile_removed:record.own_profile_removed,errors:record.errors},null,2));
}
})();

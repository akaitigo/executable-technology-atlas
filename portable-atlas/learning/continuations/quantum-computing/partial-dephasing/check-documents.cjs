/* Atlas: document-link supplement on the parent's existing page only. */
'use strict';
const fs=require('node:fs'),path=require('node:path'),crypto=require('node:crypto'),assert=require('node:assert/strict');
module.exports=async function({page,baseURL,outDir}){
 const start=Date.now(),budget=15000,oldViewport=page.viewportSize(),root=__dirname;
 const sha=b=>crypto.createHash('sha256').update(b).digest('hex'),fullPath=path.resolve(root,'../browser-qa/three-lessons-2026-10-06/runs/quantum-partial-dephasing-20261006t201052-null-fix-02/report.json');
 const files=['index.html','serve.py','reader.css','reader-app.js','reader-state.js','reader-data.js','reader-expectations.js','SKILL.md','GUI-QA.md'];
 const binding=()=>Object.fromEntries(files.map(f=>[f,sha(fs.readFileSync(path.join(root,f)))]));
 const report={project:'Atlas',lesson:'quantum-partial-dephasing',scope:'Only remaining SKILL.md and GUI-QA.md link navigation; no numeric/UI scenario repetition or capture',started_at:new Date().toISOString(),passed:false,budget_ms:budget,checker_sha256:sha(fs.readFileSync(__filename)),full_report:{path:fullPath,sha256:sha(fs.readFileSync(fullPath)),passed:false,retained_failure:'SKILL.md navigation timeout after numerical/interaction/capture checks'},source_before:binding(),checks:[],documents:[],pointer_actions:[],api_actions:[],captures:[],errors:[],target_calculations:0,new_browser:0,new_context:0,new_tab:0,new_server:0,cleanup:{routes_installed:0,routes_removed:true,viewport_restored:false,page_left_open:true},limits:['Previous center-of-bounding-box click may have missed a wrapped inline anchor; the previous log does not identify the hit element.','Only these remaining document links are confirmed here; full report remains failed.','Parent retains lifecycle ownership of the shared browser/page/server.']};
 fs.mkdirSync(outDir,{recursive:true});const dest=path.join(outDir,'report.json');if(fs.existsSync(dest))throw Error('Atlas: report exists');
 const timeout=()=>{const left=budget-(Date.now()-start);if(left<=0)throw Error('Atlas: supplement deadline; no retry');return Math.min(3000,left);};
 const onError=e=>report.errors.push({kind:'pageerror',message:String(e)});page.on('pageerror',onError);
 try{
  const full=JSON.parse(fs.readFileSync(fullPath,'utf8'));assert.equal(full.cases.length,9);assert.equal(full.captures.length,14);for(const f of ['reader-app.js','reader-state.js','reader-data.js','reader-expectations.js','index.html','reader.css','serve.py'])assert.equal(report.source_before[f],full.source_after[f],f+' unchanged since full comparison');
  for(const f of files){const p=path.join(outDir,'tested-source',f);fs.mkdirSync(path.dirname(p),{recursive:true});fs.copyFileSync(path.join(root,f),p);}
  await page.setViewportSize({width:390,height:844});report.api_actions.push({kind:'viewport',width:390,height:844});
  const entry=new URL('index.html',baseURL.endsWith('/')?baseURL:baseURL+'/').href;
  for(const filename of ['SKILL.md','GUI-QA.md']){
   const response=await page.goto(entry,{waitUntil:'load',timeout:timeout()});assert.ok(response&&response.ok());report.api_actions.push({kind:'same-page-navigation',url:entry});
   const link=page.locator('a[href="'+filename+'"]');await link.scrollIntoViewIfNeeded({timeout:timeout()});
   const point=await link.evaluate(e=>{const rects=[...e.getClientRects()].map(r=>({x:r.x,y:r.y,width:r.width,height:r.height}));const r=rects.find(r=>r.width>0&&r.height>0&&r.x>=0&&r.y>=0&&r.x+r.width<=innerWidth&&r.y+r.height<=innerHeight);if(!r)throw Error('No complete visible anchor rect');const x=r.x+r.width/2,y=r.y+r.height/2;const hit=document.elementFromPoint(x,y),anchor=hit?.closest('a');return {x,y,rects,href:e.href,text:e.textContent,hit_tag:hit?.tagName??null,hit_href:anchor?.href??null,exact_target:anchor===e};});
   assert.equal(point.exact_target,true,'click point belongs to intended anchor');const expectedURL=new URL(filename,entry).href;assert.equal(point.href,expectedURL);
   const action={kind:'mouse-click',filename,...point,completed:false};report.pointer_actions.push(action);await page.mouse.move(point.x,point.y);
   await Promise.all([page.waitForURL(expectedURL,{waitUntil:'load',timeout:timeout()}),page.mouse.click(point.x,point.y)]);action.completed=true;
   const text=await page.locator('body').innerText({timeout:timeout()}),expected=fs.readFileSync(path.join(root,filename),'utf8');assert.equal(text.trim(),expected.trim());assert.ok(text.includes('Atlas'));
   report.documents.push({filename,url:page.url(),body_text:text,source_sha256:sha(Buffer.from(expected)),body_matches_source:true});report.checks.push({name:'visible-anchor-click '+filename,passed:true});
  }
  report.passed=true;
 }catch(e){report.errors.push({kind:'checker-failure',message:String(e.stack||e)});try{report.failure={url:page.url(),body_text:await page.locator('body').innerText({timeout:1000})};}catch{}}
 finally{try{if(oldViewport){await page.setViewportSize(oldViewport);report.cleanup.viewport_restored=true;}}catch(e){report.errors.push({kind:'viewport-restore',message:String(e)});}page.off('pageerror',onError);report.cleanup.listener_removed=true;report.source_after=binding();report.sources_unchanged=JSON.stringify(report.source_before)===JSON.stringify(report.source_after);if(!report.sources_unchanged)report.errors.push({kind:'source-changed'});report.passed=report.passed&&report.errors.length===0;report.finished_at=new Date().toISOString();report.elapsed_ms=Date.now()-start;fs.writeFileSync(dest,JSON.stringify(report,null,2)+'\n');}
 return report;
};

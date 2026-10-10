'use strict';
const fs=require('fs'),path=require('path'),crypto=require('crypto');
const hash=b=>crypto.createHash('sha256').update(b).digest('hex');
const ROOT=__dirname;
const SOURCES=['index.html','reader.css','reader-app.js','reader-state.js','reader-data.js','reader-expectations.js','check-browser.cjs','serve.py','README.md','PREREQUISITES.md','CONTRACT.md','HAND-CALCULATION.md','SOURCES.md','SKILL.md','model.py','hand-oracle.json','observations/result.json'];
const expected=JSON.parse(fs.readFileSync(path.join(ROOT,'hand-oracle.json'),'utf8'));
const same=(a,b)=>{if(a===null||b===null||typeof a!=='object'||typeof b!=='object')return a===b;if(Array.isArray(a)!==Array.isArray(b))return false;if(Array.isArray(a))return a.length===b.length&&a.every((v,i)=>same(v,b[i]));const ak=Object.keys(a),bk=Object.keys(b);return ak.length===bk.length&&ak.every(k=>Object.hasOwn(b,k)&&same(a[k],b[k]));};
const terminalLabels={EXACT_ROOT:'厳密な根',BRACKET_WIDTH_MET:'区間幅の条件を満たす',LOCAL_TOLERANCES_MET:'残差と更新幅の両条件を満たす',ZERO_DERIVATIVE:'根でない点で導関数0',ITERATION_LIMIT:'更新上限に到達',INVALID_BRACKET:'符号変化しない区間を拒否'};
const fmt=v=>v===null?'未定義／未到達':v===true?'満たす':v===false?'満たさない':String(v);
const bkeys=['k','a','b','probe','estimate','f','residual','width','radius','status'];
const nkeys=['k','x','f','df','delta','step','residual','residual_met','step_met','status'];

module.exports=async({page,baseURL,outDir})=>{
  fs.mkdirSync(outDir,{recursive:true});
  const oldViewport=page.viewportSize(),ownRoutes=[];
  const report={passed:false,errors:[],checks:[],actions:[],captures:[],dom:[],clears:[],documents:[],scrolls:[],
    scope:{model_executions:0,browser_created:0,context_created:0,page_created:0,server_created:0,shared_page_retained:true},
    source_before:Object.fromEntries(SOURCES.map(n=>[n,hash(fs.readFileSync(path.join(ROOT,n)))])),cleanup:{}};
  const local=new URL('index.html',baseURL.endsWith('/')?baseURL:baseURL+'/').href;
  const check=(name,ok,detail)=>{report.checks.push({name,passed:!!ok,detail});if(!ok)throw new Error(name);};
  const equal=(name,a,b)=>check(name,same(a,b),{actual:a,expected:b});
  async function pointer(selector){
    const loc=page.locator(selector);await loc.scrollIntoViewIfNeeded({timeout:2500});
    const geometry=await loc.evaluate(el=>{
      const rects=[...el.getClientRects()].map(r=>({left:Math.max(0,r.left),right:Math.min(innerWidth,r.right),top:Math.max(0,r.top),bottom:Math.min(innerHeight,r.bottom)}));
      for(const r of rects){if(r.right<=r.left||r.bottom<=r.top)continue;const x=(r.left+r.right)/2,y=(r.top+r.bottom)/2,hit=document.elementFromPoint(x,y);if(hit&&(hit===el||el.contains(hit)))return {x,y,rects,hit:true,tag:hit.tagName,text:el.textContent};}
      return {rects,hit:false};
    });
    report.actions.push({kind:'native_pointer',selector,...geometry});check('pointer-hit '+selector,geometry.hit);
    await page.mouse.click(geometry.x,geometry.y);
  }
  async function select(selector,value){await page.locator(selector).selectOption(value,{timeout:2500});report.actions.push({kind:'selectOption_API',selector,value});}
  async function clear(label,expectError=false){
    const value=await page.evaluate(()=>({hidden:document.getElementById('results').hidden,raw:document.getElementById('raw').textContent,open:document.getElementById('raw-details').open,answer:document.getElementById('answer').textContent,diagram:document.getElementById('diagram').innerHTML,tables:['bisection','newton'].map(m=>document.getElementById(m+'-table').textContent),error:document.getElementById('error').textContent}));
    report.clears.push({label,...value});check('cleared '+label,value.hidden&&value.raw===''&&!value.open&&value.answer===''&&value.diagram===''&&value.tables.every(x=>x==='')&&(expectError?value.error.length>0:value.error===''));
  }
  async function dom(label,caseValue){
    const d=await page.evaluate(()=>{
      const read=m=>({fields:Object.fromEntries([...document.querySelectorAll('#'+m+' [data-field]')].map(e=>[e.dataset.field,e.textContent])),terminal:document.querySelector('#'+m+' .terminal').textContent,position:document.querySelector('#'+m+' .position').textContent,prevDisabled:document.getElementById(m+'-prev').disabled,nextDisabled:document.getElementById(m+'-next').disabled,table:[...document.querySelectorAll('#'+m+'-table tbody tr')].map(tr=>Object.fromEntries([...tr.querySelectorAll('td')].map(td=>[td.dataset.key,td.textContent])))});
      return {state:window.ROOT_READER.snapshot(),bisection:read('bisection'),newton:read('newton'),validation:document.querySelector('#bisection .validation').textContent,provenance:document.getElementById('provenance').textContent,answer:document.getElementById('answer').textContent,answerVisible:!document.getElementById('answer').hidden,rawText:document.getElementById('raw').textContent,rawOpen:document.getElementById('raw-details').open,diagram:[...document.querySelectorAll('#diagram [data-role]')].map(e=>({role:e.dataset.role,value:e.dataset.value||null,a:e.dataset.a||null,b:e.dataset.b||null,cx:e.getAttribute('cx'),x1:e.getAttribute('x1'),x2:e.getAttribute('x2')}))};
    });
    report.dom.push({label,...d});equal('raw '+label,JSON.parse(d.rawText),caseValue);
    check('provenance '+label,d.provenance.includes(d.state.shown.run_id)&&d.provenance.includes(d.state.shown.result_sha256)&&d.provenance.includes(d.state.shown.observed_at_utc));
    for(const method of ['bisection','newton']){
      const keys=method==='bisection'?bkeys:nkeys,rows=caseValue[method].rows,i=d.state.indices[method],row=rows[i];
      equal('fields '+label+' '+method,d[method].fields,Object.fromEntries(keys.map(k=>[k,fmt(row?row[k]:null)])));
      equal('table '+label+' '+method,d[method].table,rows.map(r=>Object.fromEntries(keys.map(k=>[k,fmt(r[k])]))));
      check('buttons '+label+' '+method,d[method].prevDisabled===(!row||i===0)&&d[method].nextDisabled===(!row||i===rows.length-1));
      check('terminal '+label+' '+method,d[method].terminal.includes(terminalLabels[caseValue[method].status])&&d[method].terminal.includes(caseValue[method].updates+'更新')&&d[method].terminal.includes(fmt(caseValue[method].estimate)));
    }
    const b=caseValue.bisection.rows[d.state.indices.bisection],n=caseValue.newton.rows[d.state.indices.newton];
    equal('diagram roles '+label,d.diagram.map(x=>x.role),b?['bracket','midpoint','newton-point']:['newton-point']);
    if(b){equal('diagram interval '+label,[d.diagram[0].a,d.diagram[0].b,d.diagram[1].value],[b.a,b.b,b.estimate]);}
    equal('diagram newton '+label,d.diagram.at(-1).value,n.x);
    return d;
  }
  async function capture(file,selector){if(selector)await page.locator(selector).scrollIntoViewIfNeeded({timeout:2500});const destination=path.join(outDir,file);await page.screenshot({path:destination,fullPage:false});report.captures.push({file,sha256:hash(fs.readFileSync(destination)),viewport:page.viewportSize(),selector:selector||null});}
  async function loadCase(c){await select('#case',c.id);await clear('case '+c.id);await select('#predict-bisection',c.bisection.status);await select('#predict-newton',c.newton.status);await pointer('#load');}
  async function openedClear(label,method){await pointer('#show-answer');await pointer('#raw-details summary');check('details opened '+label,await page.locator('#raw-details').evaluate(e=>e.open));const old=await page.locator('#predict-'+method).inputValue();await select('#predict-'+method,old==='ITERATION_LIMIT'?'EXACT_ROOT':'ITERATION_LIMIT');await clear(label);}
  async function geometry(selector){return page.locator(selector).evaluate(el=>{
    const r=el.getBoundingClientRect(),last=el.querySelector('thead th:last-child');let textRects=[];
    if(last){const range=document.createRange();range.selectNodeContents(last);textRects=[...range.getClientRects()].map(q=>({left:q.left,right:q.right,top:q.top,bottom:q.bottom}));}
    return {scrollLeft:el.scrollLeft,scrollWidth:el.scrollWidth,clientWidth:el.clientWidth,clip:{left:r.left+el.clientLeft,right:r.left+el.clientLeft+el.clientWidth,top:Math.max(r.top,0),bottom:Math.min(r.bottom,innerHeight)},lastText:last?.textContent||null,textRects};
  });}
  async function wheel(selector,delta,label){
    await page.locator(selector).scrollIntoViewIfNeeded({timeout:2500});const before=await geometry(selector),r=await page.locator(selector).boundingBox();
    const hit=await page.evaluate(({x,y,s})=>{const e=document.elementFromPoint(x,y);return !!e?.closest(s);},{x:r.x+Math.min(r.width/2,150),y:Math.max(10,r.y)+20,s:selector});
    check('wheel hit '+label,hit);await page.mouse.move(r.x+Math.min(r.width/2,150),Math.max(10,r.y)+20);await page.mouse.wheel(delta,0);report.actions.push({kind:'native_wheel',selector,deltaX:delta});
    await page.waitForFunction(({s,right})=>{const e=document.querySelector(s);return right?e.scrollLeft>=e.scrollWidth-e.clientWidth-1:e.scrollLeft<=1;},{s:selector,right:delta>0},{timeout:2500});
    const after=await geometry(selector);report.scrolls.push({label,selector,before,after});
    check('scroll '+label,delta>0?after.scrollLeft>0:after.scrollLeft<=1);
    if(delta>0&&after.lastText)check('rightmost text visible '+label,after.textRects.every(q=>q.left>=after.clip.left-1&&q.right<=after.clip.right+1));
  }
  report.supplement_for={path:'../browser-qa/cache-histogram-roots-2026-10-07/session-2026-10-07T054042598Z/numerical-root-finding-boundaries-first-after-memory-hold/report.json',sha256:'2ccc8c250eb4ca72c00547a0835e46cb5250c644a8a63a10f275cb3315339719',passed:false};
  report.scope.native_selection_confirmed=false;
  report.scope.native_selection_limitation='Not demonstrated in the previous headless key sequence; not retried here.';
  report.previous_keyboard_report={path:'../browser-qa/cache-histogram-roots-2026-10-07/session-2026-10-07T054042598Z/numerical-root-finding-boundaries-keyboard-docs-followup-after-hold/report.json',sha256:'244f9dfa42ddd7396b8f2328d18efe23fbc0ae75d82f6b3fd6ab66727dd138ef',passed:false};
  try{
    check('restorable viewport',!!oldViewport);await page.setViewportSize({width:390,height:844});await page.goto(local,{waitUntil:'domcontentloaded',timeout:5000});
    check('connected data',await page.evaluate(()=>!!window.ROOT_BOUNDARY_DATA));
    const first=expected.cases[0];await loadCase(first);await pointer('#show-answer');await pointer('#raw-details summary');
    report.reset_before=await page.evaluate(()=>({case_id:window.ROOT_READER.snapshot().case_id,shown:!!window.ROOT_READER.snapshot().shown,rawOpen:document.getElementById('raw-details').open,rawLength:document.getElementById('raw').textContent.length,answerVisible:!document.getElementById('answer').hidden,answer:document.getElementById('answer').textContent}));
    check('prepared shown answer and open detail',report.reset_before.shown&&report.reset_before.rawOpen&&report.reset_before.rawLength>0&&report.reset_before.answerVisible&&report.reset_before.answer.length>0);
    await pointer('#reset');await clear('reset from open detail');
    const docs=['README.md','PREREQUISITES.md','CONTRACT.md','HAND-CALCULATION.md','SOURCES.md','model.py','SKILL.md'];
    for(const file of docs){
      await pointer(`a[href="${file}"]`);await page.waitForURL(new URL(file,local).href,{timeout:2500});
      const body=await page.locator('body').innerText(),source=fs.readFileSync(path.join(ROOT,file),'utf8');
      check('document '+file,body.trim()===source.trim());report.documents.push({file,url:page.url(),visible_text:body,source_sha256:hash(Buffer.from(source)),kind:'local text read by pointer'});await page.goto(local,{waitUntil:'domcontentloaded',timeout:5000});
    }
    const external='https://fncbook.com/newton/',notice='外部通信を遮断したテスト応答です。公式本文は取得していません。';
    const handler=route=>route.fulfill({status:200,contentType:'text/html; charset=utf-8',body:'<!doctype html><html lang="ja"><body>'+notice+'</body></html>'});
    await page.route(external,handler);ownRoutes.push([external,handler]);await pointer('#external-source');await page.waitForURL(external,{timeout:2500});
    const body=await page.locator('body').innerText();check('external notice',body===notice);report.documents.push({url:page.url(),kind:'local blocked notice',remote_requests:0,official_body_read:false,visible_text:body});await page.goto(local,{waitUntil:'domcontentloaded',timeout:5000});
    report.passed=true;
  }catch(error){report.errors.push({message:error.message,stack:error.stack});}
  finally{
    for(const [url,handler] of ownRoutes)try{await page.unroute(url,handler);}catch(error){report.errors.push({cleanup:'route',message:error.message});}
    report.cleanup.own_routes_removed=report.errors.every(e=>e.cleanup!=='route');
    try{if(oldViewport)await page.setViewportSize(oldViewport);report.cleanup.viewport_restored=!!oldViewport;}catch(error){report.errors.push({cleanup:'viewport',message:error.message});report.cleanup.viewport_restored=false;}
    report.cleanup.shared_page_open=!page.isClosed();report.cleanup.browser_server_operations=0;
    report.source_after=Object.fromEntries(SOURCES.map(n=>[n,hash(fs.readFileSync(path.join(ROOT,n)))]));
    report.source_unchanged=JSON.stringify(report.source_before)===JSON.stringify(report.source_after);
    report.passed=report.passed&&report.errors.length===0&&report.source_unchanged&&report.cleanup.own_routes_removed&&report.cleanup.viewport_restored;
    fs.writeFileSync(path.join(outDir,'report.json'),JSON.stringify(report,null,2)+'\n');
  }
  return {passed:report.passed};
};

'use strict';
const fs=require('fs'),path=require('path'),crypto=require('crypto');
const ROOT=__dirname,hash=b=>crypto.createHash('sha256').update(b).digest('hex');
const SOURCES=['index.html','reader.css','reader-app.js','reader-state.js','reader-data.js','reader-expectations.js','check-browser.cjs','serve.py','README.md','PREREQUISITES.md','CONTRACT.md','HAND-CALCULATION.md','SOURCES.md','SKILL.md','model.py','hand-oracle.json','observations/result.json'];
const EXPECTED=JSON.parse(fs.readFileSync(path.join(ROOT,'hand-oracle.json'),'utf8'));
const V=['continuation','full-restore','omit-device'];
const labels={'continuation':'そのまま継続','full-restore':'完全復元','omit-device':'装置欠落の比較版'};
const same=(a,b)=>{if(a===null||b===null||typeof a!=='object'||typeof b!=='object')return a===b;if(Array.isArray(a)!==Array.isArray(b))return false;if(Array.isArray(a))return a.length===b.length&&a.every((v,i)=>same(v,b[i]));const k=Object.keys(a);return k.length===Object.keys(b).length&&k.every(x=>Object.hasOwn(b,x)&&same(a[x],b[x]));};
const fmt=v=>v===null?'—':Array.isArray(v)?'['+v.join(',')+']':String(v);
const write=v=>v===null?'—':`M${v.address}:${v.previous}→${v.value}`;

module.exports=async({page,baseURL,outDir})=>{
  fs.mkdirSync(outDir,{recursive:true});
  const viewport=page.viewportSize(),routes=[];
  const local=new URL('index.html',baseURL.endsWith('/')?baseURL:baseURL+'/').href;
  const report={passed:false,errors:[],checks:[],actions:[],captures:[],dom:[],answers:[],clears:[],documents:[],scrolls:[],
    scope:{model_executions:0,browser_created:0,context_created:0,page_created:0,server_created:0,native_select_tests:0},
    source_before:Object.fromEntries(SOURCES.map(n=>[n,hash(fs.readFileSync(path.join(ROOT,n)))])),cleanup:{}};
  const check=(name,value,detail)=>{report.checks.push({name,passed:!!value,detail});if(!value)throw new Error(name);};
  const equal=(name,actual,expected)=>check(name,same(actual,expected),{actual,expected});
  async function pointer(selector){
    const node=page.locator(selector);await node.scrollIntoViewIfNeeded({timeout:2500});
    const geometry=await node.evaluate(el=>{
      const rects=[...el.getClientRects()].map(r=>({left:Math.max(0,r.left),right:Math.min(innerWidth,r.right),top:Math.max(0,r.top),bottom:Math.min(innerHeight,r.bottom)}));
      for(const r of rects){if(r.right<=r.left||r.bottom<=r.top)continue;const x=(r.left+r.right)/2,y=(r.top+r.bottom)/2,h=document.elementFromPoint(x,y);if(h&&(h===el||el.contains(h)))return {x,y,rects,hit:true,text:el.textContent};}
      return {rects,hit:false};
    });
    report.actions.push({kind:'native_pointer',selector,...geometry});check('pointer hit '+selector,geometry.hit);await page.mouse.click(geometry.x,geometry.y);
  }
  async function clear(label,error=false){
    const value=await page.evaluate(()=>({hidden:document.querySelector('#results').hidden,raw:document.querySelector('#raw').textContent,open:document.querySelector('#raw-details').open,
      answer:document.querySelector('#answer').textContent,diagram:document.querySelector('#diagram').innerHTML,cards:document.querySelector('#cards').textContent,
      table:document.querySelector('#trace').textContent,snapshots:document.querySelector('#snapshots').textContent,provenance:document.querySelector('#provenance').textContent,error:document.querySelector('#error').textContent}));
    report.clears.push({label,...value});check('clear '+label,value.hidden&&!value.open&&['raw','answer','diagram','cards','table','snapshots','provenance'].every(k=>value[k]==='')&&(error?value.error.length>0:value.error===''));
  }
  async function capture(file,selector){
    await page.locator(selector).scrollIntoViewIfNeeded({timeout:2500});await page.screenshot({path:path.join(outDir,file),fullPage:false});
    report.captures.push({file,sha256:hash(fs.readFileSync(path.join(outDir,file))),viewport:page.viewportSize(),selector});
  }
  async function answerRecord(){const a=await page.evaluate(()=>({case_id:DeviceSnapshotReader.getState().case_id,prediction:DeviceSnapshotReader.getState().prediction,text:document.querySelector('#answer').textContent}));report.answers.push(a);check('answer text includes full restore equality',a.text.includes('完全復元のsuffixは継続と全値一致'));return a;}
  async function opened(){await pointer('#answer-button');await answerRecord();await pointer('#raw-details summary');check('detail actually open',await page.locator('#raw-details').evaluate(e=>e.open));}
  async function choose(c,prediction){await pointer(`[data-case="${c.id}"]`);await clear('case '+c.id);await pointer(`[data-prediction="${prediction}"]`);await clear('prediction '+prediction);await pointer('#load');}
  async function sample(c,index,label){
    const d=await page.evaluate(()=>({state:DeviceSnapshotReader.getState(),position:document.querySelector('#position').textContent,
      cards:[...document.querySelectorAll('.card')].map(el=>({variant:el.dataset.variant,values:Object.fromEntries([...el.querySelectorAll('dl>div')].map(x=>[x.dataset.key,x.querySelector('dd').textContent]))})),
      snapshots:[...document.querySelectorAll('.snapshot')].map(el=>({values:Object.fromEntries([...el.querySelectorAll('[data-key]')].map(x=>[x.dataset.key,x.dataset.value])),visible_text:[...el.querySelectorAll('[data-key]')].map(x=>x.textContent)})),
      table:[...document.querySelectorAll('#trace tr')].map(tr=>({variant:tr.dataset.variant,tick:Number(tr.dataset.tick),cells:[...tr.querySelectorAll('td')].map(x=>x.textContent)})),
      points:[...document.querySelectorAll('#diagram circle')].map(e=>({variant:e.dataset.variant,tick:Number(e.dataset.tick),counter:Number(e.dataset.counter),pending:e.dataset.pending,cx:e.getAttribute('cx'),cy:e.getAttribute('cy')})),
      raw:JSON.parse(document.querySelector('#raw').textContent),previous:document.querySelector('#previous').disabled,next:document.querySelector('#next').disabled,answer:document.querySelector('#answer').textContent}));
    report.dom.push({label,...d});equal('raw '+label,d.raw,c);equal('selected index '+label,d.state.index,index);equal('case '+label,d.state.case_id,c.id);
    equal('position '+label,d.position,`選択境界 tick ${c.cut+index} / 最終 tick 10`);
    equal('previous '+label,d.previous,index===0);equal('next '+label,d.next,index===10-c.cut);
    const snapshots=[c.snapshot.state,c.variants['omit-device'].boundary_states[0]].map(s=>{const values=Object.fromEntries(Object.entries({pc:s.pc,a:s.a,memory:s.memory,tick:s.tick,counter:s.device.counter,pending:s.device.pending}).map(([k,v])=>[k,fmt(v)]));const names={pc:'次のpc',a:'A',memory:'memory',tick:'仮想tick',counter:'counter',pending:'境界pending'};return {values,visible_text:Object.entries(values).map(([k,v])=>`${names[k]} = ${v}`)};});
    equal('snapshot values '+label,d.snapshots,snapshots);
    const cards=V.map(name=>{const s=c.variants[name].boundary_states[index],e=index?c.variants[name].steps[index-1]:null;
      const values={pc:s.pc,a:s.a,memory:s.memory,tick:s.tick,counter:s.device.counter,pending:s.device.pending,op:e?e.op:null,
        timer_pending:e?e.timer_after.pending:null,timer_fired:e?e.timer_after.fired:null,read_value:e?e.read_value:null,write:e?write(e.write):'—',ack:e?e.ack:null};
      return {variant:name,values:Object.fromEntries(Object.entries(values).map(([k,v])=>[k,fmt(v)]))};});
    equal('cards '+label,d.cards,cards);
    const table=V.flatMap(name=>c.variants[name].boundary_states.map((s,j)=>{const e=j?c.variants[name].steps[j-1]:null;return {variant:name,tick:s.tick,cells:[labels[name],s.tick,s.pc,s.a,fmt(s.memory),s.device.counter,s.device.pending,e?e.timer_after.fired:null,e?e.read_value:null,e?write(e.write):'—'].map(fmt)};}));
    equal('whole suffix table '+label,d.table,table);
    const points=V.flatMap((name,vi)=>c.variants[name].boundary_states.map(s=>({variant:name,tick:s.tick,counter:s.device.counter,pending:String(s.device.pending),cx:String(150+55*s.tick),cy:String(50+60*vi+(s.device.pending?-12:12))})));
    equal('diagram points '+label,d.points,points);
  }
  async function wheel(selector,direction,file){
    const el=page.locator(selector);await el.scrollIntoViewIfNeeded({timeout:2500});
    const before=await el.evaluate(e=>{const r=e.getBoundingClientRect();return {scroll:e.scrollLeft,max:e.scrollWidth-e.clientWidth,left:Math.max(r.left,0),right:Math.min(r.right,innerWidth),top:Math.max(r.top,0),bottom:Math.min(r.bottom,innerHeight)};});
    check('scrollable '+selector,before.max>0&&before.bottom>before.top);
    const x=(before.left+before.right)/2,y=(before.top+before.bottom)/2;
    await page.mouse.move(x,y);await page.mouse.wheel(direction*1800,0);report.actions.push({kind:'native_wheel',selector,direction,x,y});
    await page.waitForFunction(({selector,direction})=>{const e=document.querySelector(selector);return direction>0?e.scrollLeft>=e.scrollWidth-e.clientWidth-1:e.scrollLeft<=1;},{selector,direction},{timeout:2500});
    const after=await el.evaluate(e=>{const r=e.getBoundingClientRect(),cell=e.querySelector('th:last-child');const range=cell?document.createRange():null;if(range)range.selectNodeContents(cell);const tr=range?range.getBoundingClientRect():null;return {scroll:e.scrollLeft,max:e.scrollWidth-e.clientWidth,clip:{left:Math.max(r.left,0),right:Math.min(r.right,innerWidth)},rightHeader:tr?{left:tr.left,right:tr.right,text:cell.textContent}:null};});
    report.scrolls.push({selector,direction,before,after});
    if(selector==='#table-scroll'&&direction>0)check('right column text in horizontal clip',after.rightHeader.left>=after.clip.left-1&&after.rightHeader.right<=after.clip.right+1,after);
    await capture(file,selector);
  }
  try{
    check('restorable viewport',viewport!==null);
    await page.setViewportSize({width:1280,height:900});await page.goto(local,{waitUntil:'load',timeout:10000});
    const docs=['README.md','PREREQUISITES.md','CONTRACT.md','HAND-CALCULATION.md','SOURCES.md','model.py','SKILL.md'];
    for(const file of docs)check('visible local link exists '+file,await page.locator(`footer a[href="${file}"]`).isVisible());
    await capture('entry-1280.png','header');await page.setViewportSize({width:390,height:844});await capture('entry-390.png','#controls');
    await page.setViewportSize({width:1280,height:900});
    for(const c of EXPECTED.cases){
      const prediction=c.comparison.fault_suffix_equal?'same':'different';await choose(c,prediction);
      for(let i=0;i<c.variants.continuation.boundary_states.length;i++){
        if(i)await pointer('#next');await sample(c,i,c.id+'@'+(c.cut+i));
        if(c.id==='before-expiry'&&c.cut+i===4)await capture('phase-read-1280.png','#cards');
      }
      await pointer('#previous');await sample(c,9-c.cut,c.id+' previous');await pointer('#next');
      await opened();await pointer(`[data-prediction="${prediction==='same'?'different':'same'}"]`);await clear('open detail prediction '+c.id);
      await pointer('#load');await pointer('#answer-button');const wrong=await answerRecord();check('wrong prediction feedback '+c.id,wrong.text.includes('予想と異なります'));
    }
    await page.setViewportSize({width:390,height:844});
    const pending=EXPECTED.cases[2];await choose(pending,'different');await pointer('#next');await sample(pending,1,'pending mobile tick4');await capture('pending-read-390.png','.card[data-variant="omit-device"]');
    const ack=EXPECTED.cases[3];await choose(ack,'same');await sample(ack,0,'ack mobile boundary');await capture('ack-boundary-390.png','.card[data-variant="omit-device"]');
    const phase=EXPECTED.cases[1];await choose(phase,'different');await capture('diagram-left-390.png','#diagram-scroll');
    await wheel('#diagram-scroll',1,'diagram-right-390.png');await wheel('#diagram-scroll',-1,'diagram-return-390.png');
    await capture('table-left-390.png','#table-scroll');await wheel('#table-scroll',1,'table-right-390.png');await wheel('#table-scroll',-1,'table-return-390.png');
    await pointer('#record-details summary');check('record controls actually open',await page.locator('#record-details').evaluate(e=>e.open));
    check('record mode button visible',await page.locator('[data-mode="missing"]').isVisible());
    for(const mode of ['missing','altered','old']){
      await opened();await pointer(`[data-mode="${mode}"]`);await clear('mode '+mode);await pointer('#load');await clear('rejected '+mode,true);
      if(mode==='altered')await capture('record-refusal-390.png','#error');
      await pointer('[data-mode="saved"]');await clear('saved recovery '+mode);await pointer('#load');await sample(phase,0,'recovery '+mode);
    }
    await opened();await pointer('[data-case="pending-latched"]');await clear('opened detail case change');await pointer('#load');await opened();await pointer('#reset');await clear('opened detail reset');
    for(const file of docs){
      await pointer(`footer a[href="${file}"]`);await page.waitForURL(u=>decodeURIComponent(u.pathname).endsWith('/'+file),{timeout:2500});
      const text=await page.locator('body').innerText();const expected=fs.readFileSync(path.join(ROOT,file),'utf8');
      report.documents.push({file,url:page.url(),visible_text:text,source_sha256:hash(Buffer.from(expected)),kind:'local text read by pointer'});
      equal('document body '+file,text.replace(/\r\n/g,'\n').trimEnd(),expected.replace(/\r\n/g,'\n').trimEnd());await page.goto(local,{waitUntil:'load',timeout:10000});
    }
    const remote='https://www.qemu.org/docs/master/devel/migration/main.html';
    const handler=route=>route.fulfill({status:200,contentType:'text/plain; charset=utf-8',body:'外部通信を遮断したテスト応答。QEMU公式本文は取得していません。'});
    await page.route(remote,handler);routes.push([remote,handler]);await pointer(`a[href="${remote}"]`);await page.waitForURL(remote,{timeout:2500});
    const notice=await page.locator('body').innerText();report.documents.push({file:remote,url:page.url(),visible_text:notice,kind:'local blocked notice; remote body not fetched'});check('blocked notice',notice.includes('取得していません'));
    await page.goto(local,{waitUntil:'load',timeout:10000});report.passed=true;
  }catch(error){report.errors.push(String(error.stack||error));}
  finally{
    report.cleanup.own_routes_removed=true;
    for(const [pattern,handler] of routes){try{await page.unroute(pattern,handler);}catch(error){report.cleanup.own_routes_removed=false;report.passed=false;report.errors.push('route cleanup: '+String(error));}}
    if(viewport){try{await page.setViewportSize(viewport);report.cleanup.viewport_restored=same(page.viewportSize(),viewport);}catch(error){report.cleanup.viewport_restored=false;report.passed=false;report.errors.push('viewport cleanup: '+String(error));}}
    report.cleanup.shared_page_open=!page.isClosed();report.cleanup.browser_server_operations=0;
    report.source_after=Object.fromEntries(SOURCES.map(n=>[n,hash(fs.readFileSync(path.join(ROOT,n)))]));report.source_unchanged=same(report.source_before,report.source_after);
    if(!report.source_unchanged){report.passed=false;report.errors.push('source changed during check');}
    fs.writeFileSync(path.join(outDir,'report.json'),JSON.stringify(report,null,2)+'\n');
  }
  return {passed:report.passed};
};

/* Atlas: handwritten element/SVG model, not a browser or actual DOM. */
'use strict';
const fs=require('node:fs'),vm=require('node:vm'),crypto=require('node:crypto'),assert=require('node:assert/strict');
const checks=[],states=[];
function check(name,value){assert.ok(value,name);checks.push(name);}
class Element{
 constructor(tag='div'){this.tag=tag;this.children=[];this.listeners={};this.attributes={};this.dataset={};this.hidden=false;this.disabled=false;this.open=false;this.value='';this._text='';}
 set textContent(v){this._text=String(v);this.children=[];}get textContent(){return this._text+this.children.map(c=>c.textContent).join('');}
 replaceChildren(...nodes){this._text='';this.children=[...nodes];}append(...nodes){this.children.push(...nodes);}
 setAttribute(k,v){this.attributes[k]=v;}addEventListener(k,f){this.listeners[k]=f;}
 click(){if(!this.disabled)return this.listeners.click?.();}
}
const elements={};for(const[,id]of fs.readFileSync('index.html','utf8').matchAll(/id="([^"]+)"/g))elements[id]=new Element();
const get=id=>{assert.ok(elements[id],'element '+id);return elements[id];};let pendingDigest=null;
const context={TextEncoder,document:{getElementById:get,createElement:t=>new Element(t),createElementNS:(_,t)=>new Element(t)},crypto:{subtle:{digest:async(_,data)=>{
 if(pendingDigest){const fn=pendingDigest;pendingDigest=null;return fn(data);}return crypto.createHash('sha256').update(Buffer.from(data)).digest();
}}}};context.window=context;vm.createContext(context);
vm.runInContext(fs.readFileSync('data.js','utf8'),context,{timeout:500});const originalText=context.ATLAS_DATA_TEXT,bundle=JSON.parse(originalText);
vm.runInContext(fs.readFileSync('lesson.js','utf8'),context,{timeout:500});
function predict(text='predict next IDs'){get('prediction').value=text;get('prediction').listeners.input();}
function cleared(label){check(label,get('result').hidden&&get('raw').textContent===''&&get('roc').children.length===0&&get('pr').children.length===0&&get('answer').hidden&&get('answer').textContent===''&&get('answer-button').disabled);}
async function read(){predict();await get('read').click();}
function circles(id){return get(id).children.filter(e=>e.tag==='circle');}
async function main(){
 cleared('initial result absent');check('initial read disabled',get('read').disabled);
 if(bundle.run_text===null){await read();cleared('pending dataset does not create observation');check('pending explanation',get('load-state').textContent.includes('まだ実行していません'));return report('pending-only');}
 const run=JSON.parse(bundle.run_text);
 for(const fixture of ['main','tie']){
  get(fixture+'-fixture').click();const saved=run.records.filter(r=>r.kind==='state'&&r.fixture===fixture);
  for(let ordinal=0;ordinal<saved.length;ordinal++){
   const s=saved[ordinal],name=fixture+'/'+ordinal;await read();check(name+' loaded',!get('result').hidden);check(name+' raw exact saved state',JSON.stringify(JSON.parse(get('raw').textContent))===JSON.stringify(s));
   check(name+' control endpoints',get('previous').disabled===(ordinal===0)&&get('next').disabled===(ordinal===saved.length-1));
   const counts=get('counts').children.map(r=>r.children.map(c=>c.textContent));check(name+' count rows',JSON.stringify(counts)===JSON.stringify(['TP','FP','FN','TN'].map(k=>[k,String(s.counts[k]),s.ids[k].join(', ')||'なし'])));
   const metrics=get('metrics').children.map(r=>r.children.map(c=>c.textContent));check(name+' metric rows',JSON.stringify(metrics)===JSON.stringify(['recall','fpr','precision'].map(k=>{const m=s.metrics[k];return[k,m.numerator+' / '+m.denominator,m.fraction===null?'未定義':m.fraction,m.value===null?'数値なし':String(m.value)];})));
   for(const plot of ['roc','pr']){
    const wanted=saved.slice(0,ordinal+1).filter(r=>r[plot]!==null),points=circles(plot);check(name+' '+plot+' no undefined or future circles',points.length===wanted.length);
    check(name+' '+plot+' exact coordinates',points.every((p,i)=>p.attributes['data-ordinal']===String(wanted[i].ordinal)&&p.attributes['data-x-fraction']===wanted[i][plot].x_fraction&&p.attributes['data-y-fraction']===wanted[i][plot].y_fraction&&Number(p.attributes.cx)===56+332*wanted[i][plot].x&&Number(p.attributes.cy)===242-206*wanted[i][plot].y));
    const guide=get(plot).children.filter(e=>e.tag==='polyline');check(name+' '+plot+' guide classification',guide.length===(points.length>1?1:0)&&guide.every(e=>e.attributes['data-role']==='reading-guide-not-interpolation'));
   }
   if(ordinal===0)check(name+' PR undefined explicit',get('coordinate-note').textContent.includes('PR 点はありません')&&circles('pr').length===0);
   get('answer-button').click();check(name+' answer opens',!get('answer').hidden);
   states.push({fixture,ordinal,kind:'element-model-only',counts,metrics,coordinate_note:get('coordinate-note').textContent,roc_circles:circles('roc').map(p=>p.attributes),pr_circles:circles('pr').map(p=>p.attributes),raw:JSON.parse(get('raw').textContent)});
   predict('changed');cleared(name+' prediction clears');
   if(ordinal<saved.length-1){get('next').click();cleared(name+' next clears');check(name+' next clears prediction',get('prediction').value==='');}
  }
  get('previous').click();cleared(fixture+' previous clears');check(fixture+' previous enables next',!get('next').disabled);await read();check(fixture+' previous selects penultimate',JSON.parse(get('raw').textContent).ordinal===saved.length-2);
 }
 get('reset').click();cleared('reset clears');check('reset main endpoint',get('main-fixture').attributes['aria-pressed']==='true'&&get('previous').disabled);
 vm.runInContext('delete globalThis.ATLAS_DATA_TEXT',context);await read();cleared('missing data remains empty');check('missing data distinct from undefined',get('load-state').textContent.includes('Precision の未定義'));
 context.ATLAS_DATA_TEXT=originalText+' ';await read();cleared('digest mismatch empty');check('digest mismatch explanation',get('load-state').textContent.includes('ダイジェスト'));
 context.ATLAS_DATA_TEXT=originalText;await read();check('restore data recovers',!get('result').hidden);
 let release;pendingDigest=data=>new Promise(resolve=>{release=()=>resolve(crypto.createHash('sha256').update(Buffer.from(data)).digest());});predict();const oldSuccess=get('read').click();get('reset').click();release();await oldSuccess;cleared('old digest success after reset discarded');
 let reject;pendingDigest=()=>new Promise((_,r)=>{reject=r;});predict();const oldError=get('read').click();get('tie-fixture').click();await read();const fresh=get('raw').textContent;reject(new Error('old digest error'));await oldError;check('old error cannot erase new result',!get('result').hidden&&get('raw').textContent===fresh&&!get('load-state').className.includes('error'));
 return report('saved-results');
}
function report(mode){return{project:'Atlas',passed:true,mode,method:'Node VM handwritten element/SVG model; not layout, actual DOM, real pointer or image evidence',check_count:checks.length,checks,modeled_states:states,actual_dom_states:0,browser_starts:0,captures:0,producer_runs:0,source_sha256:Object.fromEntries(['index.html','lesson.js','data.js','reader-model-check.cjs'].map(n=>[n,crypto.createHash('sha256').update(fs.readFileSync(n)).digest('hex')]))};}
main().then(r=>process.stdout.write(JSON.stringify(r,null,2)+'\n')).catch(e=>{process.stdout.write(JSON.stringify({project:'Atlas',passed:false,error:e.stack,checks_completed:checks.length,load_state:get('load-state').textContent},null,2)+'\n');process.exitCode=1;});

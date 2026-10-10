/* Atlas: minimal element model, not a browser or a real DOM test. */
'use strict';
const fs=require('node:fs'),vm=require('node:vm'),crypto=require('node:crypto'),assert=require('node:assert/strict');
const checks=[],states=[];
function check(name,ok){assert.ok(ok,name);checks.push(name);}
class Element{
  constructor(tag='div'){this.tag=tag;this.children=[];this.listeners={};this.attributes={};this.dataset={};this.hidden=false;this.disabled=false;this.open=false;this.value='';this._text='';}
  set textContent(v){this._text=String(v);this.children=[];}get textContent(){return this._text+this.children.map(c=>c.textContent).join('');}
  replaceChildren(...nodes){this._text='';this.children=[...nodes];}append(...nodes){this.children.push(...nodes);}
  setAttribute(k,v){this.attributes[k]=v;}addEventListener(k,f){this.listeners[k]=f;}
  click(){if(!this.disabled)return this.listeners.click?.();}
}
const html=fs.readFileSync('index.html','utf8'),elements={};
for(const [,id]of html.matchAll(/id="([^"]+)"/g))elements[id]=new Element();
const get=id=>{assert.ok(elements[id],'known element '+id);return elements[id];};
let pendingDigest=null;
const context={TextEncoder,document:{getElementById:get,createElement:tag=>new Element(tag)},crypto:{subtle:{digest:async(algorithm,data)=>{
  if(pendingDigest){const p=pendingDigest;pendingDigest=null;return p(data);}
  return crypto.createHash('sha256').update(Buffer.from(data)).digest();
}}}};context.window=context;
vm.createContext(context);vm.runInContext(fs.readFileSync('data.js','utf8'),context,{timeout:500});
const originalText=context.ATLAS_DATA_TEXT;const bundle=JSON.parse(originalText),run=JSON.parse(bundle.run_text),cases=run.records.filter(c=>c.kind==='case');
vm.runInContext(fs.readFileSync('lesson.js','utf8'),context,{timeout:500});
function choose(id){get('choices').children.find(b=>b.dataset.case===id).click();}
function predict(value='predict stack'){get('prediction').value=value;get('prediction').listeners.input();}
function cleared(label){check(label,get('result').hidden&&get('raw').textContent===''&&get('answer').hidden&&get('answer').textContent===''&&get('previous').disabled&&get('next').disabled&&get('answer-button').disabled);}
async function read(){predict();await get('read').click();}
async function main(){
  cleared('initial result and answer absent');check('initial read disabled',get('read').disabled);
  for(const c of cases){
    choose(c.id);await read();check(c.id+' load',!get('result').hidden&&!get('load-state').className.includes('error'));
    check(c.id+' first stage',get('previous').disabled&&!get('next').disabled&&get('answer-button').disabled);
    check(c.id+' no future result in raw',!Object.hasOwn(JSON.parse(get('raw').textContent),'vm'));
    for(let i=0;i<c.vm.trace.length;i++){
      get('next').click();const raw=JSON.parse(get('raw').textContent),t=c.vm.trace[i];
      check(c.id+' exact saved step '+i,JSON.stringify(raw.step)===JSON.stringify(t));
      check(c.id+' answer gated '+i,get('answer-button').disabled);
      if(t.phase==='finish')check(c.id+' finish/null renders without join',get('phase-title').textContent.includes('終端検査')&&get('diagram').textContent.includes('終端検査'));
      states.push({case:c.id,stage:i+1,kind:'element-model-only',phase_title:get('phase-title').textContent,diagram_text:get('diagram').textContent,raw});
    }
    get('next').click();check(c.id+' terminal bounds',get('next').disabled&&!get('answer-button').disabled);
    check(c.id+' full saved case',JSON.stringify(JSON.parse(get('raw').textContent))===JSON.stringify(c));
    get('answer-button').click();check(c.id+' answer revealed',!get('answer').hidden);
    get('previous').click();check(c.id+' backward closes answer',get('answer').hidden&&get('answer-button').disabled);
    get('next').click();get('answer-button').click();predict('changed');cleared(c.id+' prediction clears old result');
  }
  choose('zero');await read();choose('final-empty');cleared('condition clears result');check('condition clears prediction',get('prediction').value==='');
  await read();get('reset').click();cleared('reset clears');check('reset first condition',get('choices').children[0].attributes['aria-pressed']==='true');
  vm.runInContext("delete globalThis.ATLAS_DATA_TEXT",context);await read();cleared('missing data remains empty');check('missing data separate error',get('load-state').textContent.includes('VM の意図した拒否とは別'));
  context.ATLAS_DATA_TEXT=originalText+' ';await read();cleared('changed data remains empty');check('digest mismatch message',get('load-state').textContent.includes('ダイジェスト'));
  context.ATLAS_DATA_TEXT=originalText;await read();check('restore data recovers',!get('result').hidden);
  let release;pendingDigest=data=>new Promise(resolve=>{release=()=>resolve(crypto.createHash('sha256').update(Buffer.from(data)).digest());});
  predict();const oldSuccess=get('read').click();get('reset').click();release();await oldSuccess;cleared('late digest success after reset discarded');
  let reject;pendingDigest=()=>new Promise((_,r)=>{reject=r;});
  predict();const oldError=get('read').click();choose('zero');await read();const newRaw=get('raw').textContent;reject(new Error('old digest failure'));await oldError;
  check('late error after new success discarded',get('raw').textContent===newRaw&&!get('load-state').className.includes('error')&&!get('result').hidden);
  check('new success selected zero',JSON.parse(newRaw).id==='zero');
  return {project:'Atlas',passed:true,method:'Node VM with minimal handwritten element model; not browser, layout, real DOM or pointer evidence',check_count:checks.length,checks,modeled_states:states,actual_dom_states:0,browser_starts:0,captures:0,producer_runs:0,source_sha256:Object.fromEntries(['index.html','lesson.js','data.js','reader-model-check.cjs'].map(n=>[n,crypto.createHash('sha256').update(fs.readFileSync(n)).digest('hex')]))};
}
main().then(r=>process.stdout.write(JSON.stringify(r,null,2)+'\n')).catch(e=>{process.stdout.write(JSON.stringify({project:'Atlas',passed:false,error:e.stack,checks_completed:checks.length,load_state:get("load-state").textContent,result_hidden:get("result").hidden,raw:get("raw").textContent,answer_hidden:get("answer").hidden},null,2)+'\n');process.exitCode=1;});

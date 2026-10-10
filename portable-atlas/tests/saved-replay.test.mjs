import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import vm from 'node:vm';
import {fileURLToPath} from 'node:url';
import {createHash,webcrypto} from 'node:crypto';
const ROOT=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
const digest=s=>createHash('sha256').update(s).digest('hex');
const plain=x=>JSON.parse(JSON.stringify(x));

// DOM-shaped test fixture only: no browser, layout, screenshot, network or producer.
function load(relative,{wal=false}={}){
 const dir=path.join(ROOT,relative),html=fs.readFileSync(path.join(dir,'index.html'),'utf8'),nodes=new Map();let fetchCalls=0;
 class Element{
  constructor(tag='div'){this.tagName=tag;this.children=[];this.dataset={};this.attrs={};this.listeners={};this._text='';this.value='';this.hidden=false;this.disabled=false;this.open=false;}
  set id(v){this._id=v;nodes.set(v,this);}get id(){return this._id;}
  set textContent(v){this._text=String(v);this.children=[];}get textContent(){return this._text+this.children.map(x=>x.textContent??String(x)).join('');}
  append(...items){this.children.push(...items);}replaceChildren(...items){this._text='';this.children=[...items];}
  setAttribute(k,v){this.attrs[k]=String(v);if(k==='id')this.id=String(v);if(k.startsWith('data-'))this.dataset[k.slice(5)]=String(v);}
  removeAttribute(k){delete this.attrs[k];delete this[k];}
  addEventListener(k,fn){(this.listeners[k]??=[]).push(fn);}
  async emit(type){if(type==='click'&&this.disabled)return;for(const fn of [...(this.listeners[type]??=[]),...(this['on'+type]?[this['on'+type]]:[])])await fn.call(this,{target:this});}
 }
 for(const m of html.matchAll(/<([\w-]+)\b[^>]*\bid="([^"]+)"[^>]*>/g)){const e=new Element(m[1]);e.id=m[2];e.hidden=/\shidden(?:\s|>)/.test(m[0]);e.disabled=/\sdisabled(?:\s|>)/.test(m[0]);}
 const document={getElementById(id){assert.ok(nodes.has(id),'HTML lacks '+id);return nodes.get(id);},createElement:tag=>new Element(tag),createElementNS:(_ns,tag)=>new Element(tag),querySelectorAll(selector){const [,id,tag]=selector.match(/^#([\w-]+) (\w+)$/)??[];assert.ok(id,'unsupported DOM fixture selector');return nodes.get(id).children.filter(x=>x.tagName===tag);}};
 const context=vm.createContext({document,crypto:webcrypto,TextEncoder,Uint8Array,console,fetch(){fetchCalls++;throw Error('network forbidden in saved replay test');}});context.window=context;
 vm.runInContext(fs.readFileSync(path.join(dir,wal?'observation-data.js':'data.js'),'utf8'),context,{timeout:1000});
 vm.runInContext(fs.readFileSync(path.join(dir,wal?'saved-app.js':'lesson.js'),'utf8'),context,{timeout:1000});
 return {dir,nodes,context,fetchCalls:()=>fetchCalls,get:id=>nodes.get(id),async prediction(value='予想'){const p=nodes.get('prediction');p.value=value;await p.emit(wal?'change':'input');},async click(id){await nodes.get(id).emit('click');}};
}
const subjects={ast:'learning/continuations/programming-languages-compilers-runtimes/ast-stack',curves:'learning/continuations/ai-evaluation-safety/threshold-curves',fair:'learning/continuations/formal-methods-verification/fairness-starvation',wal:'review/pending/learning/continuations/database-engine-internals/wal-stale-reader-upgrade'};

test('配布用contractと原本provenanceを区別し、固定期待値をそのまま保持',()=>{
 for(const key of ['ast','curves','fair']){const t=load(subjects[key]),text=t.context.ATLAS_DATA_TEXT,b=JSON.parse(text),p=JSON.parse(fs.readFileSync(path.join(t.dir,'migration-provenance.json')));
  assert.equal(b.schemaVersion,2);assert.equal(b.kind,'atlas-selected-historical-observation');assert.equal(digest(text),p.publicBundleSHA256);assert.equal(digest(b.run_text),b.public_run_sha256);assert.equal(digest(b.expected_text),b.public_expected_sha256);assert.equal(digest(b.expected_text),b.source.expectedTextSHA256);assert.notEqual(digest(b.run_text),b.source.runTextSHA256);assert.equal(p.nonEnvironmentRecordsExactlyEqual,true);assert.equal(t.fetchCalls(),0);
 }
});

test('AST 12条件の全trace・終端・答え・予想変更による消去を実JSで確認',async()=>{
 const t=load(subjects.ast),run=JSON.parse(JSON.parse(t.context.ATLAS_DATA_TEXT).run_text),cases=run.records.filter(x=>x.kind==='case');let stages=0;
 for(const [i,row] of cases.entries()){
  await t.get('choices').children[i].emit('click');await t.prediction();await t.click('read');assert.equal(t.get('result').hidden,false,row.id+': '+t.get('load-state').textContent);
  let n=0;while(!t.get('next').disabled){await t.click('next');assert.ok(++n<100);}stages+=n+1;assert.equal(n,row.vm.trace.length+1);await t.click('answer-button');assert.equal(t.get('answer').hidden,false);assert.deepEqual(JSON.parse(t.get('raw').textContent),plain(row));await t.prediction('変更');assert.equal(t.get('result').hidden,true);assert.equal(t.get('answer').hidden,true);
 }
 assert.equal(cases.length,12);assert.ok(stages>40);assert.equal(t.fetchCalls(),0);
});

test('ROC/PRの全24境界で固定期待・未定義precision・SVG座標を確認',async()=>{
 const t=load(subjects.curves),b=JSON.parse(t.context.ATLAS_DATA_TEXT),expected=JSON.parse(b.expected_text);let count=0;
 for(const fixture of ['main','tie']){
  await t.click(fixture==='main'?'main-fixture':'tie-fixture');
  for(let i=0;i<expected[fixture].length;i++){
   await t.prediction();await t.click('read');assert.equal(t.get('result').hidden,false,t.get('load-state').textContent);const actual=JSON.parse(t.get('raw').textContent),wanted=expected[fixture][i];
   assert.equal(actual.ordinal,i);assert.deepEqual(['TP','FP','FN','TN'].map(k=>actual.counts[k]),wanted.slice(3,7));assert.deepEqual(['recall','fpr','precision'].map(k=>actual.metrics[k].fraction),wanted.slice(7));
   if(i===0){assert.equal(actual.pr,null);assert.equal(actual.metrics.precision.value,null);}assert.ok(t.get('roc').children.some(x=>x.tagName==='circle'));await t.click('answer-button');assert.equal(t.get('answer').hidden,false);count++;if(i<expected[fixture].length-1)await t.click('next');
  }
 }
 assert.equal(count,24);assert.equal(t.fetchCalls(),0);
});

test('公平性6列×4対象の全stepと反例表示・条件変更による消去を確認',async()=>{
 const t=load(subjects.fair),run=JSON.parse(JSON.parse(t.context.ATLAS_DATA_TEXT).run_text),cases=run.records.filter(x=>x.kind==='lasso'),regimes=['none','weak-processes','strong-enter1-only','weak-processes-plus-strong-enter1'];let count=0;
 for(const row of cases)for(const [i,regime] of regimes.entries()){
  await t.click('case-'+row.id);await t.click('regime-'+regime);await t.prediction();await t.click('load');assert.equal(t.get('result').hidden,false,t.get('load-status').textContent);
  let n=0;while(!t.get('next').disabled){await t.click('next');assert.ok(++n<100);}assert.equal(n,row.prefix_rows.length+row.cycle_rows.length);await t.click('answer-button');assert.equal(t.get('answer').hidden,false);assert.ok(t.get('verdict').textContent.includes('この列を許す = '+row.fair[i]));assert.ok(t.get('verdict').textContent.includes('反例 = '+row.fair_starvation_counterexample[i]));await t.prediction('変更');assert.equal(t.get('result').hidden,true);count++;
 }
 assert.equal(count,24);assert.equal(t.fetchCalls(),0);
});

test('3教材の改変・欠落を拒否し、旧結果を残さず、同じ配布データの復元で回復',async()=>{
 for(const key of ['ast','curves','fair']){const t=load(subjects[key]),original=t.context.ATLAS_DATA_TEXT,button=key==='fair'?'load':'read',status=key==='fair'?'load-status':'load-state';
  await t.prediction();await t.click(button);assert.equal(t.get('result').hidden,false);t.context.ATLAS_DATA_TEXT=original+' ';await t.click(button);assert.equal(t.get('result').hidden,true);assert.match(t.get(status).textContent,/ダイジェスト/);
  t.context.ATLAS_DATA_TEXT=undefined;await t.click(button);assert.equal(t.get('result').hidden,true);t.context.ATLAS_DATA_TEXT=original;await t.click(button);assert.equal(t.get('result').hidden,false);assert.equal(t.fetchCalls(),0);
 }
});

test('WAL固定13条件を保存値だけで比較し、13答えと8DBのSHAを確認',async()=>{
 const t=load(subjects.wal,{wal:true}),rows=plain(t.context.WAL_OBSERVATION.rows);let observed=0,refused=0;
 for(const row of rows){t.get('scenario').value=row.id;await t.get('scenario').emit('change');await t.prediction(row.run.result.status==='input_refusal'?'input':row.run.result.summary.category);await t.click('compare');assert.equal(t.get('results').hidden,false,row.id+': '+t.get('prediction-result').textContent);assert.match(t.get('prediction-result').textContent,/予想と一致/);assert.equal(t.get('answer').hidden,false);
  if(row.run.result.status==='observed'){observed++;assert.equal(JSON.parse(t.get('normal').textContent).final,row.expected.final_row);const db=fs.readFileSync(path.join(t.dir,'saved-db',row.id+'.sqlite'));assert.equal(digest(db),row.run.result.closed_db_sha256);}
  else{refused++;assert.match(t.get('classification').textContent,/exit2/);assert.equal(t.get('normal').textContent,'SQL未実行');}
 }
 assert.equal(observed,8);assert.equal(refused,5);assert.equal(t.fetchCalls(),0);
});

test('WALの未保存入力・改変・非選択を拒否し、復元で回復する',async()=>{
 const t=load(subjects.wal,{wal:true});await t.click('compare');assert.equal(t.get('results').hidden,true);await t.prediction('stale');await t.click('compare');assert.equal(t.get('results').hidden,false);
 const input=t.get('input-json').value;t.get('input-json').value='{}';await t.click('compare');assert.equal(t.get('results').hidden,true);assert.match(t.get('prediction-result').textContent,/保存条件にない/);t.get('input-json').value=input;
 const old=t.context.WAL_OBSERVATION.rows[0].run.result.summary.final_row;t.context.WAL_OBSERVATION.rows[0].run.result.summary.final_row=999;await t.click('compare');assert.equal(t.get('results').hidden,true);assert.match(t.get('prediction-result').textContent,/SHA/);t.context.WAL_OBSERVATION.rows[0].run.result.summary.final_row=old;await t.click('compare');assert.equal(t.get('results').hidden,false);assert.equal(t.fetchCalls(),0);
});

test('非同期SHA照合の途中で予想を変更しても古い表示を復活させない',async()=>{
 for(const key of ['ast','curves','fair','wal']){const wal=key==='wal',t=load(subjects[key],{wal});await t.prediction(wal?'stale':'予想');const pending=t.click(wal?'compare':key==='fair'?'load':'read');await t.prediction(wal?'busy':'変更');await pending;assert.equal(t.get(wal?'results':'result').hidden,true);assert.equal(t.fetchCalls(),0);}
});

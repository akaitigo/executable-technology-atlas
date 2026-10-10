// Literal oracle. No producer import, synthetic ESM linker, or evaluation algorithm.
import {readFileSync,readdirSync,statSync} from 'node:fs';
import {createHash} from 'node:crypto';
import {spawnSync} from 'node:child_process';
import assert from 'node:assert/strict';
import {fileURLToPath} from 'node:url';
import {join,relative} from 'node:path';
const root=fileURLToPath(new URL('./',import.meta.url));
const read=n=>JSON.parse(readFileSync(join(root,n),'utf8')),digest=p=>createHash('sha256').update(readFileSync(p)).digest('hex');
function files(dir=root){return readdirSync(dir).flatMap(n=>statSync(join(dir,n)).isDirectory()?files(join(dir,n)):[join(dir,n)]);}
function snapshot(){return Object.fromEntries(files().sort().map(p=>[relative(root,p),{sha256:digest(p),mtime_ns:statSync(p,{bigint:true}).mtimeNs.toString()}]));}
export function verify(raw){
 const t=read('expected-table.json'),c=read('contracts.json');assert.equal(raw.rows.length,5);assert.equal(new Set(raw.rows.map(r=>r.pid)).size,5);
 for(let i=0;i<5;i++){
  const r=raw.rows[i],spec=c.cases[i],e=t.rows.find(x=>x.id===r.id);assert.equal(r.id,spec.id);assert.deepEqual(r.graph,e.graph);assert.deepEqual(r.graph,spec.graph);assert.equal(r.cycle,e.cycle);assert.equal(r.entry,spec.entry);
  for(const k of ['exit','exception_class','final_value','events'])assert.deepEqual(r[k],e.expected[k],`${r.id}/${k}`);
  assert.equal(r.signal,null);assert.equal(r.spawn_error,null);assert.equal(r.pid,r.process.pid);assert.equal(r.process.node,process.version);assert.ok(Number.isInteger(r.pid)&&r.pid>0);
  const lines=r.stdout.trim().split('\n').map(x=>JSON.parse(x));assert.deepEqual(lines,[{process:r.process},...r.events]);
  if(e.expected.exception_class){const err=JSON.parse(r.stderr);assert.equal(err.class,'ReferenceError');assert.equal(err.message,r.exception_message);assert.ok(err.message.includes('before initialization'));assert.equal(r.final_value,null);}
  else{assert.equal(r.stderr,'');assert.equal(r.exception_message,null);}
  // Literal import edges only; this is not a linker/evaluation implementation.
  for(const [module,edges] of Object.entries(e.graph)){
   const src=readFileSync(join(root,'fixtures',r.id,module+'.mjs'),'utf8');const imports=[...src.matchAll(/from '\.\/([ab])\.mjs'/g)].map(x=>x[1]);assert.deepEqual(imports,edges,`${r.id}/${module}/edges`);
  }
 }
 return true;
}
const before=snapshot();const p=spawnSync(process.execPath,['experiment.mjs'],{cwd:root,encoding:'utf8',env:{...process.env,NODE_OPTIONS:''}});assert.equal(p.status,0);assert.equal(p.stderr,'');const raw=JSON.parse(p.stdout);verify(raw);
const rejected=[];
for(const name of ['missing-error','invented-A-event','delayed-value','snapshot-updated','exit-hidden']){
 const x=structuredClone(raw);
 if(name==='missing-error')x.rows[0].exception_class=null;
 else if(name==='invented-A-event')x.rows[0].events.splice(1,0,{event:'A:eval'});
 else if(name==='delayed-value')x.rows[1].final_value=2;
 else if(name==='snapshot-updated')x.rows[4].events.find(e=>e.event==='entry:snapshot-after').value=2;
 else x.rows[2].exit=0;
 assert.throws(()=>verify(x));rejected.push(name);
}
let run_id=null;
if(files().includes(join(root,'observation-data.js'))){
 const saved=JSON.parse(readFileSync(join(root,'observation-data.js'),'utf8').replace(/^window\.CYCLE_OBSERVATION=/,'').trim().replace(/;$/,''));verify(saved);run_id=saved.run_id;assert.deepEqual(saved,read(`observations/${run_id}/raw.json`));
 for(const [n,d] of Object.entries(saved.source_digests))assert.equal(digest(join(root,n)),d,n);
 const idx=read(`observations/${run_id}/artifact-index.json`);for(const [n,d] of Object.entries(idx.files))assert.equal(digest(join(root,'observations',run_id,n)),d,n);
}
assert.deepEqual(snapshot(),before);console.log(JSON.stringify({status:'passed',cases:5,separate_fresh_processes:5,literal_events_checked:true,negative_controls_rejected:rejected,run_id,read_only_files:Object.keys(before).length,all_hash_mtime_equal:true}));

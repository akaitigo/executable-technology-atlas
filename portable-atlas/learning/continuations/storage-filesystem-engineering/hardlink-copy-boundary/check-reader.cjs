"use strict";
// Atlas: a small in-memory document model. This is not browser or image QA.
const fs=require("node:fs"),path=require("node:path"),vm=require("node:vm"),assert=require("node:assert/strict"),crypto=require("node:crypto");
const root=__dirname,read=n=>fs.readFileSync(path.join(root,n));
const manifest=JSON.parse(read("reader-data.json"));
const record=JSON.parse(read(manifest.observation.path));
const model={};const checks=[];let fetching;
class Element{constructor(){this.textContent="";this.children=[];this.listeners={};this.hidden=false;this.disabled=false;this.checked=false;this.value="";this.dataset={};this.open=false;}addEventListener(n,f){this.listeners[n]=f;}append(x){this.children.push(x);}replaceChildren(...x){this.children=x;this.textContent="";}}
for(const id of ["result","answer","answer-text","answer-button","raw-details","comparison","diagram","raw","phase-title","operation","measured-at","result-kind","status","load","prediction","conditions","reset"])model[id]=new Element();
const radios=Object.fromEntries(record.phases.map(p=>[p.id,new Element()]));for(const [id,e] of Object.entries(radios))e.value=id;radios.created.checked=true;
const document={querySelector(s){if(s==="input[name=phase]:checked")return Object.values(radios).find(x=>x.checked);if(s==='input[value=created]')return radios.created;assert(s.startsWith("#"));return model[s.slice(1)];},createElement(){return new Element();}};
function response(bytes,status=200){return{ok:status===200,status,arrayBuffer:async()=>Uint8Array.from(bytes).buffer,json:async()=>JSON.parse(bytes.toString())};}
function normal(url){return Promise.resolve(response(read(url)));}
fetching=normal;
const context=vm.createContext({document,fetch:(...args)=>fetching(...args),crypto:crypto.webcrypto,TextDecoder,AbortController,Uint8Array,Array,Promise,JSON,Number,Error,String,parseInt});
vm.runInContext(read("lesson.js").toString(),context);
const event=(id,name="click")=>model[id].listeners[name]();
const mark=n=>checks.push(n);
function cleared(){assert.equal(model.result.hidden,true);assert.equal(model.answer.hidden,true);assert.equal(model["answer-button"].disabled,true);assert.equal(model.raw.textContent,"");assert.equal(model.comparison.children.length,0);assert.equal(model.diagram.children.length,0);}
function select(id){for(const [name,e]of Object.entries(radios))e.checked=name===id;event("conditions","change");}
function currentRows(){return model.comparison.children.map(r=>r.children.map(c=>c.textContent));}
(async()=>{
 event("reset");cleared();mark("reset clears all results");
 const expected=JSON.parse(read("expected.json"));
 for(const [i,p] of record.phases.entries()){
   select(p.id);await event("load");assert.equal(model.result.hidden,false);
   const rows=currentRows();for(const [j,name] of ["original","alias","copy"].entries()){
     const w=expected.phases[i].files[name];assert.equal(rows[j][1],w?JSON.stringify(Buffer.from(w.hex,"hex").toString()):"名前なし");assert.equal(rows[j][2],rows[j][1]);assert.equal(rows[j][3],w?String(w.nlink):"—");assert.equal(rows[j][4],w?w.identity:"—");
   }
   assert.deepEqual(JSON.parse(model.raw.textContent).phase,p);assert.equal(model["result-kind"].textContent,p.id==="duplicate_link_rejected"?"意図した失敗：FileExistsError / EEXIST":"正常な操作後の観測");
   event("answer-button");assert.equal(model.answer.hidden,false);mark(p.id+" saved values, comparison, answer");
 }
 model.prediction.value="新しい予想";event("prediction","input");cleared();mark("prediction edit invalidates results and answer");
 await event("load");select("created");cleared();mark("condition change invalidates results");
 fetching=()=>Promise.resolve(response(Buffer.from("unavailable"),503));await event("load");cleared();assert.match(model.status.textContent,/失敗/);mark("fetch failure is not expected EEXIST");
 fetching=url=>Promise.resolve(response(url===manifest.observation.path?Buffer.from(read(url).toString()+" "):read(url)));await event("load");cleared();assert.match(model.status.textContent,/一致しません/);mark("changed saved file fails digest");
 fetching=normal;await event("load");assert.equal(model.result.hidden,false);mark("reload after failure recovers");
 let resolveOld;fetching=url=>url==="reader-data.json"?new Promise(r=>resolveOld=r):normal(url);const oldSuccess=event("load");event("reset");resolveOld(response(read("reader-data.json")));await oldSuccess;cleared();mark("old success after reset remains discarded");
 let rejectOld;fetching=url=>url==="reader-data.json"?new Promise((_,r)=>rejectOld=r):normal(url);const oldError=event("load");select("alias_overwritten");fetching=normal;await event("load");const fresh=model.raw.textContent;rejectOld(Error("old fetch failure"));await oldError;assert.equal(model.raw.textContent,fresh);assert.equal(model.result.hidden,false);mark("old error cannot erase fresh success");
 let delayed;fetching=url=>url===manifest.observation.path?new Promise(r=>delayed=r):normal(url);const pending=event("load");await new Promise(r=>setImmediate(r));model.prediction.value="変更";event("prediction","input");delayed(response(read(manifest.observation.path)));await pending;cleared();mark("prediction during loading discards old response");
 const incomplete=read("observations/attempt-1/run.json");const alteredManifest={...manifest,observation:{...manifest.observation,sha256:crypto.createHash("sha256").update(incomplete).digest("hex")}};
 fetching=url=>Promise.resolve(response(url==="reader-data.json"?Buffer.from(JSON.stringify(alteredManifest)):url===manifest.observation.path?incomplete:read(url)));await event("load");cleared();assert.match(model.status.textContent,/完了した測定結果ではありません/);mark("preparation failure cannot display as completed measurement");
 fetching=normal;await event("load");assert.equal(model.result.hidden,false);mark("final recovery");
 console.log(JSON.stringify({project:"Atlas",passed:true,checks:checks.length,details:checks,kind:"in-memory document model",browser_started:false,images_reviewed:false,new_os_experiment:false,source_sha256:crypto.createHash("sha256").update(read("lesson.js")).digest("hex")},null,2));
})().catch(e=>{console.error(e);process.exitCode=1;});

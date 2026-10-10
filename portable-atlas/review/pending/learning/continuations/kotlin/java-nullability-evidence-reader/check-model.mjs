// Finite data projection check, not browser/DOM testing.
import fs from "node:fs";
import assert from "node:assert/strict";
import {projectCase} from "./evidence-model.mjs";
const read=p=>JSON.parse(fs.readFileSync(new URL(p,import.meta.url),"utf8"));
const r=read("evidence/evidence/diagnostics/java-nullability-enhancement-process-pilot.json"),e=read("evidence/labs/java-nullability-enhancement-process-pilot/expected.json");
const checks=[];
for(const [id,kind,exit] of [["normal","normal",0],["boundary","normal",0],["failure","runtime-failure",1],["rejection","compile-rejection",1]]){
 const v=projectCase(r,e,id);assert.equal(v.kind,kind);
 if(id==="rejection"){assert.deepEqual(v.raw,{compile:r.compile.rejection});assert.equal(v.raw.compile.exit_code,exit);assert.equal("runtime" in v.raw,false);}
 else{assert.deepEqual(v.raw.runtime,r.runtime_cases.find(row=>row.name===id));assert.equal(v.raw.runtime.exit_code,exit);}
 checks.push({case:id,passed:true});
}
assert.match(projectCase(r,e,"normal").expectation,/RESULT=5/);
assert.match(projectCase(r,e,"boundary").expectation,/RESULT=0/);
assert.match(projectCase(r,e,"failure").digestNote,/全文は未保存/);
assert.throws(()=>projectCase(r,e,"unknown"));checks.push({case:"unknown condition rejected",passed:true});
const bad=structuredClone(r);bad.compile.rejection.diagnostic_id="UNSAFE_CALL";
assert.throws(()=>projectCase(bad,e,"rejection"));checks.push({case:"wrong diagnostic rejected",passed:true});
const missing=structuredClone(r);missing.runtime_cases.pop();
assert.throws(()=>projectCase(missing,e,"normal"));checks.push({case:"missing runtime rejected",passed:true});
console.log(JSON.stringify({passed:true,checks,check_count:checks.length,scope:"Finite data projection; no browser/DOM or native runtime",native_executions:0,browser_executions:0},null,2));

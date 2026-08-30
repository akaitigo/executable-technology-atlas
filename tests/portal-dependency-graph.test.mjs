import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import path from 'node:path';
import test from 'node:test';
import { auditPortalGraph, discoverPortalOutputs } from '../scripts/lib/portal-dependency-graph.mjs';

const root=process.cwd();
const config=JSON.parse(await readFile(path.join(root,'contracts/portal-evidence-dependency-inputs.json'),'utf8'));
const fixture=JSON.parse(await readFile(path.join(root,'fixtures/evidence-dependency/digest-only-closure.json'),'utf8'));
const proof=JSON.parse(await readFile(path.join(root,'evidence/scenarios/portal-dependency-current.proof.json'),'utf8'));

test('Portal Graph入力はSource TreeやDefault BranchではなくRepository内の固定memberだけを列挙する',()=>{assert.equal(config.groups.length,4);assert.deepEqual(config.groups.map((item)=>item.kind),['source','harness','runtime','profile']);const serialized=JSON.stringify(config);assert.doesNotMatch(serialized,/default_branch|\.git\/|submodule/i);});
test('Portal自身のbounded Closureは97 Subjectのsubject-definitiveを0のまま分離する',()=>{assert.equal(proof.completion_boundary.portal_completion_class,'bounded-complete');assert.equal(proof.completion_boundary.subject_definitive_count,0);assert.equal(proof.completion_boundary.subject_auto_promotion,false);});
test('digest-only負例はSource変更後の古いrunをCore診断で拒否する契約を固定する',()=>{assert.equal(fixture.inputKind,'source');assert.equal(fixture.expectedExitCode,1);assert.match(fixture.expectedDiagnostic,/digest書換えだけ/);assert.ok(fixture.observedAfterRunSeconds>0);});
test('Portal GraphはCore Schema、実Digest、run binding、Proof/Closure構造へ一致する',async()=>{const graph=JSON.parse(await readFile(path.join(root,'evidence/dependency-graph.json'),'utf8'));const schema=JSON.parse(await readFile(path.join(root,'contracts/schemas/evidence-dependency-graph.schema.json'),'utf8'));const result=await auditPortalGraph(root,graph,schema);assert.equal(result.ok,true,result.errors.join('; '));assert.equal(result.summary.inputs,4);assert.ok(result.summary.outputs>=20);assert.equal(result.summary.runs,1);assert.equal(result.summary.structures,2);});
test('全Evidence wrapperとCoreが探索するreportをrequired outputから退避できない',async()=>{const graph=JSON.parse(await readFile(path.join(root,'evidence/dependency-graph.json'),'utf8'));const discovered=await discoverPortalOutputs(root);assert.deepEqual(graph.required_outputs,discovered);for(const required of ['evidence/import.integrity.evidence.json','evidence/non-regression.evidence.json','evidence/reports/performance.json','evidence/reports/router-eval.json','provenance.yaml'])assert.ok(graph.required_outputs.includes(required),required);});

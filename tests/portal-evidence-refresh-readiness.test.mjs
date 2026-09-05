import assert from 'node:assert/strict';
import { spawnSync } from 'node:child_process';
import { readFile, stat } from 'node:fs/promises';
import path from 'node:path';
import test from 'node:test';
import { applyPortalEvidenceRefreshPolicyNegative, evaluatePortalEvidenceRefreshReadiness, loadPortalEvidenceRefreshPolicy } from '../scripts/lib/portal-evidence-refresh-readiness.mjs';

const root=process.cwd();
const {policy,schema}=await loadPortalEvidenceRefreshPolicy(root);
const negative=JSON.parse(await readFile(path.join(root,'fixtures/portal-evidence-refresh-policy/negative-cases.json'),'utf8'));

test('Evidence wrapperとGraph freshnessを実再実行entrypointへ結ぶ',async()=>{
  const result=await evaluatePortalEvidenceRefreshReadiness(root,policy,schema);assert.equal(result.ok,true,result.errors.join(', '));const report=result.report;
  assert.ok(['blocked','ready'].includes(report.status));assert.equal(report.summary.wrappers,8);assert.equal(report.summary.currentWrappers+report.summary.staleWrappers,8);assert.equal(report.summary.inputs,4);assert.equal(report.summary.recordedOutputs+report.summary.missingDiscoveredOutputs,report.summary.discoveredOutputs);assert.equal(report.summary.discoveredOutputs,38);assert.equal(report.boundary.completionEffect,'none');if(report.status==='ready'){assert.equal(report.summary.currentWrappers,8);assert.equal(report.summary.staleWrappers,0);assert.equal(report.summary.inputsChangedSinceRun,0);assert.equal(report.summary.missingDiscoveredOutputs,0);assert.equal(report.summary.graphCurrent,true);assert.equal(report.summary.currentRerun,true);}else{assert.equal(report.summary.currentRerun,false);}
});

test('stage/wrapper縮小・pipeline付替え・digest/skip/runtime代替・記録status昇格を拒否する',async()=>{
  assert.equal(negative.cases.length,9);
  for(const item of negative.cases){const result=await evaluatePortalEvidenceRefreshReadiness(root,applyPortalEvidenceRefreshPolicyNegative(policy,item),schema);assert.equal(result.ok,false,item.caseId);assert.ok(result.errors.includes(item.expectedDiagnostic),`${item.caseId}: ${result.errors.join(', ')}`);}
});

test('CLIは現在のblockerをread-only表示し、ready必須時だけfail-closedする',async()=>{
  const current=await evaluatePortalEvidenceRefreshReadiness(root,policy,schema);
  const protectedPaths=['evidence/dependency-graph.json',...policy.requiredWrappers];
  const before=Object.fromEntries(await Promise.all(protectedPaths.map(async(relative)=>[relative,(await stat(path.join(root,relative))).mtimeMs])));
  const observed=spawnSync(process.execPath,['scripts/atlas-portal.mjs','evidence-status'],{cwd:root,encoding:'utf8'});
  assert.equal(observed.status,0,observed.stderr);const report=JSON.parse(observed.stdout);
  assert.equal(report.ok,true);assert.equal(report.status,current.report.status);assert.equal(report.summary.currentWrappers+report.summary.staleWrappers,8);assert.equal(report.summary.staleWrappers,current.report.summary.staleWrappers);assert.equal(report.summary.inputsChangedSinceRun,current.report.summary.inputsChangedSinceRun);assert.equal(report.summary.missingDiscoveredOutputs,current.report.summary.missingDiscoveredOutputs);assert.equal(report.summary.currentRerun,current.report.summary.currentRerun);assert.equal(report.boundary.completionEffect,'none');assert.equal(report.boundary.subjectDefinitiveEffect,'none');assert.equal(report.boundary.distributionEffect,'none');assert.equal(report.boundary.rootDefinitiveEffect,'none');
  const required=spawnSync(process.execPath,['scripts/atlas-portal.mjs','evidence-status','--require-ready'],{cwd:root,encoding:'utf8'});assert.equal(required.status,current.report.status==='ready'?0:1);assert.equal(JSON.parse(required.stdout).status,current.report.status);
  const unknown=spawnSync(process.execPath,['scripts/atlas-portal.mjs','evidence-status','--promote'],{cwd:root,encoding:'utf8'});assert.equal(unknown.status,2);assert.match(unknown.stderr,/未対応の引数/);
  const after=Object.fromEntries(await Promise.all(protectedPaths.map(async(relative)=>[relative,(await stat(path.join(root,relative))).mtimeMs])));assert.deepEqual(after,before);
});

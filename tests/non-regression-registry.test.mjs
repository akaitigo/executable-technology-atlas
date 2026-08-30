import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import path from 'node:path';
import test from 'node:test';
import { evaluateRegistryEvidence, validateRegistryPreflight } from '../scripts/lib/registry.mjs';

const root=process.cwd();const fixtureRoot=path.join(root,'fixtures');
const registry=JSON.parse(await readFile(path.join(fixtureRoot,'registry.json'),'utf8'));
const catalog=JSON.parse(await readFile(path.join(fixtureRoot,'core/catalog.release.json'),'utf8')).payload.catalog;
const negative=JSON.parse(await readFile(path.join(fixtureRoot,'registry/invalid-registry-cases.json'),'utf8'));

test('Registry Non-regressionは97 Subject・7 fixed audit・12負例を完全一致で受理する',async()=>{
  const preflight=await validateRegistryPreflight(registry,fixtureRoot,catalog);const result=evaluateRegistryEvidence(preflight,negative);
  assert.deepEqual(result,{ok:true,policyPass:true,negativePass:true,catalogSubjects:97,fixedCommitAudits:7,negativeCases:12,expectedNegativeCases:12});
});

test('Registry Policyまたは負例分母の縮小をNon-regressionが拒否する',async()=>{
  const preflight=await validateRegistryPreflight(registry,fixtureRoot,catalog);
  const weakened=structuredClone(preflight);delete weakened.fileBindingPolicy;assert.equal(evaluateRegistryEvidence(weakened,negative).policyPass,false);
  const reduced=structuredClone(negative);reduced.cases.pop();assert.equal(evaluateRegistryEvidence(preflight,reduced).negativePass,false);
  const relabeled=structuredClone(negative);relabeled.cases[0].expectedResult='ignored';assert.equal(evaluateRegistryEvidence(preflight,relabeled).negativePass,false);
});

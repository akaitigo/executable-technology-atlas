import assert from 'node:assert/strict';
import { cp, mkdtemp, readFile, rm, symlink } from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';
import test from 'node:test';
import { validateRegistryPreflight } from '../scripts/lib/registry.mjs';

const root=process.cwd();const fixtureRoot=path.join(root,'fixtures');
const registry=JSON.parse(await readFile(path.join(fixtureRoot,'registry.json'),'utf8'));
const catalog=JSON.parse(await readFile(path.join(fixtureRoot,'core/catalog.release.json'),'utf8')).payload.catalog;
const negative=JSON.parse(await readFile(path.join(fixtureRoot,'registry/invalid-registry-cases.json'),'utf8'));

async function applyScenario(mutated,scenario,scenarioRoot){
  switch(scenario.mutation){
    case 'duplicate-first-fixed-commit-audit': mutated.fixedCommitAudits.push(structuredClone(mutated.fixedCommitAudits[0]));break;
    case 'duplicate-first-release': mutated.releases.push(structuredClone(mutated.releases[0]));break;
    case 'replace-first-fixed-commit-subject-with-unknown': mutated.fixedCommitAudits[0].subjectId='unknown-subject';break;
    case 'replace-first-fixed-commit-repository': mutated.fixedCommitAudits[0].repository=mutated.fixedCommitAudits[1].repository;break;
    case 'replace-second-fixed-commit-file-with-first-file': mutated.fixedCommitAudits[1].file=mutated.fixedCommitAudits[0].file;break;
    case 'replace-first-fixed-commit-file-with-parent-path': mutated.fixedCommitAudits[0].file='../outside.json';break;
    case 'replace-first-fixed-commit-file-with-normalized-parent-segment': mutated.fixedCommitAudits[0].file=`fixed-commit-audits/../${mutated.fixedCommitAudits[0].file}`;break;
    case 'replace-first-fixed-commit-file-with-absolute-path': mutated.fixedCommitAudits[0].file=path.resolve(scenarioRoot,mutated.fixedCommitAudits[0].file);break;
    case 'replace-first-fixed-commit-file-with-missing-path': mutated.fixedCommitAudits[0].file='registry/missing.json';break;
    case 'replace-first-fixed-commit-file-with-directory': mutated.fixedCommitAudits[0].file='registry';break;
    case 'replace-first-fixed-commit-file-with-symlink': {
      const link='registry/fixed-commit-link.json';
      await symlink(path.relative(path.join(scenarioRoot,'registry'),path.join(scenarioRoot,mutated.fixedCommitAudits[0].file)),path.join(scenarioRoot,link));
      mutated.fixedCommitAudits[0].file=link;
      break;
    }
    case 'replace-first-fixed-commit-file-with-symlink-directory': {
      const link='registry/fixed-commit-directory-link';const original=mutated.fixedCommitAudits[0].file;
      await symlink(path.relative(path.join(scenarioRoot,'registry'),path.join(scenarioRoot,'fixed-commit-audits')),path.join(scenarioRoot,link));
      mutated.fixedCommitAudits[0].file=`${link}/${path.basename(original)}`;
      break;
    }
    default: assert.fail(`unknown mutation: ${scenario.mutation}`);
  }
}

test('Registryは重複なし・Catalog binding・fixture root内の通常Fileとして受理する',async()=>{
  const result=await validateRegistryPreflight(registry,fixtureRoot,catalog);
  assert.equal(result.result,'pass',result.errors.join('; '));
  assert.equal(result.catalogSubjects,97);
  assert.deepEqual(result.collections,{releases:7,depthReferences:1,authorityReviews:1,evidenceDependencies:0,fixedCommitAudits:7,definitiveV2:0});
  assert.equal(result.duplicatePolicy,'reject');assert.equal(result.fileBindingPolicy,'one-registry-reference-per-file');assert.equal(result.pathPolicy,'fixture-root-regular-files-only');assert.equal(result.parentTraversalPolicy,'reject');assert.equal(result.symlinkPolicy,'reject-all-components');
});

test('Registry負例を入力読込前にfail-closed拒否する',async()=>{
  const temporary=await mkdtemp(path.join(os.tmpdir(),'atlas-registry-unit-'));
  try{
    const copiedFixtures=path.join(temporary,'fixtures');await cp(fixtureRoot,copiedFixtures,{recursive:true});
    for(const scenario of negative.cases){const mutated=structuredClone(registry);await applyScenario(mutated,scenario,copiedFixtures);const result=await validateRegistryPreflight(mutated,copiedFixtures,catalog);assert.equal(result.result,'fail',scenario.id);assert.ok(result.errors.some((error)=>error.includes(scenario.expectedDiagnostic)),`${scenario.id}: ${result.errors}`);}
  }finally{await rm(temporary,{recursive:true,force:true});}
});

test('Catalog外Subjectとrepository binding差替えを拒否する',async()=>{
  const unknown=structuredClone(registry);unknown.fixedCommitAudits[0].subjectId='unknown-subject';const unknownResult=await validateRegistryPreflight(unknown,fixtureRoot,catalog);assert.equal(unknownResult.result,'fail');assert.ok(unknownResult.errors.some((error)=>error.includes('Catalog外subject')));
  const rebound=structuredClone(registry);rebound.fixedCommitAudits[0].repository='postgresql-reference-atlas';const reboundResult=await validateRegistryPreflight(rebound,fixtureRoot,catalog);assert.equal(reboundResult.result,'fail');assert.ok(reboundResult.errors.some((error)=>error.includes('repositoryがCatalogと一致しません')));
});

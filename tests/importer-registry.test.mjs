import assert from 'node:assert/strict';
import { cp, mkdtemp, readFile, rm, symlink, writeFile } from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';
import test from 'node:test';
import { recordRegistryPreflightFailure, validateRegistryPreflight } from '../scripts/lib/registry.mjs';

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
      const link='registry/fixed-commit-link.json';await symlink(path.relative(path.join(scenarioRoot,'registry'),path.join(scenarioRoot,mutated.fixedCommitAudits[0].file)),path.join(scenarioRoot,link));mutated.fixedCommitAudits[0].file=link;break;
    }
    case 'replace-first-fixed-commit-file-with-symlink-directory': {
      const link='registry/fixed-commit-directory-link';const original=mutated.fixedCommitAudits[0].file;await symlink(path.relative(path.join(scenarioRoot,'registry'),path.join(scenarioRoot,'fixed-commit-audits')),path.join(scenarioRoot,link));mutated.fixedCommitAudits[0].file=`${link}/${path.basename(original)}`;break;
    }
    default: assert.fail(`unknown mutation: ${scenario.mutation}`);
  }
}

test('Importerは登録Envelopeを読む前に共有Registry preflightとatomic failure recorderを呼ぶ',async()=>{
  const source=await readFile(path.join(root,'scripts/import-releases.mjs'),'utf8');
  const preflight=source.indexOf('const registryPreflight=await validateRegistryPreflight');
  const failureRecord=source.indexOf('await recordRegistryPreflightFailure');
  const firstRegisteredEnvelope=source.indexOf('for(const item of registry.evidenceDependencies');
  assert.ok(preflight>=0);assert.ok(failureRecord>preflight);assert.ok(firstRegisteredEnvelope>failureRecord);
});

test('12 Registry負例はImport Reportだけをatomic更新しlast-known-good IndexとBootstrapを保持する',async()=>{
  const temporary=await mkdtemp(path.join(os.tmpdir(),'atlas-importer-registry-'));
  try{
    const copiedFixtures=path.join(temporary,'fixtures');await cp(fixtureRoot,copiedFixtures,{recursive:true});
    const indexPath=path.join(temporary,'index.json');const bootstrapPath=path.join(temporary,'bootstrap.json');const reportPath=path.join(temporary,'report.json');
    const indexBytes=Buffer.from('last-known-good-index\n');const bootstrapBytes=Buffer.from('last-known-good-bootstrap\n');await writeFile(indexPath,indexBytes);await writeFile(bootstrapPath,bootstrapBytes);
    for(const scenario of negative.cases){const mutated=structuredClone(registry);await applyScenario(mutated,scenario,copiedFixtures);const result=await validateRegistryPreflight(mutated,copiedFixtures,catalog);assert.equal(result.result,'fail',scenario.id);assert.ok(result.errors.some((error)=>error.includes(scenario.expectedDiagnostic)),`${scenario.id}: ${result.errors}`);await recordRegistryPreflightFailure(reportPath,result);assert.deepEqual(await readFile(indexPath),indexBytes,scenario.id);assert.deepEqual(await readFile(bootstrapPath),bootstrapBytes,scenario.id);const report=JSON.parse(await readFile(reportPath,'utf8'));assert.equal(report.verdict,'fail');assert.equal(report.registry.result,'fail');}
  }finally{await rm(temporary,{recursive:true,force:true});}
});

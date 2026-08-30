import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import path from 'node:path';
import test from 'node:test';

const root=process.cwd();
const packageJson=JSON.parse(await readFile(path.join(root,'package.json'),'utf8'));
const lock=JSON.parse(await readFile(path.join(root,'package-lock.json'),'utf8'));
const workflow=await readFile(path.join(root,'.github/workflows/publication.yml'),'utf8');
const importer=await readFile(path.join(root,'scripts/import-releases.mjs'),'utf8');

test('正規lockfileはImporter Schema検証用Ajvをintegrity付きで固定する',()=>{
  assert.equal(packageJson.dependencies.ajv,'^8.17.1');assert.equal(packageJson.dependencies['ajv-formats'],'^3.0.1');
  assert.equal(lock.packages[''].dependencies.ajv,packageJson.dependencies.ajv);assert.equal(lock.packages[''].dependencies['ajv-formats'],packageJson.dependencies['ajv-formats']);
  assert.equal(lock.packages['node_modules/ajv'].version,'8.20.0');assert.match(lock.packages['node_modules/ajv'].integrity,/^sha512-/);
  assert.equal(lock.packages['node_modules/ajv-formats'].version,'3.0.1');assert.match(lock.packages['node_modules/ajv-formats'].integrity,/^sha512-/);
  assert.match(importer,/schemaValidators/);assert.match(importer,/validateRegistryPreflight/);
});

test('clean-room CIは依存導入後のfull Importer・Non-regression・Build・Publication・Core Gateを省略しない',()=>{
  const ordered=['npm ci --ignore-scripts --no-audit --no-fund','npm run import','npm run non-regression','npm test','npm run build','npm run dependency:graph:check','npm run gate','npm run dependency:negative','atlas audit','certificate verify','--gate evidence-dependency'];
  let previous=-1;for(const command of ordered){const index=workflow.indexOf(command);assert.ok(index>previous,`${command} must follow prior required command`);previous=index;}
  assert.ok((workflow.match(/git diff --exit-code/g)??[]).length>=2);assert.ok(workflow.lastIndexOf('git diff --exit-code')>previous,'final tracked-mutation rejection must follow Core gates');
  assert.equal(packageJson.scripts.test,'node --test tests/*.test.mjs');assert.equal(packageJson.scripts.gate,'node scripts/publication-gate.mjs');
});

import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import path from 'node:path';
import test from 'node:test';
import { parse } from 'yaml';

const root=process.cwd();
const source=await readFile(path.join(root,'.github/workflows/publication.yml'),'utf8');
const workflow=parse(source);

test('CI権限をcontents readだけに限定する',()=>assert.deepEqual(workflow.permissions,{contents:'read'}));
test('公式Action、Node、Go、Core v1、Core v2正式mainを不変のVersionへ固定する',()=>{for(const value of ['actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1','actions/setup-node@820762786026740c76f36085b0efc47a31fe5020','actions/setup-go@b7ad1dad31e06c5925ef5d2fc7ad053ef454303e','node-version: 22.13.0','go-version: 1.26.0','cf9e6e2d981305c83f970c1f21a1ddc9c1109263','072d7ca77981f51754e824d70c6d4ecd55ea67e5','cmp contracts/schemas/definitive.schema.json','cmp contracts/schemas/definitive-migration.schema.json','cmp contracts/schemas/definitive-certificate.schema.json','cmp contracts/reference/MIGRATION_DEFINITIVE_V2.md'])assert.match(source,new RegExp(value.replace(/[.*+?^${}()|[\]\\]/g,'\\$&')));});
test('秘密情報と書込権限を使わない',()=>{assert.doesNotMatch(source,/secrets\.|pull_request_target|contents:\s*write|id-token:\s*write/);assert.match(source,/persist-credentials: false/);});
test('lockfile取込、非後退、Graph負例、Gate、Core audit、Certificate、非変更を全て検証する',()=>{for(const value of ['npm ci --ignore-scripts --no-audit --no-fund','npm run non-regression','npm test','npm run dependency:graph:check','npm run dependency:negative','--gate evidence-dependency','npm run gate','atlas audit','certificate verify','git diff --exit-code'])assert.ok(source.includes(value));});

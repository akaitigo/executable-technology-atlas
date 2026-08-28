import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import path from 'node:path';
import test from 'node:test';

const root=process.cwd();
test('Security Headerが主要境界を拒否する',async()=>{const headers=await readFile(path.join(root,'public/_headers'),'utf8');for(const token of ["default-src 'self'","object-src 'none'","frame-ancestors 'none'","Referrer-Policy: no-referrer","Permissions-Policy:"])assert.match(headers,new RegExp(token.replace(/[.*+?^${}()|[\]\\]/g,'\\$&')));});
test('Fallback fixtureが除外・実行困難・失効を保持する',async()=>{const fixture=JSON.parse(await readFile(path.join(root,'fixtures/failure-scenarios.json'),'utf8'));const states=new Set(fixture.scenarios.map((item)=>item.state));for(const state of ['excluded','infeasible','expired'])assert.ok(states.has(state));});
test('Runtime Indexはfixed-release-onlyを宣言する',async()=>{const index=JSON.parse(await readFile(path.join(root,'app/data/index.generated.json'),'utf8'));assert.equal(index.sourcePolicy,'fixed-release-only');assert.equal(index.subjects.length,97);});

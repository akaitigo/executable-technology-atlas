import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import path from 'node:path';
import test from 'node:test';
import { route } from '../scripts/lib/router.mjs';

const index=JSON.parse(await readFile(path.join(process.cwd(),'app/data/index.generated.json'),'utf8'));
test('planned Subjectをunclassifiedの未完了として返す',()=>{const result=route(index,{subjectId:'programming-language-foundations'});assert.equal(result.decision,'catalog-only');assert.equal(result.candidates[0].release,null);assert.equal(result.candidates[0].completion.classification,'unclassified');});
test('ReleaseをDigestへ固定する',()=>{const result=route(index,{subjectId:'zero-trust'});assert.equal(result.decision,'route');assert.match(result.candidates[0].release.digest,/^sha256:[a-f0-9]{64}$/);});
test('Routerはroute可能性とDefinitive完成を分離する',()=>{const result=route(index,{subjectId:'zero-trust'});assert.equal(result.decision,'route');assert.equal(result.candidates[0].release.completion.definitive,false);});
test('Coverage外をGapとして返す',()=>assert.equal(route(index,{query:'架空量子製品XYZ'}).decision,'coverage-gap'));
test('Read Modelの変更権限を捏造しない',()=>assert.equal(route(index,{query:'Atlasを修正して公開'}).decision,'permission-required'));
test('第三者環境への侵入をRouteしない',()=>assert.equal(route(index,{query:'第三者環境へ侵入してbypass'}).decision,'refuse-unsafe'));
test('Graph欠落をCore Gate未実行のままRouteし自動昇格しない',()=>{const result=route(index,{subjectId:'zero-trust'});assert.equal(result.candidates[0].evidenceDependency.status,'missing-required-output');assert.equal(result.candidates[0].evidenceDependency.coreGate.result,'not-run');assert.equal(result.candidates[0].evidenceDependency.autoPromotion,false);});

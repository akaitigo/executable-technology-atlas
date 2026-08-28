#!/usr/bin/env node
import { mkdir, readFile, writeFile } from 'node:fs/promises';
import path from 'node:path';
import { route } from './lib/router.mjs';

const root = process.cwd();
const index = JSON.parse(await readFile(path.join(root, 'app/data/index.generated.json'), 'utf8'));
const fixture = JSON.parse(await readFile(path.join(root, 'evals/router.eval.json'), 'utf8'));
const results = fixture.cases.map((testCase) => {
  const actual = route(index, testCase.request);
  const assertions = [
    !testCase.expect.decision || actual.decision === testCase.expect.decision,
    !testCase.expect.subjectId || actual.candidates.some((item) => item.id === testCase.expect.subjectId),
    !testCase.expect.releaseStatus || actual.candidates.some((item) => item.release?.status === testCase.expect.releaseStatus),
    !testCase.expect.noRelease || actual.candidates.every((item) => !item.release),
    !testCase.expect.digest || actual.candidates.some((item) => item.release?.digest?.startsWith('sha256:')),
    testCase.expect.completionDefinitive === undefined || actual.candidates.some((item) => item.release?.completion?.definitive === testCase.expect.completionDefinitive),
    !testCase.expect.completionClass || actual.candidates.some((item) => item.completion?.classification === testCase.expect.completionClass),
    !testCase.expect.depthAxes || actual.candidates.some((item) => item.depthReference?.summary?.axes === testCase.expect.depthAxes),
    !testCase.expect.depthSatisfied || actual.candidates.some((item) => item.depthReference?.summary?.satisfied === testCase.expect.depthSatisfied),
    !testCase.expect.depthPartial || actual.candidates.some((item) => item.depthReference?.summary?.partial === testCase.expect.depthPartial),
    !testCase.expect.depthStatus || actual.candidates.some((item) => item.depthReference?.status === testCase.expect.depthStatus),
    testCase.expect.depthBounded === undefined || actual.candidates.some((item) => item.depthReference?.completion?.bounded === testCase.expect.depthBounded),
    testCase.expect.depthDefinitive === undefined || actual.candidates.some((item) => item.depthReference?.completion?.definitive === testCase.expect.depthDefinitive),
  ];
  return { id:testCase.id, pass:assertions.every(Boolean), actual:{ decision:actual.decision, subjects:actual.candidates.map((item) => item.id) } };
});
const passed = results.filter((item) => item.pass).length;
const report = { schemaVersion:1, suite:fixture.id, cases:results.length, passed, passRate:passed/results.length, minimumPassRate:fixture.minimumPassRate, safetyCriticalPass:results.filter((item) => fixture.safetyCritical.includes(item.id)).every((item) => item.pass), results, verdict:passed/results.length >= fixture.minimumPassRate && results.filter((item) => fixture.safetyCritical.includes(item.id)).every((item) => item.pass) ? 'pass' : 'fail' };
await mkdir(path.join(root, 'evidence/reports'), { recursive:true });
await writeFile(path.join(root, 'evidence/reports/router-eval.json'), `${JSON.stringify(report,null,2)}\n`);
const categories={
  'japanese-discovery':'routing','api-distinction':'near-neighbor','operator-failure-container':'execution','planned-gap':'coverage-gap','infeasible-visible':'lifecycle','expired-visible':'lifecycle','superseded-history':'lifecycle','unsigned-gap':'authority','coverage-gap':'coverage-gap','evidence-digest':'authority','read-model-boundary':'authorization','security-boundary':'security','nearby-comparison':'near-neighbor','skill-route':'routing','fe-depth-incomplete':'coverage-gap','fe-tests-not-completion':'authority'
};
const coreEval={schema_version:1,id:'portal.router.eval',atlas_id:'executable-technology-atlas',atlas_release:'v1.0.0',skill_id:'technology-atlas-router',generated_at:'2026-08-28T00:00:00Z',cases:results.map((item)=>({id:`case.${item.id}`,category:categories[item.id],result:item.pass?'pass':'fail',assertion:`${item.id}が期待するSubject、状態、権限境界へRouteすること。`,evidence_ids:['portal.router.eval']}))};
await mkdir(path.join(root,'evals'),{recursive:true});await writeFile(path.join(root,'evals/router.skill-eval.json'),`${JSON.stringify(coreEval,null,2)}\n`);
console.log(`Router Eval: ${passed}/${results.length} (${Math.round(report.passRate*100)}%) ${report.verdict}`);
if (report.verdict !== 'pass') process.exitCode = 1;

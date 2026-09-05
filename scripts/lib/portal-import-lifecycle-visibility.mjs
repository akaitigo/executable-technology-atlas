import Ajv2020 from 'ajv/dist/2020.js';
import addFormats from 'ajv-formats';
import { readFile } from 'node:fs/promises';
import path from 'node:path';
import { canonicalJson, sha256 } from './crypto.mjs';

const INPUTS={
  index:'app/data/index.generated.json',
  importReport:'evidence/import-report.json',
  failureFixture:'fixtures/failure-scenarios.json',
  registryNegativeFixture:'fixtures/registry/invalid-registry-cases.json'
};

const lifecycleState=(subject)=>subject.release?.verification??'absent';
const count=(items,predicate)=>items.filter(predicate).length;

export async function loadPortalImportLifecycleInputs(root=process.cwd()){
  const entries=await Promise.all(Object.entries(INPUTS).map(async([key,relativePath])=>{const bytes=await readFile(path.join(root,relativePath));return[key,{path:relativePath,bytes,document:JSON.parse(bytes)}];}));
  const schema=JSON.parse(await readFile(path.join(root,'contracts/schemas/portal-import-lifecycle-visibility.schema.json'),'utf8'));
  return{...Object.fromEntries(entries),schema};
}

export function buildPortalImportLifecycleVisibility(inputs){
  const index=inputs.index.document;const report=inputs.importReport.document;const failureFixture=inputs.failureFixture.document;const registryFixture=inputs.registryNegativeFixture.document;
  const subjects=index.subjects.map((subject)=>({
    subjectId:subject.id,
    catalogStatus:subject.status,
    currentImportState:lifecycleState(subject),
    currentReleaseStatus:subject.release?.status??null,
    currentTrustUsage:subject.release?.trust?.usage??'none',
    historicalReleaseStatuses:[...new Set(subject.releaseHistory.map((release)=>release.status))],
    incompleteVisible:subject.release?.status==='incomplete',
    expiredVisible:subject.releaseHistory.some((release)=>release.status==='expired'),
    supersededVisible:subject.releaseHistory.some((release)=>release.status==='superseded'),
    archivedVisible:subject.releaseHistory.some((release)=>release.status==='archived')
  }));
  const fixtureScenarios=failureFixture.scenarios.map(({id,expected,state=null,status=null,verdict=null})=>({id,expected,state,status,verdict}));
  const registryNegativeCases=registryFixture.cases.map(({id,expectedDiagnostic,expectedResult})=>({id,expectedDiagnostic,expectedResult}));
  const actual={
    subjects:subjects.length,
    verified:count(subjects,(item)=>item.currentImportState==='verified'),
    quarantined:count(subjects,(item)=>item.currentImportState==='quarantined'),
    absent:count(subjects,(item)=>item.currentImportState==='absent'),
    incompleteCurrentReleases:count(subjects,(item)=>item.incompleteVisible),
    publicTrustedCurrentReleases:count(subjects,(item)=>item.currentTrustUsage==='public'),
    expiredHistoricalReleases:count(subjects,(item)=>item.expiredVisible),
    supersededHistoricalReleases:count(subjects,(item)=>item.supersededVisible),
    archivedHistoricalReleases:count(subjects,(item)=>item.archivedVisible),
    staleHumanReviewHolds:index.authorityReviewSummary.staleHolds,
    definitiveV2Imports:report.definitiveV2Imports.length
  };
  const coverage={
    failureScenarios:fixtureScenarios.length,
    quarantineScenarios:count(fixtureScenarios,(item)=>item.expected==='quarantined'),
    incompleteScenarios:count(fixtureScenarios,(item)=>item.expected==='incomplete'),
    excludedScenarios:count(fixtureScenarios,(item)=>item.state==='excluded'),
    infeasibleScenarios:count(fixtureScenarios,(item)=>item.state==='infeasible'),
    expiredScenarios:count(fixtureScenarios,(item)=>item.state==='expired'),
    supersededScenarios:count(fixtureScenarios,(item)=>item.status==='superseded'),
    archivedScenarios:count(fixtureScenarios,(item)=>item.status==='archived'),
    registryNegativeCases:registryNegativeCases.length,
    staleLockCases:count(registryNegativeCases,(item)=>item.id==='stale-lock'),
    revokedLockCases:count(registryNegativeCases,(item)=>item.id==='revoked-lock')
  };
  return{
    schemaVersion:1,id:'portal-import-lifecycle-visibility',status:'incomplete',
    source:Object.fromEntries(Object.entries(INPUTS).map(([key,relativePath])=>[key,{path:relativePath,digest:sha256(inputs[key].bytes)}])),
    registry:{preflightResult:report.registry.result,lifecyclePolicy:report.registry.lifecyclePolicy,lastKnownGoodPolicy:'preserve-on-preflight-failure'},
    actual,subjects,
    fixtureCoverage:{fixtureOnly:true,...coverage,scenarios:fixtureScenarios,registryCases:registryNegativeCases},
    boundary:{readOnly:true,fixtureIsActual:false,negativeCoverageIsProgress:false,staleLockAccepted:false,revokedLockAccepted:false,hideIncomplete:false,hideExpired:false,autoPromotion:false,distributionStatus:'not-established',completionEffect:'none'}
  };
}

export async function evaluatePortalImportLifecycleVisibility(root=process.cwd()){
  const inputs=await loadPortalImportLifecycleInputs(root);
  const report=buildPortalImportLifecycleVisibility(inputs);
  const result=await validatePortalImportLifecycleVisibility(root,report,inputs.schema);
  return{ok:result.ok,errors:result.errors,report,schema:inputs.schema};
}

export async function validatePortalImportLifecycleVisibility(root,document,schema){
  const errors=[];const ajv=new Ajv2020({allErrors:true,strict:true});addFormats(ajv);const validate=ajv.compile(schema);if(!validate(document))errors.push('schema-invalid');
  const inputs=await loadPortalImportLifecycleInputs(root);const expected=buildPortalImportLifecycleVisibility(inputs);
  if(canonicalJson(document.subjects?.map((item)=>item.subjectId))!==canonicalJson(expected.subjects.map((item)=>item.subjectId)))errors.push('subject-lifecycle-denominator-reduced-or-reordered');
  if(canonicalJson(document.actual)!==canonicalJson(expected.actual))errors.push('actual-lifecycle-counts-do-not-match-import');
  if(canonicalJson(document.fixtureCoverage?.scenarios)!==canonicalJson(expected.fixtureCoverage.scenarios)||canonicalJson(document.fixtureCoverage?.registryCases)!==canonicalJson(expected.fixtureCoverage.registryCases))errors.push('negative-lifecycle-coverage-hidden-or-reclassified');
  if(document.registry?.lifecyclePolicy!==expected.registry.lifecyclePolicy||document.registry?.lastKnownGoodPolicy!=='preserve-on-preflight-failure'||document.boundary?.staleLockAccepted!==false||document.boundary?.revokedLockAccepted!==false)errors.push('stale-or-revoked-lock-policy-weakened');
  if(document.boundary?.fixtureIsActual!==false||document.boundary?.negativeCoverageIsProgress!==false)errors.push('fixture-lifecycle-counted-as-actual');
  if(document.status!=='incomplete'||document.boundary?.hideIncomplete!==false||document.boundary?.hideExpired!==false||document.boundary?.autoPromotion!==false||document.boundary?.distributionStatus!=='not-established'||document.boundary?.completionEffect!=='none')errors.push('lifecycle-completion-boundary-weakened');
  if(canonicalJson(document)!==canonicalJson(expected))errors.push('lifecycle-source-drift');
  return{ok:errors.length===0,errors:[...new Set(errors)],summary:{...document.actual,fixtureCoverage:document.fixtureCoverage?{failureScenarios:document.fixtureCoverage.failureScenarios,registryNegativeCases:document.fixtureCoverage.registryNegativeCases}:null},digest:sha256(Buffer.from(`${JSON.stringify(document,null,2)}\n`))};
}

export function applyPortalImportLifecycleNegative(document,testCase){
  const mutated=structuredClone(document);
  if(testCase.mutation==='count-fixture-expired-as-actual'){mutated.actual.expiredHistoricalReleases=1;mutated.boundary.fixtureIsActual=true;}
  else if(testCase.mutation==='hide-absent'){mutated.actual.absent=0;}
  else if(testCase.mutation==='hide-incomplete'){mutated.actual.incompleteCurrentReleases=0;mutated.boundary.hideIncomplete=true;}
  else if(testCase.mutation==='drop-quarantine-scenario'){mutated.fixtureCoverage.scenarios=mutated.fixtureCoverage.scenarios.filter((item)=>item.expected!=='quarantined');}
  else if(testCase.mutation==='accept-stale-lock'){mutated.registry.lifecyclePolicy='current-or-legacy-current-plus-stale';mutated.boundary.staleLockAccepted=true;}
  else if(testCase.mutation==='accept-revoked-lock'){mutated.boundary.revokedLockAccepted=true;}
  else if(testCase.mutation==='promote-from-negative-coverage'){mutated.status='complete';mutated.boundary.negativeCoverageIsProgress=true;mutated.boundary.distributionStatus='established';mutated.boundary.completionEffect='complete';}
  else throw new Error(`未知のLifecycle可視性負例です: ${testCase.mutation}`);
  return mutated;
}

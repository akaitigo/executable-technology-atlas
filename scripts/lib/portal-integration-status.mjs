import Ajv2020 from 'ajv/dist/2020.js';
import addFormats from 'ajv-formats';
import { readFile } from 'node:fs/promises';
import path from 'node:path';
import { canonicalJson, sha256 } from './crypto.mjs';
import { validatePortalRootArtifactGapIndex } from './portal-root-artifact-gap-index.mjs';
import { validatePortalRootVerificationMatrixReadiness } from './portal-root-verification-matrix-readiness.mjs';
import { validatePortalDistributionReadiness } from './portal-distribution-readiness.mjs';
import { validatePortalDistributionGapIndex } from './portal-distribution-gap-index.mjs';
import { evaluatePortalEvidenceRefreshReadiness, loadPortalEvidenceRefreshPolicy } from './portal-evidence-refresh-readiness.mjs';

const INPUTS={
  rootArtifacts:{path:'evidence/portal-root-artifact-gap-index.json',schemaPath:'contracts/schemas/portal-root-artifact-gap-index.schema.json'},
  rootMatrix:{path:'evidence/portal-root-verification-matrix-readiness.json',schemaPath:'contracts/schemas/portal-root-verification-matrix-readiness.schema.json'},
  distribution:{path:'evidence/portal-distribution-readiness.json',schemaPath:'contracts/schemas/portal-distribution-readiness.schema.json'},
  distributionGaps:{path:'evidence/portal-distribution-gap-index.json',schemaPath:'contracts/schemas/portal-distribution-gap-index.schema.json'}
};

export async function loadPortalIntegrationStatusInputs(root=process.cwd()){
  const entries=await Promise.all(Object.entries(INPUTS).map(async([id,input])=>{const[bytes,schemaBytes]=await Promise.all([readFile(path.join(root,input.path)),readFile(path.join(root,input.schemaPath))]);return[id,{...input,bytes,document:JSON.parse(bytes),schema:JSON.parse(schemaBytes)}];}));
  const [{policy,schema:refreshSchema,policyBytes},integrationSchemaBytes]=await Promise.all([loadPortalEvidenceRefreshPolicy(root),readFile(path.join(root,'contracts/schemas/portal-integration-status.schema.json'))]);
  return{...Object.fromEntries(entries),refresh:{path:'contracts/portal-evidence-refresh-policy.json',bytes:policyBytes,policy,schema:refreshSchema},schema:JSON.parse(integrationSchemaBytes)};
}

export async function buildPortalIntegrationStatus(root,inputs){
  const validations={
    rootArtifacts:await validatePortalRootArtifactGapIndex(root,inputs.rootArtifacts.document,inputs.rootArtifacts.schema),
    rootMatrix:await validatePortalRootVerificationMatrixReadiness(root,inputs.rootMatrix.document,inputs.rootMatrix.schema),
    distribution:await validatePortalDistributionReadiness(root,inputs.distribution.document,inputs.distribution.schema),
    distributionGaps:await validatePortalDistributionGapIndex(root,inputs.distributionGaps.document,inputs.distributionGaps.schema)
  };
  const refresh=await evaluatePortalEvidenceRefreshReadiness(root,inputs.refresh.policy,inputs.refresh.schema);validations.refresh=refresh;
  const rootArtifacts=inputs.rootArtifacts.document;const matrix=inputs.rootMatrix.document;const distribution=inputs.distribution.document;const gaps=inputs.distributionGaps.document;const refreshReport=refresh.report;
  const sources=Object.fromEntries([...Object.entries(INPUTS).map(([id,input])=>[id,{path:input.path,digest:sha256(inputs[id].bytes),valid:validations[id].ok}]),['refresh',{path:inputs.refresh.path,digest:sha256(inputs.refresh.bytes),valid:refresh.ok}]]);
  return{schemaVersion:1,id:'portal-integration-status',status:'blocked',classification:'dynamic-read-only-integration-observation',sources,root:{definitiveStatus:rootArtifacts.boundary.rootDefinitiveStatus,artifactsRequired:rootArtifacts.summary.requiredArtifacts,artifactsMissing:rootArtifacts.summary.missingArtifacts,artifactsPresent:rootArtifacts.summary.presentArtifacts,matrixPrerequisites:matrix.summary.prerequisites,matrixSatisfied:matrix.summary.satisfied,matrixBlocked:matrix.summary.blocked,matrixCells:matrix.observed.portalDistributionMatrix.cells,matrixVerified:matrix.observed.portalDistributionMatrix.verified,matrixGap:matrix.observed.portalDistributionMatrix.gap,matrixNotEvaluated:matrix.observed.portalDistributionMatrix.notEvaluated,coreMatrixArtifactStatus:matrix.boundary.coreSubjectArtifact.status},distribution:{status:distribution.status,subjects:distribution.summary.subjects,ready:distribution.summary.distributionReady,subjectDefinitive:distribution.subjects.filter((item)=>item.definitive.status==='subject-definitive').length,openGapInstances:gaps.summary.openInstances,closedGapInstances:gaps.summary.closedInstances,publicTrustedRelease:distribution.summary.publicTrustedRelease,definitiveV2InputAvailable:distribution.summary.definitiveV2InputAvailable,definitiveCertificatePresent:distribution.summary.definitiveCertificatePresent},evidenceRefresh:{status:refreshReport.status,staleWrappers:refreshReport.summary.staleWrappers,inputsChangedSinceRun:refreshReport.summary.inputsChangedSinceRun,missingOutputs:refreshReport.summary.missingDiscoveredOutputs,currentRerun:refreshReport.summary.currentRerun},boundary:{readOnly:true,autoRun:false,autoPromotion:false,portalIsSubject:false,rawCountsAreCompletion:false,coreArtifactsAutoCreated:false,boundedCertificateEffect:'none',subjectDefinitiveEffect:'none',distributionEffect:'none',rootDefinitiveEffect:'none',completionEffect:'none'}};
}

export async function evaluatePortalIntegrationStatus(root=process.cwd()){
  const inputs=await loadPortalIntegrationStatusInputs(root);const report=await buildPortalIntegrationStatus(root,inputs);const errors=[];const ajv=new Ajv2020({allErrors:true,strict:true});addFormats(ajv);const validate=ajv.compile(inputs.schema);if(!validate(report))errors.push('schema-invalid');if(Object.values(report.sources).some((item)=>item.valid!==true))errors.push('integration-source-invalid');return{ok:errors.length===0,errors,report,schema:inputs.schema};
}

export function validatePortalIntegrationStatus(document,schema,expected){
  const errors=[];const ajv=new Ajv2020({allErrors:true,strict:true});addFormats(ajv);const validate=ajv.compile(schema);if(!validate(document))errors.push('schema-invalid');
  if(document.root?.artifactsRequired!==6||document.root?.artifactsMissing!==5||document.root?.artifactsPresent!==1)errors.push('integration-root-gap-hidden');
  if(document.root?.matrixPrerequisites!==8||document.root?.matrixSatisfied!==3||document.root?.matrixBlocked!==5||document.root?.matrixCells!==970||document.root?.matrixGap!==478||document.root?.matrixNotEvaluated!==291||document.root?.coreMatrixArtifactStatus!=='present')errors.push('integration-matrix-gap-hidden');
  if(document.distribution?.subjects!==97)errors.push('integration-subject-denominator-reduced');
  if(document.distribution?.status!=='not-established'||document.distribution?.ready!==0||document.distribution?.subjectDefinitive!==0)errors.push('integration-distribution-promoted');
  if(document.distribution?.openGapInstances!==589||document.distribution?.closedGapInstances!==0)errors.push('integration-gap-instances-hidden');
  if(!['blocked','ready'].includes(document.evidenceRefresh?.status)||!Number.isInteger(document.evidenceRefresh?.staleWrappers)||document.evidenceRefresh?.staleWrappers<0||document.evidenceRefresh?.staleWrappers>8||!Number.isInteger(document.evidenceRefresh?.inputsChangedSinceRun)||document.evidenceRefresh?.inputsChangedSinceRun<0||document.evidenceRefresh?.inputsChangedSinceRun>4||!Number.isInteger(document.evidenceRefresh?.missingOutputs)||document.evidenceRefresh?.missingOutputs<0||(document.evidenceRefresh?.currentRerun!==true&&document.evidenceRefresh?.currentRerun!==false)||(document.evidenceRefresh?.status==='ready'&&(document.evidenceRefresh?.currentRerun!==true||document.evidenceRefresh?.staleWrappers!==0||document.evidenceRefresh?.inputsChangedSinceRun!==0||document.evidenceRefresh?.missingOutputs!==0))||(document.evidenceRefresh?.status==='blocked'&&document.evidenceRefresh?.currentRerun!==false))errors.push('integration-refresh-promoted');
  if(expected&&JSON.stringify(document.evidenceRefresh)!==JSON.stringify(expected.evidenceRefresh))errors.push('integration-source-drift');
  if(document.boundary?.portalIsSubject!==false||document.boundary?.coreArtifactsAutoCreated!==false)errors.push('integration-portal-subjectized');
  if(document.boundary?.readOnly!==true||document.boundary?.autoRun!==false||document.boundary?.autoPromotion!==false)errors.push('integration-write-boundary-weakened');
  if(document.status!=='blocked'||document.boundary?.rawCountsAreCompletion!==false||document.boundary?.boundedCertificateEffect!=='none'||document.boundary?.subjectDefinitiveEffect!=='none'||document.boundary?.distributionEffect!=='none'||document.boundary?.rootDefinitiveEffect!=='none'||document.boundary?.completionEffect!=='none')errors.push('integration-completion-promoted');
  if(expected&&canonicalJson(document)!==canonicalJson(expected))errors.push('integration-source-drift');return{ok:errors.length===0,errors:[...new Set(errors)]};
}

export function applyPortalIntegrationStatusNegative(document,testCase){const mutated=structuredClone(document);if(testCase.mutation==='hide-root-artifact-gap'){mutated.root.artifactsMissing=0;mutated.root.artifactsPresent=6;}else if(testCase.mutation==='hide-runtime-matrix-gap'){mutated.root.matrixGap=0;mutated.root.matrixNotEvaluated=0;mutated.root.coreMatrixArtifactStatus='present';}else if(testCase.mutation==='reduce-subject-denominator')mutated.distribution.subjects=96;else if(testCase.mutation==='promote-distribution'){mutated.distribution.status='established';mutated.distribution.ready=97;mutated.distribution.subjectDefinitive=97;}else if(testCase.mutation==='close-gap-counts'){mutated.distribution.openGapInstances=0;mutated.distribution.closedGapInstances=589;}else if(testCase.mutation==='promote-refresh'){mutated.evidenceRefresh.status='ready';mutated.evidenceRefresh.staleWrappers=0;mutated.evidenceRefresh.inputsChangedSinceRun=0;mutated.evidenceRefresh.missingOutputs=0;mutated.evidenceRefresh.currentRerun=false;}else if(testCase.mutation==='subjectize-portal'){mutated.boundary.portalIsSubject=true;mutated.boundary.coreArtifactsAutoCreated=true;}else if(testCase.mutation==='allow-auto-run'){mutated.boundary.autoRun=true;mutated.boundary.autoPromotion=true;}else if(testCase.mutation==='promote-completion'){mutated.status='ready';mutated.boundary.rawCountsAreCompletion=true;mutated.boundary.completionEffect='complete';}else throw new Error(`未知のPortal integration status負例です: ${testCase.mutation}`);return mutated;}

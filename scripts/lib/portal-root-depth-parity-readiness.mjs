import Ajv2020 from 'ajv/dist/2020.js';
import addFormats from 'ajv-formats';
import { readFile } from 'node:fs/promises';
import path from 'node:path';
import { canonicalJson, sha256 } from './crypto.mjs';

const INPUT_PATHS={
  rootGapIndex:'evidence/portal-root-artifact-gap-index.json',
  portalSurfaceInventory:'contracts/portal-root-surface-inventory.json',
  distributionMatrix:'evidence/portal-distribution-verification-matrix.json',
  dependencyGraph:'evidence/dependency-graph.json'
};
const REQUIRED_GRAPH_OUTPUTS=[
  'evidence/portal-distribution-gap-index.json',
  'evidence/portal-distribution-input-bindings.json',
  'evidence/portal-distribution-readiness.json',
  'evidence/portal-distribution-verification-matrix.json',
  'evidence/portal-import-lifecycle-visibility.json',
  'evidence/portal-root-artifact-gap-index.json'
];

export async function loadPortalRootDepthParityInputs(root=process.cwd()){
  const entries=await Promise.all(Object.entries(INPUT_PATHS).map(async([key,relativePath])=>{const bytes=await readFile(path.join(root,relativePath));return[key,{path:relativePath,bytes,document:JSON.parse(bytes)}];}));
  const schema=JSON.parse(await readFile(path.join(root,'contracts/schemas/portal-root-depth-parity-readiness.schema.json'),'utf8'));
  return{...Object.fromEntries(entries),schema};
}

export function buildPortalRootDepthParityReadiness(inputs){
  const depthGap=inputs.rootGapIndex.document.gaps.find((item)=>item.artifactPath==='depth.parity.yaml');
  if(!depthGap)throw new Error('depth.parity.yamlのroot Gapがありません');
  const surface=inputs.portalSurfaceInventory.document;const matrix=inputs.distributionMatrix.document;const graph=inputs.dependencyGraph.document;
  const graphOutputs=new Set(graph.required_outputs??[]);const missingGraphOutputs=REQUIRED_GRAPH_OUTPUTS.filter((item)=>!graphOutputs.has(item));
  const matrixArtifactReady=matrix.boundary.coreSubjectArtifact.status==='present';
  const prerequisites=[
    {id:'portal-subject-authority-declaration',state:'blocked',evidence:['evidence/portal-root-artifact-gap-index.json'],gapIds:['portal-is-not-a-core-subject']},
    {id:'core-subject-surface-inventory',state:'blocked',evidence:['contracts/portal-root-surface-inventory.json'],gapIds:['surface.inventory.yaml-missing']},
    {id:'core-subject-verification-matrix',state:matrixArtifactReady?'satisfied':'blocked',evidence:['verification.matrix.yaml'],gapIds:matrixArtifactReady?[]:['verification.matrix.yaml-missing']},
    {id:'authority-derived-depth-denominator',state:'blocked',evidence:['contracts/portal-root-surface-inventory.json'],gapIds:['authority-derived-depth-denominator-not-established']},
    {id:'actual-runtime-depth-proof',state:'blocked',evidence:['evidence/portal-distribution-verification-matrix.json'],gapIds:['subject-runtime-proof-not-evaluated']},
    {id:'current-evidence-dependency-rerun',state:'blocked',evidence:['evidence/dependency-graph.json'],gapIds:['current-portal-derived-outputs-not-bound']}
  ];
  return{
    schemaVersion:1,id:'portal-root-depth-parity-readiness',status:'blocked',classification:'portal-infrastructure-readiness-only',
    source:Object.fromEntries(Object.entries(INPUT_PATHS).map(([key,relativePath])=>[key,{path:relativePath,digest:sha256(inputs[key].bytes)}])),
    coreContract:{commit:depthGap.coreContract.commit,artifactPath:depthGap.artifactPath,schemaPath:depthGap.coreContract.schemaPath,schemaDigest:depthGap.coreContract.schemaDigest,validatorPath:depthGap.coreContract.validatorPath,validatorDigest:depthGap.coreContract.validatorDigest,observedStatus:depthGap.status},
    observed:{
      portalIsSubject:inputs.rootGapIndex.document.boundary.portalIsSubject,
      portalSurfaceInventory:{classification:surface.classification,masterySurfaces:surface.denominator.masterySurfaces,coverageTargets:surface.denominator.coverageTargets,coreSubjectArtifactStatus:surface.boundary.coreSubjectArtifactStatus},
      distributionMatrix:{status:matrix.status,cells:matrix.summary.cells,gap:matrix.summary.gap,notEvaluated:matrix.summary.notEvaluated,coreSubjectArtifactStatus:matrix.boundary.coreSubjectArtifact.status,runtimeSubstitution:matrix.boundary.runtimeSubstitution},
      dependencyGraph:{recordedStatus:graph.status,requiredOutputDenominator:REQUIRED_GRAPH_OUTPUTS.length,boundRequiredOutputs:REQUIRED_GRAPH_OUTPUTS.length-missingGraphOutputs.length,missingRequiredOutputs:missingGraphOutputs}
    },
    summary:{prerequisites:prerequisites.length,satisfied:prerequisites.filter((item)=>item.state==='satisfied').length,blocked:prerequisites.filter((item)=>item.state==='blocked').length,coreDepthParityArtifactsPresent:0,completionEffect:'none'},
    prerequisites,
    boundary:{readOnly:true,autoCreate:false,autoPromotion:false,portalSurfaceInventoryIsCoreSubjectArtifact:false,distributionMatrixIsCoreSubjectMatrix:false,recordedGraphStatusIsCurrentProof:false,runtimeSubstitution:false,digestOnlyClosure:false,coreSubjectArtifact:{path:'depth.parity.yaml',status:'missing',effect:'none'},rootDefinitiveStatus:'root-definitive-incomplete',distributionStatus:'not-established',completionEffect:'none'}
  };
}

export async function validatePortalRootDepthParityReadiness(root,document,schema){
  const errors=[];const ajv=new Ajv2020({allErrors:true,strict:true});addFormats(ajv);const validate=ajv.compile(schema);if(!validate(document))errors.push('schema-invalid');
  const expected=buildPortalRootDepthParityReadiness(await loadPortalRootDepthParityInputs(root));
  const missingRequiredOutputs=document.observed?.dependencyGraph?.missingRequiredOutputs;
  if(canonicalJson(document.prerequisites?.map((item)=>item.id))!==canonicalJson(expected.prerequisites.map((item)=>item.id)))errors.push('depth-prerequisite-denominator-reduced-or-reordered');
  if(document.coreContract?.artifactPath!=='depth.parity.yaml'||document.coreContract?.observedStatus!=='missing'||document.boundary?.coreSubjectArtifact?.status!=='missing')errors.push('core-depth-parity-artifact-spoofed');
  if(document.boundary?.portalSurfaceInventoryIsCoreSubjectArtifact!==false)errors.push('portal-surface-inventory-substituted-for-core-artifact');
  if(document.boundary?.distributionMatrixIsCoreSubjectMatrix!==false)errors.push('distribution-matrix-substituted-for-core-matrix');
  if(document.boundary?.recordedGraphStatusIsCurrentProof!==false||document.observed?.dependencyGraph?.requiredOutputDenominator!==REQUIRED_GRAPH_OUTPUTS.length||!Number.isInteger(document.observed?.dependencyGraph?.boundRequiredOutputs)||document.observed.dependencyGraph.boundRequiredOutputs<0||document.observed.dependencyGraph.boundRequiredOutputs>REQUIRED_GRAPH_OUTPUTS.length||!Array.isArray(missingRequiredOutputs)||missingRequiredOutputs.length!==REQUIRED_GRAPH_OUTPUTS.length-document.observed.dependencyGraph.boundRequiredOutputs||new Set(missingRequiredOutputs).size!==missingRequiredOutputs.length||missingRequiredOutputs.some((item)=>!REQUIRED_GRAPH_OUTPUTS.includes(item)))errors.push('recorded-graph-status-promoted');
  if(document.status!=='blocked'||document.summary?.prerequisites!==expected.summary.prerequisites||document.summary?.satisfied!==expected.summary.satisfied||document.summary?.blocked!==expected.summary.blocked||document.summary?.coreDepthParityArtifactsPresent!==0||document.boundary?.autoCreate!==false||document.boundary?.autoPromotion!==false||document.boundary?.runtimeSubstitution!==false||document.boundary?.digestOnlyClosure!==false||document.boundary?.rootDefinitiveStatus!=='root-definitive-incomplete'||document.boundary?.distributionStatus!=='not-established'||document.boundary?.completionEffect!=='none')errors.push('depth-parity-readiness-promoted');
  expected.source.dependencyGraph=structuredClone(document.source?.dependencyGraph??expected.source.dependencyGraph);
  expected.observed.dependencyGraph=structuredClone(document.observed?.dependencyGraph??expected.observed.dependencyGraph);
  if(canonicalJson(document)!==canonicalJson(expected))errors.push('depth-parity-readiness-source-drift');
  return{ok:errors.length===0,errors:[...new Set(errors)],summary:document.summary??{},digest:sha256(Buffer.from(`${JSON.stringify(document,null,2)}\n`))};
}

export function applyPortalRootDepthParityNegative(document,testCase){
  const mutated=structuredClone(document);
  if(testCase.mutation==='remove-prerequisite')mutated.prerequisites.shift();
  else if(testCase.mutation==='pretend-depth-artifact-present'){mutated.coreContract.observedStatus='present';mutated.boundary.coreSubjectArtifact.status='present';}
  else if(testCase.mutation==='substitute-portal-surface')mutated.boundary.portalSurfaceInventoryIsCoreSubjectArtifact=true;
  else if(testCase.mutation==='substitute-distribution-matrix')mutated.boundary.distributionMatrixIsCoreSubjectMatrix=true;
  else if(testCase.mutation==='promote-recorded-graph'){mutated.boundary.recordedGraphStatusIsCurrentProof=true;mutated.observed.dependencyGraph.missingRequiredOutputs=[];mutated.observed.dependencyGraph.boundRequiredOutputs=6;}
  else if(testCase.mutation==='promote-readiness'){mutated.status='ready';mutated.summary.satisfied=6;mutated.summary.blocked=0;mutated.summary.coreDepthParityArtifactsPresent=1;mutated.boundary.autoCreate=true;mutated.boundary.completionEffect='complete';}
  else throw new Error(`未知のDepth parity readiness負例です: ${testCase.mutation}`);
  return mutated;
}

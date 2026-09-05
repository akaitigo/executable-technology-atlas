import Ajv2020 from 'ajv/dist/2020.js';
import addFormats from 'ajv-formats';
import { readFile, stat } from 'node:fs/promises';
import path from 'node:path';
import { canonicalJson, sha256 } from './crypto.mjs';

export const ROOT_ARTIFACT_REQUIREMENTS=[
  {artifactPath:'definitive.yaml',schemaPath:'schemas/definitive.schema.json',validatorPath:'internal/validate/definitive.go'},
  {artifactPath:'surface.inventory.yaml',schemaPath:'schemas/surface-inventory.schema.json',validatorPath:'internal/validate/definitive.go'},
  {artifactPath:'verification.matrix.yaml',schemaPath:'schemas/verification-matrix.schema.json',validatorPath:'internal/validate/definitive.go'},
  {artifactPath:'depth.parity.yaml',schemaPath:'schemas/depth-parity.schema.json',validatorPath:'internal/validate/depth_parity.go'},
  {artifactPath:'migrations/definitive-v2.yaml',schemaPath:'schemas/definitive-migration.schema.json',validatorPath:'internal/project/project.go'},
  {artifactPath:'evidence/definitive-certificate.json',schemaPath:'schemas/definitive-certificate.schema.json',validatorPath:'internal/validate/definitive_certificate.go'}
];

async function exists(root,relative){try{return(await stat(path.join(root,relative))).isFile();}catch{return false;}}

export async function buildPortalRootArtifactGapIndex(root,coreDir,coreCommit){
  const gaps=[];
  for(const requirement of ROOT_ARTIFACT_REQUIREMENTS){const present=await exists(root,requirement.artifactPath);const schemaBytes=await readFile(path.join(coreDir,requirement.schemaPath));const validatorBytes=await readFile(path.join(coreDir,requirement.validatorPath));gaps.push({gapId:`portal-root-artifact-missing:${requirement.artifactPath.replaceAll('/','-').replaceAll('.','-')}`,artifactPath:requirement.artifactPath,status:present?'present':'missing',coreContract:{commit:coreCommit,schemaPath:requirement.schemaPath,schemaDigest:sha256(schemaBytes),validatorPath:requirement.validatorPath,validatorDigest:sha256(validatorBytes)},observed:{exists:present},rootDefinitiveEffect:'none',distributionEffect:'none',completionEffect:'none'});}
  const missing=gaps.filter((gap)=>gap.status==='missing').length;
  const present=gaps.length-missing;
  return{schemaVersion:1,id:'portal-root-core-v2-artifact-gap-index',atlasId:'executable-technology-atlas',scope:'portal-root-core-v2-required-artifacts',status:missing?'open':'closed',summary:{requiredArtifacts:gaps.length,missingArtifacts:missing,presentArtifacts:present,openGaps:missing,closedGaps:present},gaps,boundary:{portalIsSubject:false,readOnly:true,autoCreate:false,autoClose:false,digestOnlyClosure:false,rootDefinitiveStatus:'root-definitive-incomplete',distributionStatus:'not-established',completionEffect:'none'}};
}

export async function validatePortalRootArtifactGapIndex(root,document,schema,{coreDir=null,coreCommit=null}={}){
  const errors=[];const ajv=new Ajv2020({allErrors:true,strict:true});addFormats(ajv);const validate=ajv.compile(schema);if(!validate(document))errors.push('schema-invalid');const expectedPaths=ROOT_ARTIFACT_REQUIREMENTS.map((item)=>item.artifactPath);const actualPaths=(document.gaps??[]).map((item)=>item.artifactPath);if(canonicalJson(actualPaths)!==canonicalJson(expectedPaths))errors.push('root-artifact-gap-denominator-reduced-or-reordered');
  let missing=0;
  for(const requirement of ROOT_ARTIFACT_REQUIREMENTS){const gap=(document.gaps??[]).find((item)=>item.artifactPath===requirement.artifactPath);if(!gap)continue;const present=await exists(root,requirement.artifactPath);if(gap.coreContract?.schemaPath!==requirement.schemaPath||gap.coreContract?.validatorPath!==requirement.validatorPath)errors.push(`root-artifact-contract-rebound:${requirement.artifactPath}`);if(gap.status!==(present?'present':'missing')||gap.observed?.exists!==present)errors.push(`root-artifact-observed-drift:${requirement.artifactPath}`);if(gap.rootDefinitiveEffect!=='none'||gap.distributionEffect!=='none'||gap.completionEffect!=='none')errors.push(`root-artifact-gap-auto-closed:${requirement.artifactPath}`);if(!present)missing+=1;}
  const present=(document.gaps??[]).length-missing;
  if(document.summary?.requiredArtifacts!==6||document.summary?.missingArtifacts!==missing||document.summary?.presentArtifacts!==present||document.summary?.openGaps!==missing||document.summary?.closedGaps!==present)errors.push('root-artifact-gap-summary-drift');
  if(document.status!==(missing?'open':'closed'))errors.push('root-artifact-gap-status-drift');
  if(document.boundary?.portalIsSubject!==false||document.boundary?.readOnly!==true||document.boundary?.autoCreate!==false||document.boundary?.autoClose!==false||document.boundary?.digestOnlyClosure!==false||document.boundary?.rootDefinitiveStatus!=='root-definitive-incomplete'||document.boundary?.distributionStatus!=='not-established'||document.boundary?.completionEffect!=='none')errors.push('root-artifact-gap-boundary-weakened');
  if(coreDir&&coreCommit){const expected=await buildPortalRootArtifactGapIndex(root,coreDir,coreCommit);if(canonicalJson(document)!==canonicalJson(expected))errors.push('root-artifact-core-contract-drift');}
  return{ok:errors.length===0,errors:[...new Set(errors)],summary:document.summary??{},digest:sha256(Buffer.from(`${JSON.stringify(document,null,2)}\n`))};
}

export function applyPortalRootArtifactGapNegative(document,testCase){const mutated=structuredClone(document);const gap=mutated.gaps.find((item)=>item.artifactPath===testCase.artifactPath);if(testCase.mutation==='remove-gap')mutated.gaps=mutated.gaps.filter((item)=>item.artifactPath!==testCase.artifactPath);else if(testCase.mutation==='phantom-present'){gap.status='present';gap.observed.exists=true;}else if(testCase.mutation==='rebind-schema')gap.coreContract.schemaPath='schemas/atlas.schema.json';else if(testCase.mutation==='rebind-validator')gap.coreContract.validatorPath='internal/validate/validate.go';else if(testCase.mutation==='close-from-digest'){gap.status='present';gap.observed.exists=true;mutated.summary.missingArtifacts=Math.max(0,mutated.summary.missingArtifacts-1);mutated.summary.presentArtifacts+=1;mutated.summary.openGaps=Math.max(0,mutated.summary.openGaps-1);mutated.summary.closedGaps+=1;gap.completionEffect='complete';}else if(testCase.mutation==='rewrite-summary'){mutated.summary.missingArtifacts=0;mutated.summary.presentArtifacts=6;mutated.summary.openGaps=0;mutated.summary.closedGaps=6;}else if(testCase.mutation==='subjectize-portal'){mutated.boundary.portalIsSubject=true;mutated.boundary.autoCreate=true;}else throw new Error(`未知のPortal root artifact負例です: ${testCase.mutation}`);return mutated;}

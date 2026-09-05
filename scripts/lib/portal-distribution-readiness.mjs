import Ajv2020 from 'ajv/dist/2020.js';
import addFormats from 'ajv-formats';
import { readFile } from 'node:fs/promises';
import path from 'node:path';
import { canonicalJson, sha256 } from './crypto.mjs';

const INDEX_PATH='app/data/index.generated.json';
const publicTrust=(subject)=>subject.release?.trust?.usage==='public';
const certificatePresent=(subject)=>Boolean(subject.definitiveV2?.certificate);
const inventoryClosed=(subject)=>subject.definitiveV2?.inventoryClosure?.status==='closed';
const evidenceDependencyCurrent=(subject)=>subject.evidenceDependency?.status==='current'&&subject.evidenceDependency?.coreGate?.result==='pass';

function projectSubject(subject){
  const blockers=[];
  if(!subject.release)blockers.push('signed-fixed-release-missing');
  else{
    if(subject.release.verification!=='verified')blockers.push('fixed-release-verification-failed');
    if(!publicTrust(subject))blockers.push('public-trust-missing');
    if(subject.release.status!=='complete')blockers.push('release-manifest-incomplete');
  }
  if(subject.definitiveV2?.availability!=='available')blockers.push('definitive-v2-input-missing');
  if(!inventoryClosed(subject))blockers.push('authority-inventory-closure-not-established');
  if(subject.definitiveV2?.coreGate?.result!=='pass')blockers.push('definitive-core-gate-not-passed');
  if(!certificatePresent(subject))blockers.push('definitive-certificate-missing');
  if(!evidenceDependencyCurrent(subject))blockers.push('evidence-dependency-not-current');
  const eligible=blockers.length===0;
  return{
    subjectId:subject.id,atlasId:subject.atlasId??null,repository:subject.repository,catalogStatus:subject.status,
    release:{availability:subject.release?'present':'missing',version:subject.release?.version??null,manifestStatus:subject.release?.status??null,verification:subject.release?.verification??null,trustUsage:subject.release?.trust?.usage??'none'},
    definitive:{availability:subject.definitiveV2.availability,status:subject.definitiveV2.status,completionClass:subject.definitiveV2.completionClass,coreGateResult:subject.definitiveV2.coreGate.result,inventoryStatus:subject.definitiveV2.inventoryClosure.status,certificateStatus:certificatePresent(subject)?'present':'missing',gapIds:[...subject.definitiveV2.gapIds]},
    fixedCommitAudit:{availability:subject.fixedCommitAudit.availability,status:subject.fixedCommitAudit.status,gapIds:[...subject.fixedCommitAudit.gapIds]},
    distribution:{status:eligible?'ready':'blocked',eligible,blockerIds:blockers}
  };
}

export function buildPortalDistributionReadiness(index,indexBytes){
  const subjects=index.subjects.map(projectSubject);const count=(predicate)=>subjects.filter(predicate).length;
  const summary={subjects:subjects.length,distributionReady:count((item)=>item.distribution.eligible),releasePresent:count((item)=>item.release.availability==='present'),publicTrustedRelease:count((item)=>item.release.trustUsage==='public'),definitiveV2InputAvailable:count((item)=>item.definitive.availability==='available'),definitiveCoreGatePassed:count((item)=>item.definitive.coreGateResult==='pass'),definitiveCertificatePresent:count((item)=>item.definitive.certificateStatus==='present'),fixedCommitAuditAvailable:count((item)=>item.fixedCommitAudit.availability==='available'),blockerInstances:subjects.reduce((sum,item)=>sum+item.distribution.blockerIds.length,0)};
  return{schemaVersion:1,id:'portal-subject-distribution-readiness',atlasId:'executable-technology-atlas',scope:'97-subject-fixed-input-distribution-read-model',status:summary.distributionReady===subjects.length?'established':'not-established',source:{path:INDEX_PATH,indexDigest:index.digest,artifactDigest:sha256(indexBytes)},summary,subjects,boundary:{readOnly:true,autoPromotion:false,rawCountsAreCompletion:false,portalBoundedCertificateEffect:'none',subjectDefinitiveEffect:'none',distributionGapEffect:'none',completionEffect:'none'}};
}

export async function loadPortalDistributionInputs(root=process.cwd()){
  const indexBytes=await readFile(path.join(root,INDEX_PATH));const schema=JSON.parse(await readFile(path.join(root,'contracts/schemas/portal-distribution-readiness.schema.json'),'utf8'));
  return{indexBytes,index:JSON.parse(indexBytes),schema};
}

export async function validatePortalDistributionReadiness(root,document,schema){
  const errors=[];const ajv=new Ajv2020({allErrors:true,strict:true});addFormats(ajv);const validate=ajv.compile(schema);if(!validate(document))errors.push('schema-invalid');
  const{indexBytes,index}=await loadPortalDistributionInputs(root);const expected=buildPortalDistributionReadiness(index,indexBytes);const ids=(document.subjects??[]).map((item)=>item.subjectId);const expectedIds=index.subjects.map((item)=>item.id);
  if(new Set(ids).size!==ids.length||canonicalJson(ids)!==canonicalJson(expectedIds))errors.push('subject-denominator-reduced-or-reordered');
  for(const expectedSubject of expected.subjects){const actual=(document.subjects??[]).find((item)=>item.subjectId===expectedSubject.subjectId);if(!actual)continue;if(canonicalJson(actual.definitive?.gapIds)!==canonicalJson(expectedSubject.definitive.gapIds)||canonicalJson(actual.fixedCommitAudit?.gapIds)!==canonicalJson(expectedSubject.fixedCommitAudit.gapIds))errors.push(`gap-granularity-reduced:${expectedSubject.subjectId}`);if(actual.distribution?.eligible!==expectedSubject.distribution.eligible||actual.distribution?.status!==expectedSubject.distribution.status)errors.push(`distribution-promotion-forbidden:${expectedSubject.subjectId}`);}
  if(document.status!==expected.status||document.boundary?.readOnly!==true||document.boundary?.autoPromotion!==false||document.boundary?.rawCountsAreCompletion!==false||document.boundary?.completionEffect!=='none'||document.boundary?.subjectDefinitiveEffect!=='none'||document.boundary?.distributionGapEffect!=='none')errors.push('distribution-boundary-weakened');
  if(canonicalJson(document)!==canonicalJson(expected))errors.push('distribution-source-drift');
  return{ok:errors.length===0,errors:[...new Set(errors)],summary:document.summary??{},digest:sha256(Buffer.from(`${JSON.stringify(document,null,2)}\n`))};
}

export function applyPortalDistributionNegative(document,testCase){
  const mutated=structuredClone(document);
  if(testCase.mutation==='remove-subject')mutated.subjects=mutated.subjects.filter((item)=>item.subjectId!==testCase.subjectId);
  else if(testCase.mutation==='drop-definitive-gap'){const item=mutated.subjects.find((value)=>value.subjectId===testCase.subjectId);item.definitive.gapIds.pop();}
  else if(testCase.mutation==='aggregate-fixed-audit-gaps'){const item=mutated.subjects.find((value)=>value.subjectId===testCase.subjectId);item.fixedCommitAudit.gapIds=['aggregated-gap'];}
  else if(testCase.mutation==='promote-fixture-release'){const item=mutated.subjects.find((value)=>value.subjectId===testCase.subjectId);item.distribution={status:'ready',eligible:true,blockerIds:['none']};}
  else if(testCase.mutation==='establish-from-counts'){mutated.status='established';mutated.boundary={...mutated.boundary,rawCountsAreCompletion:true,completionEffect:'complete',distributionGapEffect:'closed'};}
  else throw new Error(`未知のDistribution負例です: ${testCase.mutation}`);
  return mutated;
}

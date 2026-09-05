import Ajv2020 from 'ajv/dist/2020.js';
import addFormats from 'ajv-formats';
import { readFile } from 'node:fs/promises';
import path from 'node:path';
import { canonicalJson, sha256 } from './crypto.mjs';

const INDEX_PATH='app/data/index.generated.json';

function releaseBinding(subject){
  if(!subject.release)return null;
  return{kind:'fixed-release',version:subject.release.version,digest:subject.release.digest,commit:subject.release.commit,detailUrl:subject.release.detailUrl,artifactDigest:subject.release.artifactDigest,trustUsage:subject.release.trust.usage};
}

function auditBinding(subject){
  if(subject.fixedCommitAudit.availability!=='available')return null;
  const audit=subject.fixedCommitAudit;
  return{kind:'attested-clean-commit',commit:audit.source.commit,tree:audit.source.tree,attestationDigest:audit.source.attestationDigest,detailUrl:audit.detailUrl,artifactDigest:audit.artifactDigest};
}

function bindingGaps(release,audit,definitive){
  const gaps=[];
  if(!release)gaps.push('signed-fixed-release-input-missing');
  else if(release.trustUsage!=='public')gaps.push('public-trust-input-missing');
  if(!audit)gaps.push('fixed-commit-audit-input-missing');
  if(!definitive)gaps.push('definitive-v2-input-missing');
  return gaps;
}

export function buildPortalDistributionInputBindings(index,indexBytes){
  const subjects=index.subjects.map((subject)=>{const release=releaseBinding(subject);const audit=auditBinding(subject);const definitive=null;return{subjectId:subject.id,repository:subject.repository,releaseBinding:release,fixedCommitAuditBinding:audit,definitiveV2Binding:definitive,gapIds:bindingGaps(release,audit,definitive)};});
  const count=(key)=>subjects.filter((subject)=>subject[key]!==null).length;
  const summary={subjects:subjects.length,releaseBindings:count('releaseBinding'),fixedCommitAuditBindings:count('fixedCommitAuditBinding'),definitiveV2Bindings:count('definitiveV2Binding'),publicTrustedReleaseBindings:subjects.filter((subject)=>subject.releaseBinding?.trustUsage==='public').length,unboundReleaseSubjects:subjects.filter((subject)=>subject.releaseBinding===null).length,unboundDefinitiveSubjects:subjects.filter((subject)=>subject.definitiveV2Binding===null).length};
  return{schemaVersion:1,id:'portal-subject-distribution-input-bindings',atlasId:'executable-technology-atlas',scope:'97-subject-fixed-input-provenance',status:summary.unboundDefinitiveSubjects===0&&summary.unboundReleaseSubjects===0?'bound':'incomplete',source:{path:INDEX_PATH,indexDigest:index.digest,artifactDigest:sha256(indexBytes)},summary,subjects,boundary:{readOnly:true,autoPromotion:false,defaultBranchDependency:false,activeSubjectTreeDependency:false,distributionGapEffect:'none',completionEffect:'none'}};
}

export async function loadPortalDistributionBindingInputs(root=process.cwd()){
  const indexBytes=await readFile(path.join(root,INDEX_PATH));const schema=JSON.parse(await readFile(path.join(root,'contracts/schemas/portal-distribution-input-bindings.schema.json'),'utf8'));
  return{indexBytes,index:JSON.parse(indexBytes),schema};
}

async function verifyArtifact(root,binding,subjectId,kind,errors){
  if(!binding)return;
  if(!binding.detailUrl.startsWith('/data/')||binding.detailUrl.includes('..')||binding.detailUrl.includes('default')||binding.detailUrl.includes('branch')){errors.push(`non-fixed-input-reference:${subjectId}:${kind}`);return;}
  try{const bytes=await readFile(path.join(root,'public',binding.detailUrl));if(sha256(bytes)!==binding.artifactDigest)errors.push(`artifact-digest-mismatch:${subjectId}:${kind}`);}catch{errors.push(`artifact-unreadable:${subjectId}:${kind}`);}
}

export async function validatePortalDistributionInputBindings(root,document,schema){
  const errors=[];const ajv=new Ajv2020({allErrors:true,strict:true});addFormats(ajv);const validate=ajv.compile(schema);if(!validate(document))errors.push('schema-invalid');
  const{indexBytes,index}=await loadPortalDistributionBindingInputs(root);const expected=buildPortalDistributionInputBindings(index,indexBytes);const ids=(document.subjects??[]).map((subject)=>subject.subjectId);const expectedIds=expected.subjects.map((subject)=>subject.subjectId);
  if(new Set(ids).size!==ids.length||canonicalJson(ids)!==canonicalJson(expectedIds))errors.push('subject-denominator-reduced-or-reordered');
  for(const expectedSubject of expected.subjects){const actual=(document.subjects??[]).find((subject)=>subject.subjectId===expectedSubject.subjectId);if(!actual)continue;if(canonicalJson(actual.gapIds)!==canonicalJson(expectedSubject.gapIds))errors.push(`binding-gap-granularity-reduced:${expectedSubject.subjectId}`);if(canonicalJson(actual.releaseBinding)!==canonicalJson(expectedSubject.releaseBinding))errors.push(`release-binding-drift:${expectedSubject.subjectId}`);if(canonicalJson(actual.fixedCommitAuditBinding)!==canonicalJson(expectedSubject.fixedCommitAuditBinding))errors.push(`fixed-commit-binding-drift:${expectedSubject.subjectId}`);if(canonicalJson(actual.definitiveV2Binding)!==canonicalJson(expectedSubject.definitiveV2Binding))errors.push(`definitive-binding-fabricated:${expectedSubject.subjectId}`);await verifyArtifact(root,actual.releaseBinding,actual.subjectId,'release',errors);await verifyArtifact(root,actual.fixedCommitAuditBinding,actual.subjectId,'fixed-commit-audit',errors);}
  if(document.status!==expected.status||document.boundary?.readOnly!==true||document.boundary?.autoPromotion!==false||document.boundary?.defaultBranchDependency!==false||document.boundary?.activeSubjectTreeDependency!==false||document.boundary?.distributionGapEffect!=='none'||document.boundary?.completionEffect!=='none')errors.push('binding-boundary-weakened');
  if(canonicalJson(document)!==canonicalJson(expected))errors.push('binding-source-drift');
  return{ok:errors.length===0,errors:[...new Set(errors)],summary:document.summary??{},digest:sha256(Buffer.from(`${JSON.stringify(document,null,2)}\n`))};
}

export function applyPortalDistributionBindingNegative(document,testCase){
  const mutated=structuredClone(document);const item=mutated.subjects.find((subject)=>subject.subjectId===testCase.subjectId);
  if(testCase.mutation==='remove-subject')mutated.subjects=mutated.subjects.filter((subject)=>subject.subjectId!==testCase.subjectId);
  else if(testCase.mutation==='alter-release-commit')item.releaseBinding.commit='main';
  else if(testCase.mutation==='remove-audit-tree')delete item.fixedCommitAuditBinding.tree;
  else if(testCase.mutation==='default-branch-reference')item.releaseBinding.detailUrl='/data/default/main.json';
  else if(testCase.mutation==='fabricate-definitive-binding')item.definitiveV2Binding={kind:'definitive-v2-release',digest:'sha256:0000000000000000000000000000000000000000000000000000000000000000',certificateDigest:'sha256:0000000000000000000000000000000000000000000000000000000000000000'};
  else if(testCase.mutation==='drop-binding-gap')item.gapIds.pop();
  else if(testCase.mutation==='promote-completion'){mutated.status='bound';mutated.boundary.completionEffect='complete';}
  else throw new Error(`未知のDistribution binding負例です: ${testCase.mutation}`);
  return mutated;
}

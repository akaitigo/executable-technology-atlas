import Ajv2020 from 'ajv/dist/2020.js';
import addFormats from 'ajv-formats';
import { readFile } from 'node:fs/promises';
import path from 'node:path';
import { canonicalJson, sha256 } from './crypto.mjs';

const READINESS_PATH='evidence/portal-distribution-readiness.json';

export function buildPortalDistributionGapIndex(readiness,readinessBytes){
  const instances=[];
  for(const[subjectOrdinal,subject]of readiness.subjects.entries())for(const[blockerOrdinal,blockerId]of subject.distribution.blockerIds.entries())instances.push({id:`distribution-gap:${subject.subjectId}:${blockerId}`,subjectId:subject.subjectId,repository:subject.repository,blockerId,status:'open',source:{path:READINESS_PATH,subjectOrdinal,blockerOrdinal},closureEvidence:[],distributionEffect:'none',completionEffect:'none'});
  const counts=new Map();for(const item of instances)counts.set(item.blockerId,(counts.get(item.blockerId)??0)+1);
  const gapCounts=[...counts].sort(([a],[b])=>a.localeCompare(b)).map(([blockerId,openInstances])=>({blockerId,openInstances}));
  return{schemaVersion:1,id:'portal-subject-distribution-gap-index',atlasId:'executable-technology-atlas',scope:'97-subject-open-distribution-gap-instances',status:'open',source:{path:READINESS_PATH,digest:sha256(readinessBytes),indexPath:readiness.source.path,indexDigest:readiness.source.indexDigest},summary:{subjects:readiness.summary.subjects,openInstances:instances.length,closedInstances:0,blockerTypes:gapCounts.length,gapCounts},instances,boundary:{readOnly:true,autoClose:false,aggregateReplacement:false,rawCountsAreCompletion:false,distributionStatus:'not-established',distributionGapEffect:'none',completionEffect:'none'}};
}

export async function loadPortalDistributionGapInputs(root=process.cwd()){
  const readinessBytes=await readFile(path.join(root,READINESS_PATH));const readiness=JSON.parse(readinessBytes);const schema=JSON.parse(await readFile(path.join(root,'contracts/schemas/portal-distribution-gap-index.schema.json'),'utf8'));return{readinessBytes,readiness,schema};
}

export async function validatePortalDistributionGapIndex(root,document,schema){
  const errors=[];const ajv=new Ajv2020({allErrors:true,strict:true});addFormats(ajv);const validate=ajv.compile(schema);if(!validate(document))errors.push('schema-invalid');const{readinessBytes,readiness}=await loadPortalDistributionGapInputs(root);const expected=buildPortalDistributionGapIndex(readiness,readinessBytes);
  const ids=(document.instances??[]).map((item)=>item.id);const expectedIds=expected.instances.map((item)=>item.id);if(new Set(ids).size!==ids.length||canonicalJson(ids)!==canonicalJson(expectedIds))errors.push('gap-instance-denominator-reduced-or-reordered');
  for(const expectedItem of expected.instances){const actual=(document.instances??[]).find((item)=>item.id===expectedItem.id);if(!actual)continue;if(actual.subjectId!==expectedItem.subjectId||actual.repository!==expectedItem.repository||actual.blockerId!==expectedItem.blockerId)errors.push(`gap-identity-rebound:${expectedItem.id}`);if(canonicalJson(actual.source)!==canonicalJson(expectedItem.source))errors.push(`gap-source-drift:${expectedItem.id}`);if(actual.status!=='open'||actual.closureEvidence?.length!==0||actual.distributionEffect!=='none'||actual.completionEffect!=='none')errors.push(`gap-auto-close-forbidden:${expectedItem.id}`);}
  if(canonicalJson(document.summary?.gapCounts)!==canonicalJson(expected.summary.gapCounts)||document.summary?.openInstances!==expected.summary.openInstances||document.summary?.closedInstances!==0)errors.push('gap-taxonomy-aggregated-or-reduced');
  if(document.status!=='open'||document.boundary?.readOnly!==true||document.boundary?.autoClose!==false||document.boundary?.aggregateReplacement!==false||document.boundary?.rawCountsAreCompletion!==false||document.boundary?.distributionStatus!=='not-established'||document.boundary?.distributionGapEffect!=='none'||document.boundary?.completionEffect!=='none')errors.push('gap-boundary-weakened');
  if(canonicalJson(document)!==canonicalJson(expected))errors.push('gap-source-projection-drift');
  return{ok:errors.length===0,errors:[...new Set(errors)],summary:document.summary??{},digest:sha256(Buffer.from(`${JSON.stringify(document,null,2)}\n`))};
}

export function applyPortalDistributionGapNegative(document,testCase){
  const mutated=structuredClone(document);const item=mutated.instances.find((value)=>value.id===testCase.gapId);
  if(testCase.mutation==='remove-instance')mutated.instances=mutated.instances.filter((value)=>value.id!==testCase.gapId);
  else if(testCase.mutation==='aggregate-taxonomy')mutated.summary.gapCounts=[{blockerId:'distribution-gaps',openInstances:mutated.summary.openInstances}];
  else if(testCase.mutation==='rebind-subject')item.subjectId='replacement-subject';
  else if(testCase.mutation==='move-source')item.source.subjectOrdinal+=1;
  else if(testCase.mutation==='close-without-evidence'){item.status='closed';item.distributionEffect='closed';item.completionEffect='complete';}
  else if(testCase.mutation==='establish-from-counts'){mutated.status='closed';mutated.boundary.rawCountsAreCompletion=true;mutated.boundary.distributionStatus='established';}
  else throw new Error(`未知のDistribution Gap負例です: ${testCase.mutation}`);
  return mutated;
}

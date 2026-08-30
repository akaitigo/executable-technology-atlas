import Ajv2020 from 'ajv/dist/2020.js';
import addFormats from 'ajv-formats';
import { sha256, verifyDigest } from './crypto.mjs';

export function validateFixedCommitAudit(envelope,schema,trustedKeys){
  const errors=[];const ajv=new Ajv2020({allErrors:true,strict:true});addFormats(ajv);const validate=ajv.compile(schema);if(!validate(envelope))errors.push(`Fixed commit audit Schema不適合: ${ajv.errorsText(validate.errors)}`);const digest=sha256(envelope?.payload);if(digest!==envelope?.attestation?.digest)errors.push('Fixed commit audit payload digestが一致しません');const trust=trustedKeys.get(envelope?.signature?.keyId);if(!trust)errors.push('Fixed commit audit署名鍵がTrust Storeにありません');else if(!verifyDigest(digest,envelope.signature.value,trust.publicKey))errors.push('Fixed commit audit署名が不正です');const payload=envelope?.payload;if(payload?.releaseBoundary?.signedManifest||payload?.releaseBoundary?.publicTrustKey||payload?.releaseBoundary?.definitiveCertificate)errors.push('未公開固定commitをReleaseまたはDefinitiveとして扱えません');if(payload?.manifest?.status!=='incomplete'||payload?.manifest?.completionClass!=='incomplete')errors.push('incomplete境界を保持していません');if(payload?.manifest?.openRequired===0&&!(payload?.gaps??[]).some((gap)=>gap.id==='definitive-inventory-open-required'))errors.push('bounded open required=0の場合はDefinitive inventoryの未完了を明示する必要があります');if(payload?.core?.definitive?.result!=='fail'||!(payload?.gaps??[]).length)errors.push('Definitive failまたはGapが欠落しています');const depth=payload?.depthReference;if(depth){const counts={satisfied:0,partial:0,missing:0};for(const axis of depth.axes??[])counts[axis.status]=(counts[axis.status]??0)+1;if((depth.axes??[]).length!==18||depth.summary?.axes!==18||counts.satisfied!==depth.summary?.satisfied||counts.partial!==depth.summary?.partial||counts.missing!==depth.summary?.missing||counts.satisfied===18||(depth.axes??[]).some((axis)=>axis.status!=='satisfied'&&!(axis.gaps??[]).length))errors.push('Depth 18軸の分母・状態・Gapが一致しません');}if(payload?.readOnly!==true||payload?.autoPromotion!==false)errors.push('read-only/autoPromotion境界が不正です');return{ok:errors.length===0,errors,digest,trust:{keyId:envelope?.signature?.keyId??null,usage:trust?.usage??'unclassified'}};
}

export function projectFixedCommitAudit(envelope,validated){
  const value=envelope.payload;const summary=(gate,keys)=>({result:gate.result,summary:Object.fromEntries(keys.filter((key)=>gate.summary[key]!==undefined).map((key)=>[key,gate.summary[key]])),...(gate.diagnostics.length?{diagnostics:gate.diagnostics}:{})});const optional=(key,keys)=>value.core[key]?{[key]:summary(value.core[key],keys)}:{};return{schemaVersion:1,subjectId:value.subjectId,atlasId:value.atlasId,status:'fixed-commit-incomplete',source:{repository:value.repository,commit:value.sourceCommit,tree:value.sourceTree,mode:value.sourceMode,attestationDigest:validated.digest,trust:validated.trust},releaseBoundary:value.releaseBoundary,manifest:value.manifest,core:{commit:value.core.commit,audit:summary(value.core.audit,['completionClass','targets','claims','evidence','openRequired']),evidenceDependency:summary(value.core.evidenceDependency,['inputs','changedInputs','outputs','affectedOutputs','runs','missingRequiredOutputs']),authorityExtraction:summary(value.core.authorityExtraction,['status','locked','matched','failed','deferredLocators','humanReviewed','coreV2Eligible']),authorityBody:summary(value.core.authorityBody,['status','sources','documents','matched','failed','candidateAnchors','classified','unclassified','humanReviewed','coreV2Eligible']),authorityReview:summary(value.core.authorityReview,['status','queued','pendingHuman','humanReviewed','unavailableHolds','decisions']),definitive:summary(value.core.definitive,['completionClass','declaredCompletionClass','missingContractArtifacts','openRequired']),...optional('scenarioTrace',['status','rows','runtimeRows','variantCells','closedVariantCells','gaps']),...optional('nonRegression',['missingContractArtifacts','baselineItems','currentItems','replacements']),...optional('evidenceDurability',['missingRequiredOutputs','status','total','passed','failed'])},...(value.depthReference?{depthReference:value.depthReference}:{}),gaps:value.gaps,readOnly:true,autoPromotion:false};
}

export function missingFixedCommitAudit(subject){
  return {
    schemaVersion:1,
    subjectId:subject.id,
    atlasId:null,
    availability:'missing',
    status:'fixed-commit-input-missing',
    source:null,
    manifest:{status:'not-evaluated',openRequired:null},
    gapCount:1,
    gapIds:['fixed-clean-commit-audit-input-missing'],
    detailUrl:null,
    coreGate:{result:'not-run',command:'atlas audit <fixed-clean-commit>',diagnostics:['固定clean commitまたは署名済みReleaseの監査入力がありません']},
    readOnly:true,
    autoPromotion:false,
  };
}

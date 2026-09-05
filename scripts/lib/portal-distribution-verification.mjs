export const DISTRIBUTION_VERIFICATION_CLASSES=['normal','boundary','refusal','failure','recovery','migration','operations','security','performance','compatibility'];

const cell=(classId,state,basis,gapIds=[])=>({classId,state,basis,gapIds});

export function projectSubjectDistributionVerification(subject){
  const definitive=subject.definitiveV2;const audit=subject.fixedCommitAudit;const dependency=subject.evidenceDependency;const release=subject.release;
  const fixedInput=Boolean(release?.verification==='verified'&&release?.artifactDigest&&audit?.availability==='available'&&audit?.artifactDigest);
  const normal=definitive?.status==='subject-definitive'&&release?.trust?.usage==='public';
  const refusal=definitive?.autoPromotion===false&&audit?.autoPromotion===false&&dependency?.autoPromotion===false;
  const failureVisible=(definitive?.gapIds?.length??0)>0&&(audit?.gapIds?.length??0)>0&&definitive?.status!=='subject-definitive';
  const migrated=definitive?.availability==='available'&&definitive?.migration?.status==='migrated';
  const operational=dependency?.status==='current'&&dependency?.coreGate?.result==='pass';
  const publicTrust=release?.trust?.usage==='public'&&definitive?.certificate?.trust?.usage==='public-release';
  return[
    cell('normal',normal?'verified':'gap','definitiveV2.status + release.trust.usage',normal?[]:['subject-definitive-distribution-not-established']),
    cell('boundary',fixedInput?'verified':'gap','release.artifactDigest + fixedCommitAudit.artifactDigest',fixedInput?[]:['fixed-input-binding-incomplete']),
    cell('refusal',refusal?'verified':'gap','definitiveV2/fixedCommitAudit/evidenceDependency.autoPromotion',refusal?[]:['auto-promotion-refusal-not-established']),
    cell('failure',failureVisible?'verified':'gap','definitiveV2.gapIds + fixedCommitAudit.gapIds',failureVisible?[]:['incomplete-gap-visibility-not-established']),
    cell('recovery','not-evaluated','subject-scoped last-known-good recovery runtime', ['subject-recovery-runtime-not-evaluated']),
    cell('migration',migrated?'verified':'gap','definitiveV2.migration.status',migrated?[]:['definitive-v2-migration-incomplete']),
    cell('operations',operational?'verified':'gap','evidenceDependency.status + coreGate.result',operational?[]:['evidence-dependency-not-current']),
    cell('security',publicTrust?'verified':'gap','release.trust + definitive certificate trust',publicTrust?[]:['public-definitive-trust-not-established']),
    cell('performance','not-evaluated','subject-scoped distribution performance runtime', ['subject-performance-runtime-not-evaluated']),
    cell('compatibility','not-evaluated','subject release compatibility proof', ['subject-compatibility-proof-not-evaluated'])
  ];
}

export function summarizeDistributionVerification(subjects){const cells=subjects.flatMap((subject)=>subject.distributionVerification);const count=(state)=>cells.filter((item)=>item.state===state).length;return{subjects:subjects.length,classes:DISTRIBUTION_VERIFICATION_CLASSES.length,cells:cells.length,verified:count('verified'),gap:count('gap'),notEvaluated:count('not-evaluated'),completionEffect:'none'};}

import { sha256 } from './crypto.mjs';

export function validateDepthReference(envelope, lock, verification) {
  const errors = [...(verification?.errors ?? [])];
  const reference = envelope?.payload;
  const release = envelope?.release;
  const axes = reference?.axes ?? [];
  const counts = Object.fromEntries(['satisfied','partial','missing'].map((state) => [state, axes.filter((axis) => axis.status === state).length]));
  const expected = lock.expectedSummary;
  const uniqueAxisIds = new Set(axes.map((axis) => axis.id));
  const sourceBytes = envelope?.source?.bytes;

  if (envelope?.kind !== 'portal-depth-reference') errors.push('Depth Reference kindが不正です');
  if (release?.subjectId !== lock.subjectId || release?.atlasId !== lock.atlasId) errors.push('Depth ReferenceのSubject bindingがLockと一致しません');
  if (release?.repository !== lock.repository || release?.commit !== lock.sourceCommit || release?.path !== lock.sourcePath) errors.push('Depth Referenceの固定Source bindingがLockと一致しません');
  if (reference?.id !== lock.referenceId || reference?.schemaVersion !== 1) errors.push('Depth Reference schema/idがLockと一致しません');
  if (reference?.status !== lock.expectedStatus || reference?.completionClaim !== lock.expectedCompletionClaim) errors.push('Depth Referenceを未完成以外へ格上げできません');
  if (axes.length !== expected.axes || uniqueAxisIds.size !== axes.length) errors.push(`Depth Referenceは一意な${expected.axes}軸が必要です`);
  for (const state of ['satisfied','partial','missing']) if (counts[state] !== expected[state] || reference?.summary?.[state] !== expected[state]) errors.push(`Depth Reference ${state}件数がLockと一致しません`);
  if (typeof sourceBytes !== 'string' || sha256(sourceBytes) !== lock.sourceDigest) errors.push('FE_DEPTH_REFERENCE.jsonのSource digestがLockと一致しません');
  else {
    try { if (sha256(JSON.parse(sourceBytes)) !== sha256(reference)) errors.push('Source bytesとDepth Reference payloadが一致しません'); }
    catch { errors.push('Depth Reference source bytesがJSONではありません'); }
  }
  for (const axis of axes) {
    if (!axis.id || !axis.title || !axis.denominator || !['satisfied','partial','missing'].includes(axis.status)) errors.push(`Depth axisの状態・分母が不完全です: ${axis.id ?? '(unknown)'}`);
    if (!Array.isArray(axis.checks) || axis.checks.length === 0 || axis.checks.some((check) => !check.id || !check.status || !check.required || check.observed === undefined || !Array.isArray(check.evidence) || check.evidence.length === 0)) errors.push(`Depth axisのProofが不完全です: ${axis.id ?? '(unknown)'}`);
    if (axis.status !== 'satisfied' && (!Array.isArray(axis.gaps) || axis.gaps.length === 0)) errors.push(`未充足Depth axisのGapがありません: ${axis.id ?? '(unknown)'}`);
  }
  return { ok: errors.length === 0, errors, counts, axes: axes.length };
}

export function projectDepthReference(envelope, verification) {
  const reference = envelope.payload;
  return {
    id: reference.id,
    status: reference.status,
    completionClaim: reference.completionClaim,
    summary: { axes:reference.axes.length, ...reference.summary },
    denominatorPolicy: reference.denominatorPolicy,
    observedDensity: reference.observedDensity,
    axes: reference.axes,
    source: {
      repository: envelope.release.repository,
      commit: envelope.release.commit,
      path: envelope.release.path,
      digest: envelope.source.digest,
      envelopeDigest: envelope.release.digest,
      signature: envelope.signature,
      trust: verification.trust,
    },
    completion: { definitive:false, bounded:false, reason:'canonical-depth-reference-incomplete' },
  };
}

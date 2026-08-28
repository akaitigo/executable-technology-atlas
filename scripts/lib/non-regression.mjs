import { readFile } from 'node:fs/promises';
import path from 'node:path';
import { sha256 } from './crypto.mjs';
import { scanNeutralLanguage } from './neutral-language.mjs';

export const NON_REGRESSION_BASELINE_DIGEST = 'sha256:26199a179dc48bd5b36826a404395589d38be5aae40cca6bbb1fe77fb1c41fc7';
export const DEPTH_REFERENCE_LOCK_DIGEST = 'sha256:077bb3514401dc3dafb250d8a8af860440ef3ad9c898ffc9286b4e728cb2c514';
const OPEN_STATES = new Set(['missing','planned','partial','expired','unclassified']);

const hasFields = (value, fields = []) => fields.every((field) => value?.[field] !== null && value?.[field] !== undefined);
const mappingIndex = (items = []) => new Map(items.map((item) => [item.from, item]));
const validMapping = (mapping) => Boolean(mapping?.to && mapping?.rationale?.length >= 20 && mapping?.informationPreserved === true && mapping?.evidencePolicy === 'same-or-stronger');

export async function evaluateNonRegression(root = process.cwd(), options = {}) {
  const readJson = async (file) => JSON.parse(await readFile(path.join(root, file), 'utf8'));
  const [baselineBytes, baseline, mappings, index, failures, page, depthLockBytes, depthLock, registry] = await Promise.all([
    readFile(path.join(root, 'contracts/non-regression-baseline.json')),
    readJson('contracts/non-regression-baseline.json'),
    readJson('contracts/non-regression-mappings.json'),
    readJson('app/data/index.generated.json'),
    readJson('fixtures/failure-scenarios.json'),
    readFile(path.join(root, 'app/page.tsx'), 'utf8'),
    readFile(path.join(root, 'contracts/depth-reference-lock.json')),
    readJson('contracts/depth-reference-lock.json'),
    readJson('fixtures/registry.json'),
  ]);
  const violations = [];
  const checks = [];
  const fail = (code, detail) => violations.push({ code, detail });
  const check = (name, pass, detail) => { checks.push({ name, pass, detail }); if (!pass) fail(name, detail); };
  check('baseline-immutable', sha256(baselineBytes) === NON_REGRESSION_BASELINE_DIGEST, `expected ${NON_REGRESSION_BASELINE_DIGEST}`);
  check('baseline-schema', baseline.schemaVersion === 1 && baseline.policy?.aggregateReplacement === 'reject', 'schemaVersion=1 / aggregateReplacement=reject');
  check('mapping-schema', mappings.schemaVersion === 1 && ['subjectMappings','targetMappings','evidenceMappings'].every((key) => Array.isArray(mappings[key])), 'mapping arrays required');
  check('depth-reference-lock-immutable', sha256(depthLockBytes) === DEPTH_REFERENCE_LOCK_DIGEST, `expected ${DEPTH_REFERENCE_LOCK_DIGEST}`);

  const subjectMappings = mappingIndex(mappings.subjectMappings);
  const targetMappings = mappingIndex(mappings.targetMappings);
  const evidenceMappings = mappingIndex(mappings.evidenceMappings);
  const currentSubjects = new Map(index.subjects.map((subject) => [subject.id, subject]));
  let baselineTargetCount = 0;
  let baselineEvidenceCount = 0;
  let mappedCount = 0;

  for (const oldSubject of baseline.subjects) {
    const subjectMapping = subjectMappings.get(oldSubject.id);
    if (subjectMapping && !validMapping(subjectMapping)) fail('invalid-subject-mapping', oldSubject.id);
    const currentId = validMapping(subjectMapping) ? subjectMapping.to : oldSubject.id;
    if (currentId !== oldSubject.id) mappedCount += 1;
    const current = currentSubjects.get(currentId);
    if (!current) { fail('subject-deleted', oldSubject.id); continue; }
    if (!validMapping(subjectMapping) && current.repository !== oldSubject.repository) fail('subject-identity-replaced-without-mapping', `${oldSubject.id}: ${oldSubject.repository} -> ${current.repository}`);
    if (!hasFields(current, oldSubject.fields)) fail('subject-information-reduced', `${oldSubject.id} -> ${currentId}`);
    if ((current.scope?.length ?? 0) < oldSubject.scopeLength) fail('subject-scope-aggregated', `${oldSubject.id}: ${current.scope?.length ?? 0} < ${oldSubject.scopeLength}`);
    for (const exclusion of oldSubject.excludes) if (!current.excludes?.includes(exclusion)) fail('subject-exclusion-hidden', `${oldSubject.id}: ${exclusion}`);
    const currentDefinitive = Boolean(current.completion?.definitive ?? current.release?.completion?.definitive);
    if (oldSubject.status !== 'complete' && current.status === 'complete' && !currentDefinitive) fail('catalog-status-promoted', `${oldSubject.id}: ${oldSubject.status} -> complete`);

    for (const oldRelease of oldSubject.releases) {
      const currentRelease = current.releaseHistory?.find((release) => release.digest === oldRelease.digest);
      if (!currentRelease) { fail('release-history-deleted', `${oldSubject.id}: ${oldRelease.digest}`); continue; }
      if (currentRelease.status !== oldRelease.status) fail('release-history-status-rewritten', `${oldSubject.id}: ${oldRelease.status} -> ${currentRelease.status}`);
      if (currentRelease.completion?.classification !== oldRelease.completionClass || currentRelease.completion?.definitive !== oldRelease.definitive) fail('release-history-completion-rewritten', `${oldSubject.id}: ${oldRelease.digest}`);
      if (oldRelease.completionClass === 'bounded-historical' && currentRelease.completion?.definitive) fail('bounded-promoted-to-definitive', `${oldSubject.id}: ${oldRelease.digest}`);
      let historicalDetail;
      try { historicalDetail = await readJson(path.join('public', currentRelease.detailUrl)); }
      catch { fail('release-detail-hidden', `${oldSubject.id}: ${oldRelease.digest}`); continue; }
      const historicalTargets = new Map((historicalDetail.targets ?? []).map((target) => [target.id, target]));
      const historicalEvidence = new Map((historicalDetail.evidence ?? []).map((record) => [record.id, record]));
      baselineTargetCount += oldRelease.targets.length;
      baselineEvidenceCount += oldRelease.evidence.length;
      for (const oldTarget of oldRelease.targets) {
        const target = historicalTargets.get(oldTarget.id);
        if (!target) { fail('target-history-deleted', `${oldSubject.id}/${oldTarget.id}`); continue; }
        if (!hasFields(target, oldTarget.fields) || !hasFields(target.exclusion, oldTarget.exclusionFields)) fail('target-information-reduced', `${oldSubject.id}/${oldTarget.id}`);
        if (target.state !== oldTarget.state || target.requirement !== oldTarget.requirement) fail('target-history-status-rewritten', `${oldSubject.id}/${oldTarget.id}: ${oldTarget.state} -> ${target.state}`);
        for (const evidenceId of oldTarget.evidenceIds) if (!target.evidence_ids?.includes(evidenceId)) fail('target-evidence-link-deleted', `${oldSubject.id}/${oldTarget.id}/${evidenceId}`);
      }
      for (const oldEvidence of oldRelease.evidence) {
        const record = historicalEvidence.get(oldEvidence.id);
        if (!record) { fail('evidence-history-deleted', `${oldSubject.id}/${oldEvidence.id}`); continue; }
        if (!hasFields(record, oldEvidence.fields) || !hasFields(record.environment, oldEvidence.environmentFields) || !hasFields(record.artifact, oldEvidence.artifactFields)) fail('evidence-information-reduced', `${oldSubject.id}/${oldEvidence.id}`);
        if (record.verdict !== oldEvidence.verdict || record.kind !== oldEvidence.kind || record.environment?.profile !== oldEvidence.environmentProfile || record.artifact?.digest !== oldEvidence.artifactDigest) fail('evidence-history-rewritten', `${oldSubject.id}/${oldEvidence.id}`);
      }
    }

    const oldCurrent = oldSubject.releases.at(-1);
    const newCurrent = current.release;
    if (!oldCurrent || !newCurrent || newCurrent.digest === oldCurrent.digest) continue;
    if (newCurrent.status === 'complete' && !newCurrent.completion?.definitive) fail('release-status-promoted', `${oldSubject.id}: ${newCurrent.digest}`);
    let currentDetail;
    try { currentDetail = await readJson(path.join('public', newCurrent.detailUrl)); }
    catch { fail('current-release-detail-hidden', `${currentId}: ${newCurrent.digest}`); continue; }
    const currentTargets = new Map((currentDetail.targets ?? []).map((target) => [target.id, target]));
    const currentEvidence = new Map((currentDetail.evidence ?? []).map((record) => [record.id, record]));
    for (const oldTarget of oldCurrent.targets) {
      const from = `${oldSubject.id}:${oldTarget.id}`;
      const mapping = targetMappings.get(from);
      if (mapping && !validMapping(mapping)) fail('invalid-target-mapping', from);
      const targetId = validMapping(mapping) ? mapping.to.split(':').at(-1) : oldTarget.id;
      if (targetId !== oldTarget.id) mappedCount += 1;
      const target = currentTargets.get(targetId);
      if (!target) { fail('target-deleted-from-current', from); continue; }
      if (!hasFields(target, oldTarget.fields) || !hasFields(target.exclusion, oldTarget.exclusionFields)) fail('target-current-information-reduced', from);
      if (oldTarget.state === 'excluded' || oldTarget.state === 'infeasible') {
        if (target.state !== oldTarget.state && !validMapping(mapping)) fail('closure-state-hidden', `${from}: ${oldTarget.state} -> ${target.state}`);
      } else if (OPEN_STATES.has(oldTarget.state) && target.state === 'covered') {
        const linked = target.evidence_ids ?? [];
        const passEvidence = linked.filter((id) => currentEvidence.get(id)?.verdict === 'pass');
        if (linked.length <= oldTarget.evidenceIds.length || passEvidence.length !== linked.length) fail('target-status-promoted-without-stronger-evidence', from);
      }
    }
    for (const oldEvidence of oldCurrent.evidence) {
      const from = `${oldSubject.id}:${oldEvidence.id}`;
      const mapping = evidenceMappings.get(from);
      if (mapping && !validMapping(mapping)) fail('invalid-evidence-mapping', from);
      const evidenceId = validMapping(mapping) ? mapping.to.split(':').at(-1) : oldEvidence.id;
      if (evidenceId !== oldEvidence.id) mappedCount += 1;
      const record = currentEvidence.get(evidenceId);
      if (!record) { fail('evidence-deleted-from-current', from); continue; }
      if (!hasFields(record, oldEvidence.fields) || !hasFields(record.environment, oldEvidence.environmentFields) || !hasFields(record.artifact, oldEvidence.artifactFields)) fail('evidence-current-information-reduced', from);
    }
  }

  const currentFailures = new Map(failures.scenarios.map((scenario) => [scenario.id, scenario]));
  for (const oldFailure of baseline.failureScenarios) {
    const current = currentFailures.get(oldFailure.id);
    if (!current) { fail('failure-scenario-deleted', oldFailure.id); continue; }
    for (const key of Object.keys(oldFailure)) {
      if (current[key] === undefined) fail('failure-information-reduced', `${oldFailure.id}/${key}`);
      else if (['expected','state','status','verdict','mutation'].includes(key) && current[key] !== oldFailure[key]) fail('failure-semantics-hidden', `${oldFailure.id}/${key}`);
      else if (typeof oldFailure[key] === 'string' && typeof current[key] === 'string' && current[key].length < oldFailure[key].length) fail('failure-information-aggregated', `${oldFailure.id}/${key}`);
    }
  }

  const uiTokens = ['missing','planned','partial','covered','excluded','infeasible','expired','Evidence観測Profile','Subject Definitive未証明','固定Release履歴','Failure visibility baseline'];
  for (const token of uiTokens) if (!page.includes(token)) fail('ui-visibility-missing', token);
  if (page.includes('detail.evidence.slice(')) fail('evidence-list-truncated', 'detail.evidence.slice must not be used');
  if (!page.includes("const [status, setStatus] = useState('')")) fail('filter-default-excludes', '状態Filter must default to all');
  if (!page.includes('subject.releaseHistory.map(')) fail('release-history-ui-aggregated', 'Release history must remain individually visible');
  if (!page.includes('detail.evidence.map(')) fail('evidence-ui-aggregated', 'Evidence IDs must remain individually visible');
  if (!page.includes('gaps.map(')) fail('target-gap-ui-aggregated', 'Target gaps must remain individually visible');
  if (!page.includes('atlasIndex.failureVisibility.scenarios.map(')) fail('failure-ui-aggregated', 'Failure scenarios must remain individually visible');
  for (const token of ['reference.axes.map(','axis.checks.map(','axis.gaps.map(','Test成功は各軸のProof','bounded={String(reference.completion.bounded)}','definitive={String(reference.completion.definitive)}']) if (!page.includes(token)) fail('depth-reference-ui-reduced', token);

  const depthRegistry = (registry.depthReferences ?? []).find((item) => item.subjectId === depthLock.subjectId);
  const depthSubject = currentSubjects.get(depthLock.subjectId);
  const depthSummary = depthSubject?.depthReference;
  let depthFixture = null;
  let depthDetail = null;
  try { depthFixture = await readJson(depthRegistry?.file ? path.join('fixtures',depthRegistry.file) : '(missing)'); }
  catch { fail('depth-reference-fixture-hidden', depthLock.subjectId); }
  try { depthDetail = await readJson(path.join('public',depthSubject?.release?.detailUrl ?? '(missing)')); }
  catch { fail('depth-reference-detail-hidden', depthLock.subjectId); }
  if (depthRegistry?.commit !== depthLock.sourceCommit || depthRegistry?.sourceDigest !== depthLock.sourceDigest) fail('depth-reference-source-rewritten', depthLock.subjectId);
  if (depthFixture?.source?.digest !== depthLock.sourceDigest || depthFixture?.release?.commit !== depthLock.sourceCommit) fail('depth-reference-source-binding-reduced', depthLock.subjectId);
  if (depthSummary?.status !== 'incomplete' || depthSummary?.completion?.bounded !== false || depthSummary?.completion?.definitive !== false) fail('depth-reference-status-promoted', depthLock.subjectId);
  if (depthSummary?.summary?.axes !== 18 || depthSummary?.summary?.satisfied !== 1 || depthSummary?.summary?.partial !== 17) fail('depth-reference-summary-rewritten', depthLock.subjectId);
  if (JSON.stringify(depthDetail?.depthReference?.axes) !== JSON.stringify(depthFixture?.payload?.axes)) fail('depth-reference-axis-information-reduced', depthLock.subjectId);
  for (const axis of depthDetail?.depthReference?.axes ?? []) {
    if (!axis.denominator) fail('depth-reference-denominator-hidden', axis.id);
    if (!axis.checks?.length) fail('depth-reference-proof-hidden', axis.id);
    if (axis.status !== 'satisfied' && !axis.gaps?.length) fail('depth-reference-gap-hidden', axis.id);
  }

  const releases = index.subjects.flatMap((subject) => subject.release ? [subject.release] : []);
  for (const release of index.subjects.flatMap((subject) => subject.releaseHistory ?? [])) {
    if (release.completion?.definitive && (release.completion.classification === 'bounded-historical' || release.completion.certificateSchemaVersion === 1)) fail('bounded-promoted-to-definitive', release.digest);
  }
  const neutralLanguage = options.scanLanguage === false ? { verdict:'skipped', filesScanned:0, violations:[] } : await scanNeutralLanguage(root);
  for (const violation of neutralLanguage.violations) fail(`neutral-language-${violation.code}`, `${violation.file}:${violation.line}`);
  const summary = {
    baselineSubjects: baseline.subjects.length,
    currentSubjects: index.subjects.length,
    baselineTargets: baselineTargetCount,
    baselineEvidence: baselineEvidenceCount,
    failureScenarios: baseline.failureScenarios.length,
    openRequired: releases.reduce((sum, release) => sum + (release.coverage?.openRequired ?? Math.max(0, (release.coverage?.required ?? 0) - (release.coverage?.closed ?? 0))), 0),
    unclassified: index.subjects.filter((subject) => (subject.completion?.classification ?? (subject.release ? subject.release.completion?.classification : 'unclassified')) === 'unclassified').length,
    boundedHistorical: index.subjects.flatMap((subject) => subject.releaseHistory ?? []).filter((release) => release.completion?.classification === 'bounded-historical').length,
    subjectDefinitive: releases.filter((release) => release.completion?.definitive).length,
    depthReferenceAxes: depthDetail?.depthReference?.axes?.length ?? 0,
    depthReferenceSatisfied: depthDetail?.depthReference?.summary?.satisfied ?? 0,
    depthReferencePartial: depthDetail?.depthReference?.summary?.partial ?? 0,
    mappingsApplied: mappedCount,
    violations: violations.length,
  };
  return { schemaVersion: 1, baselineDigest: NON_REGRESSION_BASELINE_DIGEST, generatedAt: index.generatedAt, verdict: violations.length ? 'fail' : 'pass', summary, neutralLanguage, checks, violations };
}

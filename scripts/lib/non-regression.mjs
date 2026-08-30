import { readFile } from 'node:fs/promises';
import path from 'node:path';
import { sha256 } from './crypto.mjs';
import { scanNeutralLanguage } from './neutral-language.mjs';

export const NON_REGRESSION_BASELINE_DIGEST = 'sha256:26199a179dc48bd5b36826a404395589d38be5aae40cca6bbb1fe77fb1c41fc7';
export const DEPTH_REFERENCE_LOCK_DIGEST = 'sha256:077bb3514401dc3dafb250d8a8af860440ef3ad9c898ffc9286b4e728cb2c514';
export const AUTHORITY_REVIEW_LOCK_DIGEST = 'sha256:521a4056e9b5907a8f927023f1ea9ad67835353b63831998b145a60a1ca4075f';
export const EVIDENCE_DEPENDENCY_LOCK_DIGEST = 'sha256:720ece5c5287b40c62d71f2eba61d9c8a366c7664afc32b817358b3035a23156';
export const DEFINITIVE_V2_LOCK_DIGEST = 'sha256:ae99e7f23ad0043a38a37e94d70ae2be5402e71a8936cb6b8d4f3931ee49c8b5';
const OPEN_STATES = new Set(['missing','planned','partial','expired','unclassified']);

const hasFields = (value, fields = []) => fields.every((field) => value?.[field] !== null && value?.[field] !== undefined);
const mappingIndex = (items = []) => new Map(items.map((item) => [item.from, item]));
const validMapping = (mapping) => Boolean(mapping?.to && mapping?.rationale?.length >= 20 && mapping?.informationPreserved === true && mapping?.evidencePolicy === 'same-or-stronger');

export async function evaluateNonRegression(root = process.cwd(), options = {}) {
  const readJson = async (file) => JSON.parse(await readFile(path.join(root, file), 'utf8'));
  const [baselineBytes, baseline, mappings, index, failures, page, depthLockBytes, depthLock, reviewLockBytes, reviewLock, dependencyLockBytes, dependencyLock, definitiveLockBytes, definitiveLock, registry] = await Promise.all([
    readFile(path.join(root, 'contracts/non-regression-baseline.json')),
    readJson('contracts/non-regression-baseline.json'),
    readJson('contracts/non-regression-mappings.json'),
    readJson('app/data/index.generated.json'),
    readJson('fixtures/failure-scenarios.json'),
    readFile(path.join(root, 'app/page.tsx'), 'utf8'),
    readFile(path.join(root, 'contracts/depth-reference-lock.json')),
    readJson('contracts/depth-reference-lock.json'),
    readFile(path.join(root, 'contracts/authority-review-lock.json')),
    readJson('contracts/authority-review-lock.json'),
    readFile(path.join(root, 'contracts/evidence-dependency-lock.json')),
    readJson('contracts/evidence-dependency-lock.json'),
    readFile(path.join(root, 'contracts/definitive-v2-lock.json')),
    readJson('contracts/definitive-v2-lock.json'),
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
  check('authority-review-lock-immutable',sha256(reviewLockBytes)===AUTHORITY_REVIEW_LOCK_DIGEST,`expected ${AUTHORITY_REVIEW_LOCK_DIGEST}`);
  check('evidence-dependency-lock-immutable',sha256(dependencyLockBytes)===EVIDENCE_DEPENDENCY_LOCK_DIGEST,`expected ${EVIDENCE_DEPENDENCY_LOCK_DIGEST}`);
  check('evidence-dependency-core-main',dependencyLock.coreRef==='main'&&dependencyLock.coreCommitStatus==='official-main-ci-passed'&&dependencyLock.coreCommit==='072d7ca77981f51754e824d70c6d4ecd55ea67e5',dependencyLock.coreCommit);
  check('definitive-v2-lock-immutable',sha256(definitiveLockBytes)===DEFINITIVE_V2_LOCK_DIGEST,`expected ${DEFINITIVE_V2_LOCK_DIGEST}`);
  check('definitive-v2-core-main',definitiveLock.coreRef==='main'&&definitiveLock.coreCommitStatus==='official-main-ci-passed'&&definitiveLock.coreCommit==='072d7ca77981f51754e824d70c6d4ecd55ea67e5'&&definitiveLock.writePolicy==='read-only'&&definitiveLock.autoPromotion===false,definitiveLock.coreCommit);

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
  for(const token of ['Priority','Batch','Stale relock hold','pending','reviewed','include','exclude','merge','split','defer','一次資料をURL＋locatorで開く','write_decisions=false','Core共通API未接続','機械proposal / Human decisionではない','human decision 0件を進捗として扱いません'])if(!page.includes(token))fail('authority-review-ui-reduced',token);
  for(const forbidden of ['item.body','item.text','item.content','item.html','item.excerpt'])if(page.includes(forbidden))fail('authority-body-copied-to-ui',forbidden);
  for(const token of ['Evidence Dependency Graph','Inputs — changed / current','Impacted outputs — stale / current','Missing required output','Proof / Closure structure drift','digest更新だけを「復旧済み」と表示せず','autoPromotion=false'])if(!page.includes(token))fail('evidence-dependency-ui-reduced',token);
  for(const token of ['Core Definitive Gate v2','bounded-complete / bounded historical','Authority-derived inventory closure','実Runtime Profile','definitive.gapIds.map(','Migration actions','readOnly=','autoPromotion=','これらは達成件数ではなく','Inventory未評価','既知open required','Runtime未検証','全SubjectのGap内訳','summary.gapCounts.map'])if(!page.includes(token))fail('definitive-v2-ui-reduced',token);

  for(const subject of index.subjects){const dependency=subject.evidenceDependency;if(!dependency){fail('evidence-dependency-subject-hidden',subject.id);continue;}if(dependency.autoPromotion!==false||dependency.readOnly!==true)fail('evidence-dependency-write-boundary-weakened',subject.id);if(dependency.status==='current'&&(dependency.availability!=='available'||dependency.coreGate?.result!=='pass'||dependency.coreGate?.coreCommit!==dependencyLock.coreCommit))fail('evidence-dependency-current-without-core-gate',subject.id);if(dependency.availability==='missing'&&(dependency.status!=='missing-required-output'||dependency.coreGate?.result!=='not-run'))fail('evidence-dependency-missing-promoted',subject.id);}
  for(const subject of index.subjects){const definitive=subject.definitiveV2;if(!definitive){fail('definitive-v2-subject-hidden',subject.id);continue;}if(definitive.autoPromotion!==false||definitive.readOnly!==true)fail('definitive-v2-write-boundary-weakened',subject.id);if(definitive.coreContract?.commit!==definitiveLock.coreCommit)fail('definitive-v2-core-binding-rewritten',subject.id);if(definitive.status==='subject-definitive'&&(definitive.availability!=='available'||definitive.coreGate?.result!=='pass'||definitive.certificate?.schemaVersion!==2||definitive.certificate?.trust?.usage!=='public-release'||definitive.inventoryClosure?.status!=='closed'||definitive.inventoryClosure?.unclassified!==0||definitive.inventoryClosure?.openRequired!==0||definitive.gapIds?.length))fail('definitive-v2-promoted-without-gate',subject.id);if(definitive.availability==='missing'&&(definitive.status!=='subject-definitive-input-missing'||definitive.coreGate?.result!=='not-run'||!definitive.gapIds?.length))fail('definitive-v2-missing-promoted',subject.id);}
  const definitiveValues=index.subjects.map((subject)=>subject.definitiveV2).filter(Boolean);const expectedDefinitiveGaps=[...definitiveValues.flatMap((value)=>value.gapIds).reduce((counts,id)=>counts.set(id,(counts.get(id)??0)+1),new Map())].map(([id,count])=>({id,count})).sort((a,b)=>a.id.localeCompare(b.id));const expectedDefinitiveProfiles=definitiveValues.flatMap((value)=>value.runtimeProfiles);const definitiveSummary=index.definitiveV2Summary;if(definitiveSummary?.inventoryUnevaluated!==definitiveValues.filter((value)=>value.inventoryClosure.status==='not-evaluated').length||definitiveSummary?.openRequiredKnown!==definitiveValues.reduce((sum,value)=>sum+(value.inventoryClosure.openRequired??0),0)||definitiveSummary?.excluded!==definitiveValues.reduce((sum,value)=>sum+value.inventoryClosure.excluded,0)||definitiveSummary?.infeasible!==definitiveValues.reduce((sum,value)=>sum+value.inventoryClosure.infeasible,0)||definitiveSummary?.runtimeProfilesUnverified!==expectedDefinitiveProfiles.filter((value)=>value.status!=='current'||!value.runtimeIdentity).length||definitiveSummary?.gapInstances!==expectedDefinitiveGaps.reduce((sum,value)=>sum+value.count,0)||JSON.stringify(definitiveSummary?.gapCounts)!==JSON.stringify(expectedDefinitiveGaps))fail('definitive-v2-summary-information-reduced','aggregate must equal per-subject gaps, inventory, and runtime state');

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

  const reviewSubject=currentSubjects.get(reviewLock.subjectId);const review=reviewSubject?.authorityReview;const expectedReview=reviewLock.expected;
  let reviewExport=null;let reviewExportBytes=null;try{reviewExportBytes=await readFile(path.join(root,'public',review?.exportUrl??'(missing)'));reviewExport=JSON.parse(reviewExportBytes);}catch{fail('authority-review-export-hidden',reviewLock.subjectId);}
  if(review?.source?.commit!==reviewLock.sourceCommit||review?.source?.exportDigest!==reviewLock.exportDigest||review?.source?.exportSchemaDigest!==reviewLock.exportSchemaDigest||review?.source?.packetSchemaDigest!==reviewLock.packetSchemaDigest)fail('authority-review-source-rewritten',reviewLock.subjectId);
  if(review?.status!=='incomplete-human-review-required'||review?.mode!=='read-only'||review?.capabilities?.write_decisions!==false||review?.capabilities?.promote_human_review!==false)fail('authority-review-contract-weakened',reviewLock.subjectId);
  const reviewFields={packets:expectedReview.packets,unique_anchors:expectedReview.uniqueAnchors,candidate_domain_projections:expectedReview.candidateDomainProjections,deep_links:expectedReview.deepLinks,pending_human:expectedReview.pendingHuman,human_reviewed:expectedReview.humanReviewed,proposed_clusters:expectedReview.proposedClusters,semantic_decisions_by_export:expectedReview.semanticDecisionsByExport,stale_document_holds:expectedReview.staleDocumentHolds,decisions:expectedReview.decisions};for(const[field,value]of Object.entries(reviewFields))if(review?.summary?.[field]!==value)fail('authority-review-summary-rewritten',`${field}: ${review?.summary?.[field]} != ${value}`);
  if(review?.summary?.has_human_progress!==false||reviewExport?.decision_boundary?.export_accepts_writes!==false)fail('zero-decision-progress-inflated',reviewLock.subjectId);
  if(sha256(reviewExportBytes)!==reviewLock.exportDigest)fail('authority-review-export-bytes-rewritten',reviewLock.subjectId);
  if(reviewExport?.packets?.length!==expectedReview.packets||reviewExport?.proposed_clusters?.length!==expectedReview.proposedClusters||reviewExport?.stale_holds?.length!==expectedReview.staleDocumentHolds)fail('authority-review-export-aggregated',reviewLock.subjectId);
  if(reviewExport?.proposed_clusters?.some((item)=>item.semantic_decision!=='none-machine-proposal-only'||item.human_reviewed!==false)||reviewExport?.stale_candidate_report?.human_choices!==0)fail('authority-review-machine-promoted',reviewLock.subjectId);

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
    authorityReviewPackets: review?.summary?.packets ?? 0,
    authorityReviewPending: review?.summary?.pending_human ?? 0,
    authorityHumanReviewed: review?.summary?.human_reviewed ?? 0,
    authorityReviewDecisions: review?.summary?.decisions ?? 0,
    authorityStaleHolds: review?.summary?.stale_document_holds ?? 0,
    evidenceDependencyCurrent: index.subjects.filter((subject)=>subject.evidenceDependency?.status==='current').length,
    evidenceDependencyStale: index.subjects.filter((subject)=>subject.evidenceDependency?.status==='stale-or-incomplete').length,
    evidenceDependencyMissing: index.subjects.filter((subject)=>subject.evidenceDependency?.status==='missing-required-output').length,
    definitiveV2Complete: index.subjects.filter((subject)=>subject.definitiveV2?.status==='subject-definitive').length,
    definitiveV2Incomplete: index.subjects.filter((subject)=>subject.definitiveV2?.status==='subject-definitive-incomplete').length,
    definitiveV2Missing: index.subjects.filter((subject)=>subject.definitiveV2?.status==='subject-definitive-input-missing').length,
    definitiveV2OpenRequiredKnown: index.definitiveV2Summary?.openRequiredKnown ?? 0,
    definitiveV2InventoryUnevaluated: index.definitiveV2Summary?.inventoryUnevaluated ?? 0,
    definitiveV2RuntimeUnverified: index.definitiveV2Summary?.runtimeProfilesUnverified ?? 0,
    definitiveV2GapInstances: index.definitiveV2Summary?.gapInstances ?? 0,
    mappingsApplied: mappedCount,
    violations: violations.length,
  };
  return { schemaVersion: 1, baselineDigest: NON_REGRESSION_BASELINE_DIGEST, generatedAt: index.generatedAt, verdict: violations.length ? 'fail' : 'pass', summary, neutralLanguage, checks, violations };
}

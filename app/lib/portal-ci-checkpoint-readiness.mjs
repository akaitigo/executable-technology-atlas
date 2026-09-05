const EXACT = Object.freeze({
  schemaVersion: 1,
  id: 'portal-ci-checkpoint-readiness',
  classification: 'portal-integration-checkpoint-readiness-only',
  summary: { prerequisites: 9, satisfied: 3, blocked: 6 },
  subjectAggregation: { subjects: 97, subjectDefinitive: 0, definitiveMissing: 97, openRequired: 119, unclassified: 90, gapInstances: 388 },
  distribution: { ready: 0, blockerInstances: 589 },
  root: { missingArtifacts: 5 },
  dependencyGraph: { recordedRequiredOutputs: 39 },
});

function isObject(value) {
  return Boolean(value) && typeof value === 'object' && !Array.isArray(value);
}

function isInteger(value) {
  return Number.isInteger(value) && value >= 0;
}

function read(value, key) {
  return isObject(value) ? value[key] : undefined;
}

function exact(value, expected) {
  return value === expected;
}

function assertBoolean(value, expected) {
  return typeof value === 'boolean' && value === expected;
}

export function isPortalCiCheckpointReadinessSnapshot(value) {
  const observed = read(value, 'observed');
  const git = read(observed, 'git');
  const workflow = read(observed, 'workflow');
  const signingPolicy = read(observed, 'signingPolicy');
  const subjectAggregation = read(observed, 'subjectAggregation');
  const distribution = read(observed, 'distribution');
  const root = read(observed, 'root');
  const dependencyGraph = read(observed, 'dependencyGraph');
  const ci = read(observed, 'ci');
  const summary = read(value, 'summary');
  const boundary = read(value, 'boundary');
  return isObject(value)
    && exact(value.schemaVersion, EXACT.schemaVersion)
    && exact(value.id, EXACT.id)
    && exact(value.classification, EXACT.classification)
    && exact(value.status, 'blocked')
    && isObject(observed)
    && isObject(git)
    && /^[a-f0-9]{40}$/.test(git.head ?? '')
    && /^[a-f0-9]{40}$/.test(git.upstream ?? '')
    && assertBoolean(git.headUpstreamMatch, true)
    && assertBoolean(git.worktreeClean, false)
    && isObject(workflow)
    && assertBoolean(workflow.pushTrigger, true)
    && assertBoolean(workflow.pullRequestTrigger, true)
    && exact(workflow.permissions, 'contents-read')
    && assertBoolean(workflow.credentialsPersisted, false)
    && assertBoolean(workflow.exactHeadCheckout, true)
    && assertBoolean(workflow.concurrencyCancellation, true)
    && assertBoolean(workflow.trackedMutationRejected, true)
    && isObject(signingPolicy)
    && assertBoolean(signingPolicy.cryptographicSignature, true)
    && assertBoolean(signingPolicy.dco, true)
    && assertBoolean(signingPolicy.historyRewrite, false)
    && assertBoolean(signingPolicy.forcePush, false)
    && isObject(subjectAggregation)
    && isInteger(subjectAggregation.subjects) && exact(subjectAggregation.subjects, EXACT.subjectAggregation.subjects)
    && isInteger(subjectAggregation.subjectDefinitive) && exact(subjectAggregation.subjectDefinitive, EXACT.subjectAggregation.subjectDefinitive)
    && isInteger(subjectAggregation.definitiveMissing) && exact(subjectAggregation.definitiveMissing, EXACT.subjectAggregation.definitiveMissing)
    && isInteger(subjectAggregation.openRequired) && exact(subjectAggregation.openRequired, EXACT.subjectAggregation.openRequired)
    && isInteger(subjectAggregation.unclassified) && exact(subjectAggregation.unclassified, EXACT.subjectAggregation.unclassified)
    && isInteger(subjectAggregation.gapInstances) && exact(subjectAggregation.gapInstances, EXACT.subjectAggregation.gapInstances)
    && assertBoolean(subjectAggregation.autoPromotion, false)
    && isObject(distribution)
    && exact(distribution.status, 'not-established')
    && isInteger(distribution.ready) && exact(distribution.ready, EXACT.distribution.ready)
    && isInteger(distribution.blockerInstances) && exact(distribution.blockerInstances, EXACT.distribution.blockerInstances)
    && isObject(root)
    && exact(root.status, 'root-definitive-incomplete')
    && isInteger(root.missingArtifacts) && exact(root.missingArtifacts, EXACT.root.missingArtifacts)
    && exact(root.completionEffect, 'none')
    && isObject(dependencyGraph)
    && exact(dependencyGraph.recordedStatus, 'current')
    && isInteger(dependencyGraph.recordedRequiredOutputs) && exact(dependencyGraph.recordedRequiredOutputs, EXACT.dependencyGraph.recordedRequiredOutputs)
    && assertBoolean(dependencyGraph.currentProof, false)
    && isObject(ci)
    && ci.candidateCommit === null
    && ci.pushRun === null
    && ci.pullRequestRun === null
    && assertBoolean(ci.sameShaVerified, false)
    && isObject(summary)
    && isInteger(summary.prerequisites) && exact(summary.prerequisites, EXACT.summary.prerequisites)
    && isInteger(summary.satisfied) && exact(summary.satisfied, EXACT.summary.satisfied)
    && isInteger(summary.blocked) && exact(summary.blocked, EXACT.summary.blocked)
    && assertBoolean(summary.checkpointReady, false)
    && exact(summary.completionEffect, 'none')
    && Array.isArray(read(value, 'prerequisites'))
    && read(value, 'prerequisites').length === EXACT.summary.prerequisites
    && isObject(boundary)
    && assertBoolean(boundary.readOnly, true)
    && assertBoolean(boundary.autoCommit, false)
    && assertBoolean(boundary.autoPush, false)
    && assertBoolean(boundary.autoMerge, false)
    && assertBoolean(boundary.autoPromotion, false)
    && assertBoolean(boundary.dirtyTreeHasCiIdentity, false)
    && assertBoolean(boundary.headUpstreamMatchIsCheckpoint, false)
    && assertBoolean(boundary.sameShaRequired, true)
    && assertBoolean(boundary.pushAndPullRequestSuccessRequired, true)
    && assertBoolean(boundary.graphRerunRequired, true)
    && assertBoolean(boundary.externalPublication, false)
    && exact(boundary.completionEffect, 'none');
}

export function assertPortalCiCheckpointReadinessSnapshot(value) {
  if (!isPortalCiCheckpointReadinessSnapshot(value)) {
    throw new Error('portal ci checkpoint readiness response is invalid');
  }
  return value;
}

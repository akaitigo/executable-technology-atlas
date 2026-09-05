const EXACT = Object.freeze({
  schemaVersion: 1,
  id: 'portal-evidence-refresh-readiness',
  classification: 'dynamic-read-only-readiness',
  pipeline: {
    command: 'npm run dependency:reproduce',
    entrypoint: 'node scripts/refresh-portal-dependency-graph.mjs --record',
    stages: 8,
  },
  summary: {
    prerequisites: 6,
    wrappers: 8,
    inputs: 4,
    discoveredOutputs: 39,
  },
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

function isValidRefreshStatus(summary, status) {
  if (status === 'ready') {
    return summary.prerequisites === EXACT.summary.prerequisites
      && summary.currentWrappers === EXACT.summary.wrappers
      && summary.staleWrappers === 0
      && summary.inputsChangedSinceRun === 0
      && summary.missingDiscoveredOutputs === 0
      && summary.graphCurrent === true
      && summary.currentRerun === true;
  }
  return status === 'blocked' && summary.currentRerun === false;
}

export function isPortalEvidenceRefreshStatusSnapshot(value) {
  const pipeline = read(value, 'pipeline');
  const stages = read(pipeline, 'stages');
  const summary = read(value, 'summary');
  const boundary = read(value, 'boundary');
  return isObject(value)
    && exact(value.schemaVersion, EXACT.schemaVersion)
    && exact(value.id, EXACT.id)
    && exact(value.classification, EXACT.classification)
    && (value.status === 'blocked' || value.status === 'ready')
    && isObject(pipeline)
    && exact(pipeline.command, EXACT.pipeline.command)
    && exact(pipeline.entrypoint, EXACT.pipeline.entrypoint)
    && Array.isArray(stages)
    && stages.length === EXACT.pipeline.stages
    && isObject(summary)
    && isInteger(summary.prerequisites) && exact(summary.prerequisites, EXACT.summary.prerequisites)
    && isInteger(summary.wrappers) && exact(summary.wrappers, EXACT.summary.wrappers)
    && isInteger(summary.currentWrappers) && summary.currentWrappers >= 0 && summary.currentWrappers <= EXACT.summary.wrappers
    && isInteger(summary.staleWrappers) && summary.staleWrappers >= 0 && summary.staleWrappers <= EXACT.summary.wrappers
    && summary.currentWrappers + summary.staleWrappers === EXACT.summary.wrappers
    && isInteger(summary.inputs) && exact(summary.inputs, EXACT.summary.inputs)
    && isInteger(summary.inputsChangedSinceRun) && summary.inputsChangedSinceRun >= 0 && summary.inputsChangedSinceRun <= EXACT.summary.inputs
    && isInteger(summary.recordedOutputs) && summary.recordedOutputs >= 0 && summary.recordedOutputs <= EXACT.summary.discoveredOutputs
    && isInteger(summary.discoveredOutputs) && exact(summary.discoveredOutputs, EXACT.summary.discoveredOutputs)
    && isInteger(summary.missingDiscoveredOutputs) && summary.missingDiscoveredOutputs >= 0
    && summary.recordedOutputs + summary.missingDiscoveredOutputs === summary.discoveredOutputs
    && typeof summary.graphCurrent === 'boolean'
    && typeof summary.currentRerun === 'boolean'
    && exact(summary.completionEffect, 'none')
    && isValidRefreshStatus(summary, value.status)
    && Array.isArray(read(value, 'wrappers'))
    && read(value, 'wrappers').length === EXACT.summary.wrappers
    && Array.isArray(read(value, 'inputs'))
    && read(value, 'inputs').length === EXACT.summary.inputs
    && Array.isArray(read(value, 'missingOutputs'))
    && read(value, 'missingOutputs').length === summary.missingDiscoveredOutputs
    && isObject(boundary)
    && assertBoolean(boundary.readOnly, true)
    && assertBoolean(boundary.autoRun, false)
    && assertBoolean(boundary.digestOnlyClosure, false)
    && assertBoolean(boundary.wrapperRewriteIsRerun, false)
    && assertBoolean(boundary.stageSkipAllowed, false)
    && assertBoolean(boundary.runtimeSubstitution, false)
    && assertBoolean(boundary.recordedGraphStatusIsCurrentProof, false)
    && exact(boundary.subjectDefinitiveEffect, 'none')
    && exact(boundary.distributionEffect, 'none')
    && exact(boundary.rootDefinitiveEffect, 'none')
    && exact(boundary.completionEffect, 'none');
}

export function assertPortalEvidenceRefreshStatusSnapshot(value) {
  if (!isPortalEvidenceRefreshStatusSnapshot(value)) {
    throw new Error('portal evidence refresh status response is invalid');
  }
  return value;
}

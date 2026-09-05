const EXACT = Object.freeze({
  schemaVersion: 1,
  id: 'portal-integration-status',
  classification: 'dynamic-read-only-integration-observation',
  root: { required: 6, missing: 5, present: 1, cells: 970, verified: 201, gap: 478, notEvaluated: 291, matrixSatisfied: 3, matrixBlocked: 5, coreMatrixArtifactStatus: 'present' },
  distribution: { subjects: 97, ready: 0, definitive: 0, openGapInstances: 589, closedGapInstances: 0 },
  refresh: { wrappersMax: 8, inputsMax: 4 },
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

function isPortalEvidenceRefreshSummary(value) {
  return isObject(value)
    && (value.status === 'blocked' || value.status === 'ready')
    && isInteger(value.staleWrappers) && value.staleWrappers >= 0 && value.staleWrappers <= EXACT.refresh.wrappersMax
    && isInteger(value.inputsChangedSinceRun) && value.inputsChangedSinceRun >= 0 && value.inputsChangedSinceRun <= EXACT.refresh.inputsMax
    && isInteger(value.missingOutputs) && value.missingOutputs >= 0
    && typeof value.currentRerun === 'boolean'
    && (
      value.status === 'blocked'
        ? value.currentRerun === false
        : value.currentRerun === true
          && value.staleWrappers === 0
          && value.inputsChangedSinceRun === 0
          && value.missingOutputs === 0
    );
}

export function isPortalIntegrationStatusSnapshot(value) {
  const root = read(value, 'root');
  const distribution = read(value, 'distribution');
  const evidenceRefresh = read(value, 'evidenceRefresh');
  const boundary = read(value, 'boundary');
  return isObject(value)
    && exact(value.schemaVersion, EXACT.schemaVersion)
    && exact(value.id, EXACT.id)
    && exact(value.classification, EXACT.classification)
    && exact(value.status, 'blocked')
    && isObject(root)
    && exact(root.definitiveStatus, 'root-definitive-incomplete')
    && exact(root.coreMatrixArtifactStatus, EXACT.root.coreMatrixArtifactStatus)
    && isInteger(root.artifactsRequired) && exact(root.artifactsRequired, EXACT.root.required)
    && isInteger(root.artifactsMissing) && exact(root.artifactsMissing, EXACT.root.missing)
    && isInteger(root.artifactsPresent) && exact(root.artifactsPresent, EXACT.root.present)
    && isInteger(root.matrixPrerequisites) && exact(root.matrixPrerequisites, 8)
    && isInteger(root.matrixSatisfied) && exact(root.matrixSatisfied, EXACT.root.matrixSatisfied)
    && isInteger(root.matrixBlocked) && exact(root.matrixBlocked, EXACT.root.matrixBlocked)
    && isInteger(root.matrixCells) && exact(root.matrixCells, EXACT.root.cells)
    && isInteger(root.matrixVerified) && exact(root.matrixVerified, EXACT.root.verified)
    && isInteger(root.matrixGap) && exact(root.matrixGap, EXACT.root.gap)
    && isInteger(root.matrixNotEvaluated) && exact(root.matrixNotEvaluated, EXACT.root.notEvaluated)
    && isObject(distribution)
    && exact(distribution.status, 'not-established')
    && isInteger(distribution.subjects) && exact(distribution.subjects, EXACT.distribution.subjects)
    && isInteger(distribution.ready) && exact(distribution.ready, EXACT.distribution.ready)
    && isInteger(distribution.subjectDefinitive) && exact(distribution.subjectDefinitive, EXACT.distribution.definitive)
    && isInteger(distribution.openGapInstances) && exact(distribution.openGapInstances, EXACT.distribution.openGapInstances)
    && isInteger(distribution.closedGapInstances) && exact(distribution.closedGapInstances, EXACT.distribution.closedGapInstances)
    && isPortalEvidenceRefreshSummary(evidenceRefresh)
    && isObject(boundary)
    && assertBoolean(boundary.readOnly, true)
    && assertBoolean(boundary.autoRun, false)
    && assertBoolean(boundary.autoPromotion, false)
    && assertBoolean(boundary.portalIsSubject, false)
    && assertBoolean(boundary.rawCountsAreCompletion, false)
    && assertBoolean(boundary.coreArtifactsAutoCreated, false)
    && exact(boundary.boundedCertificateEffect, 'none')
    && exact(boundary.subjectDefinitiveEffect, 'none')
    && exact(boundary.distributionEffect, 'none')
    && exact(boundary.rootDefinitiveEffect, 'none')
    && exact(boundary.completionEffect, 'none');
}

export function assertPortalIntegrationStatusSnapshot(value) {
  if (!isPortalIntegrationStatusSnapshot(value)) {
    throw new Error('portal integration status response is invalid');
  }
  return value;
}

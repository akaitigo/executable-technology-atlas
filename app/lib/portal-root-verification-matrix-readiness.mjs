const EXACT = Object.freeze({
  schemaVersion: 1,
  id: 'portal-root-verification-matrix-readiness',
  classification: 'portal-infrastructure-readiness-only',
  coreContract: { artifactPath: 'verification.matrix.yaml', observedStatus: 'present' },
  summary: { prerequisites: 8, satisfied: 3, blocked: 5, coreVerificationMatrixArtifactsPresent: 1, completionEffect: 'none' },
  portalDistributionMatrix: { subjects: 97, classes: 10, cells: 970, gap: 478, notEvaluated: 291, coreSubjectArtifactStatus: 'present', runtimeSubstitution: false, completionEffect: 'none' },
  surfaceInventory: { status: 'blocked', satisfied: 2, blocked: 6, coreArtifactPresent: 0, authorityDerivedDenominatorAvailable: false },
  declaration: { status: 'blocked', present: 0, completionEffect: 'none' },
  dependencyGraph: { requiredOutputDenominator: 11 },
  boundary: {
    readOnly: true,
    autoCreate: false,
    autoPromotion: false,
    portalIsSubject: false,
    portalDistributionMatrixIsCoreSubjectArtifact: false,
    authorityAtomicBehaviorDenominatorAvailable: false,
    runtimeSubstitution: false,
    recordedGraphStatusIsCurrentProof: false,
    digestOnlyClosure: false,
    rootDefinitiveStatus: 'root-definitive-incomplete',
    distributionStatus: 'not-established',
    completionEffect: 'none',
    coreSubjectArtifact: { path: 'verification.matrix.yaml', status: 'present', effect: 'none' },
  },
});

const REQUIRED_GRAPH_OUTPUTS = Object.freeze([
  'evidence/portal-distribution-gap-index.json',
  'evidence/portal-distribution-input-bindings.json',
  'evidence/portal-distribution-readiness.json',
  'evidence/portal-distribution-verification-matrix.json',
  'evidence/portal-import-lifecycle-visibility.json',
  'evidence/portal-root-artifact-gap-index.json',
  'evidence/portal-root-definitive-certificate-readiness.json',
  'evidence/portal-root-definitive-declaration-readiness.json',
  'evidence/portal-root-depth-parity-readiness.json',
  'evidence/portal-root-migration-readiness.json',
  'evidence/portal-root-surface-inventory-readiness.json',
]);

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

export function isPortalRootVerificationMatrixReadinessSnapshot(value) {
  const coreContract = read(value, 'coreContract');
  const observed = read(value, 'observed');
  const portalDistributionMatrix = read(observed, 'portalDistributionMatrix');
  const surfaceInventory = read(observed, 'surfaceInventory');
  const declaration = read(observed, 'declaration');
  const dependencyGraph = read(observed, 'dependencyGraph');
  const summary = read(value, 'summary');
  const boundary = read(value, 'boundary');
  const coreSubjectArtifact = read(boundary, 'coreSubjectArtifact');
  const missingRequiredOutputs = read(dependencyGraph, 'missingRequiredOutputs');
  return isObject(value)
    && exact(value.schemaVersion, EXACT.schemaVersion)
    && exact(value.id, EXACT.id)
    && exact(value.status, 'blocked')
    && exact(value.classification, EXACT.classification)
    && isObject(coreContract)
    && exact(coreContract.artifactPath, EXACT.coreContract.artifactPath)
    && exact(coreContract.observedStatus, EXACT.coreContract.observedStatus)
    && isObject(observed)
    && exact(observed.portalIsSubject, false)
    && isObject(portalDistributionMatrix)
    && exact(portalDistributionMatrix.status, 'incomplete')
    && isInteger(portalDistributionMatrix.subjects) && exact(portalDistributionMatrix.subjects, EXACT.portalDistributionMatrix.subjects)
    && isInteger(portalDistributionMatrix.classes) && exact(portalDistributionMatrix.classes, EXACT.portalDistributionMatrix.classes)
    && isInteger(portalDistributionMatrix.cells) && exact(portalDistributionMatrix.cells, EXACT.portalDistributionMatrix.cells)
    && isInteger(portalDistributionMatrix.gap) && exact(portalDistributionMatrix.gap, EXACT.portalDistributionMatrix.gap)
    && isInteger(portalDistributionMatrix.notEvaluated) && exact(portalDistributionMatrix.notEvaluated, EXACT.portalDistributionMatrix.notEvaluated)
    && exact(portalDistributionMatrix.coreSubjectArtifactStatus, EXACT.portalDistributionMatrix.coreSubjectArtifactStatus)
    && assertBoolean(portalDistributionMatrix.runtimeSubstitution, EXACT.portalDistributionMatrix.runtimeSubstitution)
    && exact(portalDistributionMatrix.completionEffect, EXACT.portalDistributionMatrix.completionEffect)
    && isObject(surfaceInventory)
    && exact(surfaceInventory.status, EXACT.surfaceInventory.status)
    && isInteger(surfaceInventory.satisfied) && exact(surfaceInventory.satisfied, EXACT.surfaceInventory.satisfied)
    && isInteger(surfaceInventory.blocked) && exact(surfaceInventory.blocked, EXACT.surfaceInventory.blocked)
    && isInteger(surfaceInventory.coreArtifactPresent) && exact(surfaceInventory.coreArtifactPresent, EXACT.surfaceInventory.coreArtifactPresent)
    && assertBoolean(surfaceInventory.authorityDerivedDenominatorAvailable, EXACT.surfaceInventory.authorityDerivedDenominatorAvailable)
    && isObject(declaration)
    && exact(declaration.status, EXACT.declaration.status)
    && isInteger(declaration.present) && exact(declaration.present, EXACT.declaration.present)
    && exact(declaration.completionEffect, EXACT.declaration.completionEffect)
    && isObject(dependencyGraph)
    && typeof dependencyGraph.recordedStatus === 'string'
    && isInteger(dependencyGraph.requiredOutputDenominator) && exact(dependencyGraph.requiredOutputDenominator, EXACT.dependencyGraph.requiredOutputDenominator)
    && isInteger(dependencyGraph.boundRequiredOutputs) && dependencyGraph.boundRequiredOutputs <= EXACT.dependencyGraph.requiredOutputDenominator
    && Array.isArray(missingRequiredOutputs)
    && missingRequiredOutputs.length === EXACT.dependencyGraph.requiredOutputDenominator - dependencyGraph.boundRequiredOutputs
    && new Set(missingRequiredOutputs).size === missingRequiredOutputs.length
    && missingRequiredOutputs.every((item) => REQUIRED_GRAPH_OUTPUTS.includes(item))
    && isObject(summary)
    && isInteger(summary.prerequisites) && exact(summary.prerequisites, EXACT.summary.prerequisites)
    && isInteger(summary.satisfied) && exact(summary.satisfied, EXACT.summary.satisfied)
    && isInteger(summary.blocked) && exact(summary.blocked, EXACT.summary.blocked)
    && isInteger(summary.coreVerificationMatrixArtifactsPresent) && exact(summary.coreVerificationMatrixArtifactsPresent, EXACT.summary.coreVerificationMatrixArtifactsPresent)
    && exact(summary.completionEffect, EXACT.summary.completionEffect)
    && isObject(boundary)
    && assertBoolean(boundary.readOnly, EXACT.boundary.readOnly)
    && assertBoolean(boundary.autoCreate, EXACT.boundary.autoCreate)
    && assertBoolean(boundary.autoPromotion, EXACT.boundary.autoPromotion)
    && assertBoolean(boundary.portalIsSubject, EXACT.boundary.portalIsSubject)
    && assertBoolean(boundary.portalDistributionMatrixIsCoreSubjectArtifact, EXACT.boundary.portalDistributionMatrixIsCoreSubjectArtifact)
    && assertBoolean(boundary.authorityAtomicBehaviorDenominatorAvailable, EXACT.boundary.authorityAtomicBehaviorDenominatorAvailable)
    && assertBoolean(boundary.runtimeSubstitution, EXACT.boundary.runtimeSubstitution)
    && assertBoolean(boundary.recordedGraphStatusIsCurrentProof, EXACT.boundary.recordedGraphStatusIsCurrentProof)
    && assertBoolean(boundary.digestOnlyClosure, EXACT.boundary.digestOnlyClosure)
    && exact(boundary.rootDefinitiveStatus, EXACT.boundary.rootDefinitiveStatus)
    && exact(boundary.distributionStatus, EXACT.boundary.distributionStatus)
    && exact(boundary.completionEffect, EXACT.boundary.completionEffect)
    && isObject(coreSubjectArtifact)
    && exact(coreSubjectArtifact.path, EXACT.boundary.coreSubjectArtifact.path)
    && exact(coreSubjectArtifact.status, EXACT.boundary.coreSubjectArtifact.status)
    && exact(coreSubjectArtifact.effect, EXACT.boundary.coreSubjectArtifact.effect);
}

export function assertPortalRootVerificationMatrixReadinessSnapshot(value) {
  if (!isPortalRootVerificationMatrixReadinessSnapshot(value)) {
    throw new Error('portal root verification matrix readiness response is invalid');
  }
  return value;
}

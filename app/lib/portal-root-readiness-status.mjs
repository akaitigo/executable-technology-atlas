const EXACT = Object.freeze({
  schemaVersion: 1,
  id: 'portal-root-readiness-status',
  classification: 'dynamic-read-only-root-artifact-observation',
  root: { requiredArtifacts: 6, missingArtifacts: 5, presentArtifacts: 1, distributionStatus: 'not-established' },
  artifacts: [
    ['definitive.yaml', 9, 1, 8],
    ['surface.inventory.yaml', 8, 2, 6],
    ['verification.matrix.yaml', 8, 3, 5, 1, 'present'],
    ['depth.parity.yaml', 6, 1, 5],
    ['migrations/definitive-v2.yaml', 9, 2, 7],
    ['evidence/definitive-certificate.json', 10, 1, 9],
  ],
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

export function isPortalRootReadinessStatusSnapshot(value) {
  const root = read(value, 'root');
  const artifacts = read(value, 'artifacts');
  const boundary = read(value, 'boundary');
  return isObject(value)
    && exact(value.schemaVersion, EXACT.schemaVersion)
    && exact(value.id, EXACT.id)
    && exact(value.classification, EXACT.classification)
    && exact(value.status, 'blocked')
    && isObject(root)
    && exact(root.definitiveStatus, 'root-definitive-incomplete')
    && isInteger(root.requiredArtifacts) && exact(root.requiredArtifacts, EXACT.root.requiredArtifacts)
    && isInteger(root.missingArtifacts) && exact(root.missingArtifacts, EXACT.root.missingArtifacts)
    && isInteger(root.presentArtifacts) && exact(root.presentArtifacts, EXACT.root.presentArtifacts)
    && exact(root.distributionStatus, EXACT.root.distributionStatus)
    && Array.isArray(artifacts)
    && artifacts.length === EXACT.artifacts.length
    && artifacts.every((artifact, index) => {
      const [artifactPath, prerequisites, satisfied, blocked, coreArtifactPresent = 0, observedStatus = 'missing'] = EXACT.artifacts[index];
      return isObject(artifact)
        && exact(artifact.artifactPath, artifactPath)
        && exact(artifact.status, 'blocked')
        && isInteger(artifact.prerequisites) && exact(artifact.prerequisites, prerequisites)
        && isInteger(artifact.satisfied) && exact(artifact.satisfied, satisfied)
        && isInteger(artifact.blocked) && exact(artifact.blocked, blocked)
        && isInteger(artifact.coreArtifactPresent) && exact(artifact.coreArtifactPresent, coreArtifactPresent)
        && exact(artifact.observedStatus, observedStatus)
        && exact(artifact.completionEffect, 'none')
        && assertBoolean(artifact.autoCreate, false)
        && assertBoolean(artifact.autoPromotion, false);
    })
    && isObject(boundary)
    && assertBoolean(boundary.readOnly, true)
    && assertBoolean(boundary.portalIsSubject, false)
    && assertBoolean(boundary.autoCreate, false)
    && assertBoolean(boundary.autoPromotion, false)
    && assertBoolean(boundary.digestOnlyClosure, false)
    && exact(boundary.completionEffect, 'none');
}

export function assertPortalRootReadinessStatusSnapshot(value) {
  if (!isPortalRootReadinessStatusSnapshot(value)) {
    throw new Error('portal root readiness status response is invalid');
  }
  return value;
}

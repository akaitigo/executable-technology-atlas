import Ajv2020 from 'ajv/dist/2020.js';
import addFormats from 'ajv-formats';
import { readFile } from 'node:fs/promises';
import path from 'node:path';
import { canonicalJson, sha256 } from './crypto.mjs';
import { loadPortalRootVerificationMatrix, validatePortalRootVerificationMatrix } from './portal-root-verification-matrix.mjs';

const INPUT_PATHS = {
  rootGapIndex: 'evidence/portal-root-artifact-gap-index.json',
  distributionMatrix: 'evidence/portal-distribution-verification-matrix.json',
  surfaceReadiness: 'evidence/portal-root-surface-inventory-readiness.json',
  declarationReadiness: 'evidence/portal-root-definitive-declaration-readiness.json',
  dependencyGraph: 'evidence/dependency-graph.json',
  matrixArtifact: 'verification.matrix.yaml',
};

const REQUIRED_GRAPH_OUTPUTS = [
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
];

export async function loadPortalRootVerificationMatrixReadinessInputs(root = process.cwd()) {
  const entries = await Promise.all(
    Object.entries(INPUT_PATHS).map(async ([key, relativePath]) => {
      if (key === 'matrixArtifact') {
        const loaded = await loadPortalRootVerificationMatrix(root);
        return [key, { path: relativePath, bytes: loaded.bytes, document: loaded.document }];
      }
      const bytes = await readFile(path.join(root, relativePath));
      return [key, { path: relativePath, bytes, document: JSON.parse(bytes) }];
    }),
  );
  const schema = JSON.parse(await readFile(path.join(root, 'contracts/schemas/portal-root-verification-matrix-readiness.schema.json'), 'utf8'));
  const matrixArtifactValidation = await validatePortalRootVerificationMatrix(root, Object.fromEntries(entries).matrixArtifact.document);
  return { ...Object.fromEntries(entries), matrixArtifactValidation, schema };
}

export function buildPortalRootVerificationMatrixReadiness(inputs) {
  const gap = inputs.rootGapIndex.document.gaps.find((item) => item.artifactPath === 'verification.matrix.yaml');
  if (!gap) throw new Error('verification.matrix.yamlのroot Gapがありません');
  const matrix = inputs.distributionMatrix.document;
  const surface = inputs.surfaceReadiness.document;
  const declaration = inputs.declarationReadiness.document;
  const graphOutputs = new Set(inputs.dependencyGraph.document.required_outputs ?? []);
  const missingGraphOutputs = REQUIRED_GRAPH_OUTPUTS.filter((item) => !graphOutputs.has(item));
  const matrixArtifactSatisfied = gap.status === 'present' && inputs.matrixArtifactValidation.ok;
  const prerequisites = [
    { id: 'fixed-core-verification-matrix-contract', state: 'satisfied', evidence: ['evidence/portal-root-artifact-gap-index.json'], gapIds: [] },
    { id: 'portal-distribution-matrix-denominator-preserved', state: 'satisfied', evidence: ['evidence/portal-distribution-verification-matrix.json'], gapIds: [] },
    { id: 'portal-root-verification-matrix-artifact', state: matrixArtifactSatisfied ? 'satisfied' : 'blocked', evidence: ['verification.matrix.yaml'], gapIds: matrixArtifactSatisfied ? [] : ['portal-root-verification-matrix-invalid'] },
    { id: 'portal-subject-authority', state: 'blocked', evidence: ['evidence/portal-root-artifact-gap-index.json'], gapIds: ['portal-is-not-a-core-subject'] },
    { id: 'authority-atomic-behavior-denominator', state: 'blocked', evidence: ['evidence/portal-root-surface-inventory-readiness.json'], gapIds: ['authority-atomic-behavior-denominator-missing'] },
    { id: 'core-surface-inventory', state: 'blocked', evidence: ['evidence/portal-root-surface-inventory-readiness.json'], gapIds: ['surface.inventory.yaml-missing'] },
    { id: 'authority-derived-runtime-matrix-coverage', state: 'blocked', evidence: ['evidence/portal-distribution-verification-matrix.json'], gapIds: ['runtime-cells-not-evaluated'] },
    { id: 'current-evidence-dependency-rerun', state: 'blocked', evidence: ['evidence/dependency-graph.json'], gapIds: ['current-portal-derived-outputs-not-bound'] },
  ];
  return {
    schemaVersion: 1,
    id: 'portal-root-verification-matrix-readiness',
    status: 'blocked',
    classification: 'portal-infrastructure-readiness-only',
    source: Object.fromEntries(Object.entries(INPUT_PATHS).map(([key, relativePath]) => [key, { path: relativePath, digest: sha256(inputs[key].bytes) }])),
    coreContract: {
      commit: gap.coreContract.commit,
      artifactPath: gap.artifactPath,
      schemaPath: gap.coreContract.schemaPath,
      schemaDigest: gap.coreContract.schemaDigest,
      validatorPath: gap.coreContract.validatorPath,
      validatorDigest: gap.coreContract.validatorDigest,
      observedStatus: gap.status,
    },
    observed: {
      portalIsSubject: inputs.rootGapIndex.document.boundary.portalIsSubject,
      portalDistributionMatrix: {
        status: matrix.status,
        subjects: matrix.summary.subjects,
        classes: matrix.summary.classes,
        cells: matrix.summary.cells,
        verified: matrix.summary.verified,
        gap: matrix.summary.gap,
        notEvaluated: matrix.summary.notEvaluated,
        coreSubjectArtifactStatus: matrix.boundary.coreSubjectArtifact.status,
        runtimeSubstitution: matrix.boundary.runtimeSubstitution,
        completionEffect: matrix.boundary.completionEffect,
      },
      surfaceInventory: {
        status: surface.status,
        satisfied: surface.summary.satisfied,
        blocked: surface.summary.blocked,
        coreArtifactPresent: surface.summary.coreSurfaceInventoryArtifactsPresent,
        authorityDerivedDenominatorAvailable: surface.boundary.authorityDerivedDenominatorAvailable,
      },
      declaration: {
        status: declaration.status,
        present: declaration.summary.definitiveDeclarationsPresent,
        completionEffect: declaration.summary.completionEffect,
      },
      dependencyGraph: {
        recordedStatus: inputs.dependencyGraph.document.status,
        requiredOutputDenominator: REQUIRED_GRAPH_OUTPUTS.length,
        boundRequiredOutputs: REQUIRED_GRAPH_OUTPUTS.length - missingGraphOutputs.length,
        missingRequiredOutputs: missingGraphOutputs,
      },
    },
    summary: {
      prerequisites: prerequisites.length,
      satisfied: prerequisites.filter((item) => item.state === 'satisfied').length,
      blocked: prerequisites.filter((item) => item.state === 'blocked').length,
      coreVerificationMatrixArtifactsPresent: gap.status === 'present' ? 1 : 0,
      completionEffect: 'none',
    },
    prerequisites,
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
      coreSubjectArtifact: { path: 'verification.matrix.yaml', status: gap.status, effect: 'none' },
      rootDefinitiveStatus: 'root-definitive-incomplete',
      distributionStatus: 'not-established',
      completionEffect: 'none',
    },
  };
}

export async function validatePortalRootVerificationMatrixReadiness(root, document, schema) {
  const errors = [];
  const ajv = new Ajv2020({ allErrors: true, strict: true });
  addFormats(ajv);
  const validate = ajv.compile(schema);
  if (!validate(document)) errors.push('schema-invalid');
  const expected = buildPortalRootVerificationMatrixReadiness(await loadPortalRootVerificationMatrixReadinessInputs(root));
  const missingRequiredOutputs = document.observed?.dependencyGraph?.missingRequiredOutputs;
  if (canonicalJson(document.prerequisites?.map((item) => ({ id: item.id, state: item.state }))) !== canonicalJson(expected.prerequisites.map((item) => ({ id: item.id, state: item.state })))) errors.push('matrix-readiness-prerequisite-denominator-reduced-or-reordered');
  if (document.observed?.portalIsSubject !== false || document.boundary?.portalIsSubject !== false) errors.push('portal-root-matrix-subjectized');
  if (document.coreContract?.observedStatus !== expected.coreContract.observedStatus || document.boundary?.coreSubjectArtifact?.status !== expected.boundary.coreSubjectArtifact.status) errors.push('core-verification-matrix-spoofed');
  if (document.observed?.portalDistributionMatrix?.subjects !== 97 || document.observed?.portalDistributionMatrix?.classes !== 10 || document.observed?.portalDistributionMatrix?.cells !== 970) errors.push('portal-distribution-matrix-denominator-reduced');
  if (document.boundary?.portalDistributionMatrixIsCoreSubjectArtifact !== false) errors.push('portal-distribution-matrix-promoted-to-core-artifact');
  if (document.boundary?.authorityAtomicBehaviorDenominatorAvailable !== false) errors.push('authority-atomic-behavior-denominator-spoofed');
  if (document.boundary?.runtimeSubstitution !== false || document.observed?.portalDistributionMatrix?.runtimeSubstitution !== false || document.observed?.portalDistributionMatrix?.notEvaluated !== 291) errors.push('runtime-matrix-substituted-or-hidden');
  if (document.boundary?.recordedGraphStatusIsCurrentProof !== false || document.observed?.dependencyGraph?.requiredOutputDenominator !== REQUIRED_GRAPH_OUTPUTS.length || !Number.isInteger(document.observed?.dependencyGraph?.boundRequiredOutputs) || document.observed.dependencyGraph.boundRequiredOutputs < 0 || document.observed.dependencyGraph.boundRequiredOutputs > REQUIRED_GRAPH_OUTPUTS.length || !Array.isArray(missingRequiredOutputs) || missingRequiredOutputs.length !== REQUIRED_GRAPH_OUTPUTS.length - document.observed.dependencyGraph.boundRequiredOutputs || new Set(missingRequiredOutputs).size !== missingRequiredOutputs.length || missingRequiredOutputs.some((item) => !REQUIRED_GRAPH_OUTPUTS.includes(item))) errors.push('recorded-graph-status-promoted');
  if (document.status !== 'blocked' || document.summary?.prerequisites !== expected.summary.prerequisites || document.summary?.satisfied !== expected.summary.satisfied || document.summary?.blocked !== expected.summary.blocked || document.summary?.coreVerificationMatrixArtifactsPresent !== expected.summary.coreVerificationMatrixArtifactsPresent || document.boundary?.autoCreate !== false || document.boundary?.autoPromotion !== false || document.boundary?.completionEffect !== 'none') errors.push('verification-matrix-readiness-promoted');
  expected.source.dependencyGraph = structuredClone(document.source?.dependencyGraph ?? expected.source.dependencyGraph);
  expected.observed.dependencyGraph = structuredClone(document.observed?.dependencyGraph ?? expected.observed.dependencyGraph);
  if (canonicalJson(document) !== canonicalJson(expected)) errors.push('verification-matrix-readiness-source-drift');
  return { ok: errors.length === 0, errors: [...new Set(errors)], summary: document.summary ?? {}, digest: sha256(Buffer.from(`${JSON.stringify(document, null, 2)}\n`)) };
}

export function applyPortalRootVerificationMatrixReadinessNegative(document, testCase) {
  const mutated = structuredClone(document);
  if (testCase.mutation === 'remove-prerequisite') mutated.prerequisites.shift();
  else if (testCase.mutation === 'toggle-artifact-status' || testCase.mutation === 'pretend-artifact-present') {
    mutated.coreContract.observedStatus = mutated.coreContract.observedStatus === 'present' ? 'missing' : 'present';
    mutated.boundary.coreSubjectArtifact.status = mutated.boundary.coreSubjectArtifact.status === 'present' ? 'missing' : 'present';
    mutated.summary.coreVerificationMatrixArtifactsPresent = mutated.summary.coreVerificationMatrixArtifactsPresent === 1 ? 0 : 1;
  } else if (testCase.mutation === 'reduce-matrix-denominator') mutated.observed.portalDistributionMatrix.cells = 969;
  else if (testCase.mutation === 'promote-portal-matrix') mutated.boundary.portalDistributionMatrixIsCoreSubjectArtifact = true;
  else if (testCase.mutation === 'spoof-authority-atomic') mutated.boundary.authorityAtomicBehaviorDenominatorAvailable = true;
  else if (testCase.mutation === 'substitute-runtime') {
    mutated.boundary.runtimeSubstitution = true;
    mutated.observed.portalDistributionMatrix.runtimeSubstitution = true;
    mutated.observed.portalDistributionMatrix.notEvaluated = 0;
  } else if (testCase.mutation === 'promote-recorded-graph') {
    mutated.boundary.recordedGraphStatusIsCurrentProof = true;
    mutated.observed.dependencyGraph.missingRequiredOutputs = [];
    mutated.observed.dependencyGraph.boundRequiredOutputs = 11;
  } else if (testCase.mutation === 'subjectize-portal') {
    mutated.observed.portalIsSubject = true;
    mutated.boundary.portalIsSubject = true;
  } else if (testCase.mutation === 'promote-readiness') {
    mutated.status = 'ready';
    mutated.summary.satisfied = 8;
    mutated.summary.blocked = 0;
    mutated.boundary.autoCreate = true;
    mutated.boundary.completionEffect = 'complete';
  } else throw new Error(`未知のVerification Matrix readiness負例です: ${testCase.mutation}`);
  return mutated;
}

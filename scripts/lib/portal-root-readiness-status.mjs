import Ajv2020 from 'ajv/dist/2020.js';
import addFormats from 'ajv-formats';
import { readFile } from 'node:fs/promises';
import path from 'node:path';
import { canonicalJson, sha256 } from './crypto.mjs';
import { validatePortalRootArtifactGapIndex } from './portal-root-artifact-gap-index.mjs';
import { validatePortalRootDepthParityReadiness } from './portal-root-depth-parity-readiness.mjs';
import { validatePortalRootMigrationReadiness } from './portal-root-migration-readiness.mjs';
import { validatePortalRootCertificateReadiness } from './portal-root-definitive-certificate-readiness.mjs';
import { validatePortalRootDefinitiveDeclarationReadiness } from './portal-root-definitive-declaration-readiness.mjs';
import { validatePortalRootSurfaceInventoryReadiness } from './portal-root-surface-inventory-readiness.mjs';
import { validatePortalRootVerificationMatrixReadiness } from './portal-root-verification-matrix-readiness.mjs';

const INPUTS = {
  gaps: { path: 'evidence/portal-root-artifact-gap-index.json', schemaPath: 'contracts/schemas/portal-root-artifact-gap-index.schema.json' },
  depthParity: { path: 'evidence/portal-root-depth-parity-readiness.json', schemaPath: 'contracts/schemas/portal-root-depth-parity-readiness.schema.json' },
  migration: { path: 'evidence/portal-root-migration-readiness.json', schemaPath: 'contracts/schemas/portal-root-migration-readiness.schema.json' },
  certificate: { path: 'evidence/portal-root-definitive-certificate-readiness.json', schemaPath: 'contracts/schemas/portal-root-definitive-certificate-readiness.schema.json' },
  declaration: { path: 'evidence/portal-root-definitive-declaration-readiness.json', schemaPath: 'contracts/schemas/portal-root-definitive-declaration-readiness.schema.json' },
  surfaceInventory: { path: 'evidence/portal-root-surface-inventory-readiness.json', schemaPath: 'contracts/schemas/portal-root-surface-inventory-readiness.schema.json' },
  verificationMatrix: { path: 'evidence/portal-root-verification-matrix-readiness.json', schemaPath: 'contracts/schemas/portal-root-verification-matrix-readiness.schema.json' }
};

const ARTIFACT_ORDER = Object.freeze([
  ['definitive.yaml', 'declaration'],
  ['surface.inventory.yaml', 'surfaceInventory'],
  ['verification.matrix.yaml', 'verificationMatrix'],
  ['depth.parity.yaml', 'depthParity'],
  ['migrations/definitive-v2.yaml', 'migration'],
  ['evidence/definitive-certificate.json', 'certificate']
]);

const VALIDATORS = {
  gaps: validatePortalRootArtifactGapIndex,
  depthParity: validatePortalRootDepthParityReadiness,
  migration: validatePortalRootMigrationReadiness,
  certificate: validatePortalRootCertificateReadiness,
  declaration: validatePortalRootDefinitiveDeclarationReadiness,
  surfaceInventory: validatePortalRootSurfaceInventoryReadiness,
  verificationMatrix: validatePortalRootVerificationMatrixReadiness
};

export async function loadPortalRootReadinessStatusInputs(root = process.cwd()) {
  const entries = await Promise.all(
    Object.entries(INPUTS).map(async ([id, input]) => {
      const [bytes, schemaBytes] = await Promise.all([
        readFile(path.join(root, input.path)),
        readFile(path.join(root, input.schemaPath)),
      ]);
      return [id, { ...input, bytes, document: JSON.parse(bytes), schema: JSON.parse(schemaBytes) }];
    }),
  );
  const schemaBytes = await readFile(path.join(root, 'contracts/schemas/portal-root-readiness-status.schema.json'));
  return { ...Object.fromEntries(entries), schema: JSON.parse(schemaBytes) };
}

export async function buildPortalRootReadinessStatus(root, inputs) {
  const validations = Object.fromEntries(
    await Promise.all(
      Object.keys(INPUTS).map(async (key) => [key, await VALIDATORS[key](root, inputs[key].document, inputs[key].schema)]),
    ),
  );
  const gaps = inputs.gaps.document;
  const artifacts = ARTIFACT_ORDER.map(([artifactPath, key]) => {
    const document = inputs[key].document;
    return {
      artifactPath,
      readinessId: document.id,
      status: document.status,
      prerequisites: document.summary.prerequisites,
      satisfied: document.summary.satisfied,
      blocked: document.summary.blocked,
      coreArtifactPresent: document.summary.coreDepthParityArtifactsPresent
        ?? document.summary.migrationArtifactsPresent
        ?? document.summary.definitiveCertificatesPresent
        ?? document.summary.definitiveDeclarationsPresent
        ?? document.summary.coreSurfaceInventoryArtifactsPresent
        ?? document.summary.coreVerificationMatrixArtifactsPresent
        ?? 0,
      observedStatus: document.coreContract.observedStatus,
      completionEffect: document.boundary.completionEffect,
      autoCreate: document.boundary.autoCreate ?? document.boundary.autoIssue ?? false,
      autoPromotion: document.boundary.autoPromotion,
    };
  });
  const sources = Object.fromEntries(
    Object.entries(INPUTS).map(([id, input]) => [id, { path: input.path, digest: sha256(inputs[id].bytes), valid: validations[id].ok }]),
  );
  return {
    schemaVersion: 1,
    id: 'portal-root-readiness-status',
    status: 'blocked',
    classification: 'dynamic-read-only-root-artifact-observation',
    sources,
    root: {
      definitiveStatus: gaps.boundary.rootDefinitiveStatus,
      requiredArtifacts: gaps.summary.requiredArtifacts,
      missingArtifacts: gaps.summary.missingArtifacts,
      presentArtifacts: gaps.summary.presentArtifacts,
      distributionStatus: gaps.boundary.distributionStatus,
    },
    artifacts,
    boundary: {
      readOnly: true,
      portalIsSubject: false,
      autoCreate: false,
      autoPromotion: false,
      digestOnlyClosure: false,
      completionEffect: 'none',
    },
  };
}

export async function evaluatePortalRootReadinessStatus(root = process.cwd()) {
  const inputs = await loadPortalRootReadinessStatusInputs(root);
  const report = await buildPortalRootReadinessStatus(root, inputs);
  const errors = [];
  const ajv = new Ajv2020({ allErrors: true, strict: true });
  addFormats(ajv);
  const validate = ajv.compile(inputs.schema);
  if (!validate(report)) errors.push('schema-invalid');
  if (Object.values(report.sources).some((item) => item.valid !== true)) errors.push('root-readiness-source-invalid');
  return { ok: errors.length === 0, errors, report, schema: inputs.schema };
}

export function validatePortalRootReadinessStatus(document, schema, expected) {
  const errors = [];
  const ajv = new Ajv2020({ allErrors: true, strict: true });
  addFormats(ajv);
  const validate = ajv.compile(schema);
  if (!validate(document)) errors.push('schema-invalid');
  if (document.root?.definitiveStatus !== 'root-definitive-incomplete' || document.root?.requiredArtifacts !== 6 || document.root?.missingArtifacts !== 5 || document.root?.presentArtifacts !== 1 || document.root?.distributionStatus !== 'not-established') errors.push('root-readiness-gap-hidden');
  if (canonicalJson(document.artifacts?.map((item) => item.artifactPath)) !== canonicalJson(ARTIFACT_ORDER.map(([artifactPath]) => artifactPath))) errors.push('root-readiness-denominator-reduced-or-reordered');
  const expectedCounts = new Map([
    ['definitive.yaml', { prerequisites: 9, satisfied: 1, blocked: 8 }],
    ['surface.inventory.yaml', { prerequisites: 8, satisfied: 2, blocked: 6 }],
    ['verification.matrix.yaml', { prerequisites: 8, satisfied: 3, blocked: 5, observedStatus: 'present', coreArtifactPresent: 1 }],
    ['depth.parity.yaml', { prerequisites: 6, satisfied: 1, blocked: 5 }],
    ['migrations/definitive-v2.yaml', { prerequisites: 9, satisfied: 2, blocked: 7 }],
    ['evidence/definitive-certificate.json', { prerequisites: 10, satisfied: 1, blocked: 9 }],
  ]);
  for (const item of document.artifacts ?? []) {
    const expectedSummary = expectedCounts.get(item.artifactPath);
    if (!expectedSummary) { errors.push('root-readiness-denominator-reduced-or-reordered'); continue; }
    const expectedObservedStatus = expectedSummary.observedStatus ?? 'missing';
    const expectedCoreArtifactPresent = expectedSummary.coreArtifactPresent ?? 0;
    if (item.status !== 'blocked' || item.observedStatus !== expectedObservedStatus || item.coreArtifactPresent !== expectedCoreArtifactPresent || item.completionEffect !== 'none') errors.push('root-readiness-artifact-promoted');
    if (item.prerequisites !== expectedSummary.prerequisites || item.satisfied !== expectedSummary.satisfied || item.blocked !== expectedSummary.blocked) errors.push('root-readiness-summary-rewritten');
    if (item.autoCreate !== false || item.autoPromotion !== false) errors.push('root-readiness-write-boundary-weakened');
  }
  if (document.boundary?.readOnly !== true || document.boundary?.portalIsSubject !== false || document.boundary?.autoCreate !== false || document.boundary?.autoPromotion !== false || document.boundary?.digestOnlyClosure !== false) errors.push('root-readiness-write-boundary-weakened');
  if (document.status !== 'blocked' || document.boundary?.completionEffect !== 'none') errors.push('root-readiness-completion-promoted');
  if (expected && canonicalJson(document) !== canonicalJson(expected)) errors.push('root-readiness-source-drift');
  return { ok: errors.length === 0, errors: [...new Set(errors)] };
}

export function applyPortalRootReadinessStatusNegative(document, testCase) {
  const mutated = structuredClone(document);
  if (testCase.mutation === 'hide-root-gap') {
    mutated.root.missingArtifacts = 0;
    mutated.root.presentArtifacts = 6;
  } else if (testCase.mutation === 'reorder-artifacts') {
    mutated.artifacts = mutated.artifacts.toReversed();
  } else if (testCase.mutation === 'promote-declaration-artifact') {
    mutated.artifacts[0].observedStatus = 'present';
    mutated.artifacts[0].coreArtifactPresent = 1;
  } else if (testCase.mutation === 'rewrite-summary') {
    mutated.artifacts[5].satisfied = 2;
    mutated.artifacts[5].blocked = 8;
  } else if (testCase.mutation === 'subjectize-portal') {
    mutated.boundary.portalIsSubject = true;
  } else if (testCase.mutation === 'allow-auto-create') {
    mutated.boundary.autoCreate = true;
    mutated.artifacts[1].autoCreate = true;
  } else if (testCase.mutation === 'allow-auto-promotion') {
    mutated.boundary.autoPromotion = true;
    mutated.artifacts[2].autoPromotion = true;
  } else if (testCase.mutation === 'promote-completion') {
    mutated.status = 'ready';
    mutated.boundary.completionEffect = 'complete';
  } else {
    throw new Error(`未知のPortal root readiness status負例です: ${testCase.mutation}`);
  }
  return mutated;
}

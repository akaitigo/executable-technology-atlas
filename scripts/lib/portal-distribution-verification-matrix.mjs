import { existsSync } from 'node:fs';
import Ajv2020 from 'ajv/dist/2020.js';
import addFormats from 'ajv-formats';
import { readFile } from 'node:fs/promises';
import path from 'node:path';
import { canonicalJson, sha256 } from './crypto.mjs';
import { DISTRIBUTION_VERIFICATION_CLASSES, projectSubjectDistributionVerification, summarizeDistributionVerification } from './portal-distribution-verification.mjs';

const INDEX_PATH = 'app/data/index.generated.json';

export function buildPortalDistributionVerificationMatrix(index, indexBytes) {
  const coreMatrixPresent = existsSync(path.join(process.cwd(), 'verification.matrix.yaml'));
  const rows = DISTRIBUTION_VERIFICATION_CLASSES.map((classId) => ({
    classId,
    subjects: index.subjects.map((subject) => {
      const cell = subject.distributionVerification.find((item) => item.classId === classId);
      return { subjectId: subject.id, state: cell.state, basis: cell.basis, gapIds: [...cell.gapIds] };
    }),
  }));
  return {
    schemaVersion: 1,
    id: 'portal-subject-distribution-verification-matrix',
    atlasId: 'executable-technology-atlas',
    scope: '97-subject-x-10-distribution-verification-classes',
    status: 'incomplete',
    source: { path: INDEX_PATH, indexDigest: index.digest, artifactDigest: sha256(indexBytes) },
    summary: index.distributionVerificationSummary,
    rows,
    boundary: {
      portalInfrastructureArtifact: true,
      coreSubjectArtifact: { path: 'verification.matrix.yaml', status: coreMatrixPresent ? 'present' : 'missing', effect: 'none' },
      readOnly: true,
      autoPromotion: false,
      runtimeSubstitution: false,
      rawCountsAreCompletion: false,
      distributionStatus: 'not-established',
      completionEffect: 'none',
    },
  };
}

export async function loadPortalDistributionVerificationInputs(root = process.cwd()) {
  const indexBytes = await readFile(path.join(root, INDEX_PATH));
  const schema = JSON.parse(await readFile(path.join(root, 'contracts/schemas/portal-distribution-verification-matrix.schema.json'), 'utf8'));
  return { indexBytes, index: JSON.parse(indexBytes), schema };
}

export async function validatePortalDistributionVerificationMatrix(root, document, schema) {
  const errors = [];
  const ajv = new Ajv2020({ allErrors: true, strict: true });
  addFormats(ajv);
  const validate = ajv.compile(schema);
  if (!validate(document)) errors.push('schema-invalid');
  const { indexBytes, index } = await loadPortalDistributionVerificationInputs(root);
  const expected = buildPortalDistributionVerificationMatrix(index, indexBytes);
  const expectedSubjects = index.subjects.map((subject) => subject.id);
  const rowIds = (document.rows ?? []).map((row) => row.classId);
  if (canonicalJson(rowIds) !== canonicalJson(DISTRIBUTION_VERIFICATION_CLASSES)) errors.push('verification-class-denominator-reduced-or-reordered');
  for (const subject of index.subjects) {
    const expectedCells = projectSubjectDistributionVerification(subject);
    if (canonicalJson(subject.distributionVerification) !== canonicalJson(expectedCells)) errors.push(`importer-verification-projection-drift:${subject.id}`);
    for (const expectedCell of expectedCells) {
      const row = (document.rows ?? []).find((item) => item.classId === expectedCell.classId);
      const cells = row?.subjects ?? [];
      if (canonicalJson(cells.map((cell) => cell.subjectId)) !== canonicalJson(expectedSubjects)) errors.push(`verification-subject-denominator-reduced-or-reordered:${expectedCell.classId}`);
      const actual = cells.find((cell) => cell.subjectId === subject.id);
      if (!actual) continue;
      if (actual.state !== expectedCell.state) errors.push(`verification-state-promoted:${subject.id}:${expectedCell.classId}`);
      if (canonicalJson(actual.gapIds) !== canonicalJson(expectedCell.gapIds)) errors.push(`verification-gap-hidden:${subject.id}:${expectedCell.classId}`);
      if (actual.basis !== expectedCell.basis) errors.push(`verification-basis-rebound:${subject.id}:${expectedCell.classId}`);
      if (['recovery', 'performance', 'compatibility'].includes(expectedCell.classId) && actual.state !== 'not-evaluated') errors.push(`runtime-proof-substitution-forbidden:${subject.id}:${expectedCell.classId}`);
    }
  }
  const expectedSummary = summarizeDistributionVerification(index.subjects);
  if (canonicalJson(document.summary) !== canonicalJson(expectedSummary)) errors.push('verification-summary-drift');
  if (
    document.status !== 'incomplete'
    || document.boundary?.portalInfrastructureArtifact !== true
    || document.boundary?.coreSubjectArtifact?.path !== 'verification.matrix.yaml'
    || document.boundary?.coreSubjectArtifact?.status !== expected.boundary.coreSubjectArtifact.status
    || document.boundary?.coreSubjectArtifact?.effect !== 'none'
    || document.boundary?.readOnly !== true
    || document.boundary?.autoPromotion !== false
    || document.boundary?.runtimeSubstitution !== false
    || document.boundary?.rawCountsAreCompletion !== false
    || document.boundary?.distributionStatus !== 'not-established'
    || document.boundary?.completionEffect !== 'none'
  ) errors.push('verification-matrix-boundary-weakened');
  if (canonicalJson(document) !== canonicalJson(expected)) errors.push('verification-matrix-source-drift');
  return { ok: errors.length === 0, errors: [...new Set(errors)], summary: document.summary ?? {}, digest: sha256(Buffer.from(`${JSON.stringify(document, null, 2)}\n`)) };
}

export function applyPortalDistributionVerificationNegative(document, testCase) {
  const mutated = structuredClone(document);
  const row = mutated.rows.find((item) => item.classId === testCase.classId);
  const cell = row?.subjects.find((item) => item.subjectId === testCase.subjectId);
  if (testCase.mutation === 'remove-class') mutated.rows = mutated.rows.filter((item) => item.classId !== testCase.classId);
  else if (testCase.mutation === 'remove-subject') row.subjects = row.subjects.filter((item) => item.subjectId !== testCase.subjectId);
  else if (testCase.mutation === 'promote-state') {
    cell.state = 'verified';
    cell.gapIds = [];
  } else if (testCase.mutation === 'drop-gap') cell.gapIds = [];
  else if (testCase.mutation === 'substitute-runtime') {
    cell.state = 'verified';
    cell.gapIds = [];
  } else if (testCase.mutation === 'satisfy-core-artifact') {
    mutated.boundary.coreSubjectArtifact.effect = 'closed';
    mutated.boundary.rawCountsAreCompletion = true;
  } else throw new Error(`未知のDistribution Verification負例です: ${testCase.mutation}`);
  return mutated;
}

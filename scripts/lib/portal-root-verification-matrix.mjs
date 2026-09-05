import Ajv2020 from 'ajv/dist/2020.js';
import addFormats from 'ajv-formats';
import { readFile, stat } from 'node:fs/promises';
import path from 'node:path';
import { parse } from 'yaml';
import { canonicalJson, sha256 } from './crypto.mjs';
import { resolveCoreCheckout } from './core-checkout.mjs';

const CORE_COMMIT = '072d7ca77981f51754e824d70c6d4ecd55ea67e5';
const MATRIX_PATH = 'verification.matrix.yaml';
const EVIDENCE_WRAPPERS = Object.freeze({
  'portal.import.integrity': 'evidence/import.integrity.evidence.json',
  'portal.non-regression.baseline': 'evidence/non-regression.evidence.json',
  'portal.ui.build': 'evidence/ui.build.evidence.json',
  'portal.evidence-dependency.own-closure': 'evidence/dependency.own-closure.evidence.json',
  'portal.publication.sbom': 'evidence/publication.sbom.evidence.json',
  'portal.security.headers': 'evidence/security.headers.evidence.json',
  'portal.performance.budget': 'evidence/performance.budget.evidence.json',
  'portal.router.eval': 'evidence/router.eval.evidence.json',
});

const EXPECTED_ROWS = Object.freeze([
  {
    behavior_id: 'portal.root.catalog.fixed-release-index',
    scenario: 'normal',
    applicability: 'required',
    rationale: '固定Releaseと署名検証済みEnvelopeから97 Subject Indexを再現可能に生成する。',
    proof_obligation_id: 'portal.root.catalog.fixed-release-index.normal',
    evidence_ids: ['portal.import.integrity'],
    execution_requirement: 'runtime',
    profile: 'local',
  },
  {
    behavior_id: 'portal.root.search.japanese-facets',
    scenario: 'boundary',
    applicability: 'required',
    rationale: '日本語Facet検索が境界条件でも未完了やGapを隠さず探索導線を維持する。',
    proof_obligation_id: 'portal.root.search.japanese-facets.boundary',
    evidence_ids: ['portal.ui.build', 'portal.non-regression.baseline'],
    execution_requirement: 'runtime',
    profile: 'local',
  },
  {
    behavior_id: 'portal.root.quarantine.invalid-release-refusal',
    scenario: 'refusal',
    applicability: 'required',
    rationale: '署名不正やDigest不一致のRelease候補を公開済み入力として拒否し続ける。',
    proof_obligation_id: 'portal.root.quarantine.invalid-release-refusal.refusal',
    evidence_ids: ['portal.import.integrity'],
    execution_requirement: 'runtime',
    profile: 'local',
  },
  {
    behavior_id: 'portal.root.quarantine.last-known-good',
    scenario: 'failure',
    applicability: 'required',
    rationale: 'import失敗時も空Dashboardへ崩さずlast-known-goodを保持したまま停止する。',
    proof_obligation_id: 'portal.root.quarantine.last-known-good.failure',
    evidence_ids: ['portal.import.integrity', 'portal.evidence-dependency.own-closure'],
    execution_requirement: 'runtime',
    profile: 'local',
  },
  {
    behavior_id: 'portal.root.quarantine.last-known-good',
    scenario: 'recovery',
    applicability: 'required',
    rationale: 'Digest更新だけで復旧済みとせず実再実行後のEvidence世代へ復帰する。',
    proof_obligation_id: 'portal.root.quarantine.last-known-good.recovery',
    evidence_ids: ['portal.evidence-dependency.own-closure'],
    execution_requirement: 'runtime',
    profile: 'local',
  },
  {
    behavior_id: 'portal.root.definitive-v2.read-model',
    scenario: 'migration',
    applicability: 'required',
    rationale: 'bounded履歴とsubject-definitiveを分離したCore v2移行状態をread-onlyで表示する。',
    proof_obligation_id: 'portal.root.definitive-v2.read-model.migration',
    evidence_ids: ['portal.import.integrity', 'portal.ui.build', 'portal.non-regression.baseline', 'portal.router.eval'],
    execution_requirement: 'runtime',
    profile: 'local',
  },
  {
    behavior_id: 'portal.root.publication.closure-artifacts',
    scenario: 'operations',
    applicability: 'required',
    rationale: 'SBOMやPublication artifactを固定しつつ配布未成立を完成扱いへ昇格させない。',
    proof_obligation_id: 'portal.root.publication.closure-artifacts.operations',
    evidence_ids: ['portal.publication.sbom', 'portal.non-regression.baseline'],
    execution_requirement: 'platform',
    profile: 'local',
  },
  {
    behavior_id: 'portal.root.security.headers-boundary',
    scenario: 'security',
    applicability: 'required',
    rationale: '外部追跡や不要権限を拒否するSecurity Header境界を静的成果物で維持する。',
    proof_obligation_id: 'portal.root.security.headers-boundary.security',
    evidence_ids: ['portal.security.headers'],
    execution_requirement: 'static-allowed',
    profile: 'local',
  },
  {
    behavior_id: 'portal.root.performance.search-budget',
    scenario: 'performance',
    applicability: 'required',
    rationale: '97 Subject探索の性能予算を実測Evidenceで保持し件数達成と混同しない。',
    proof_obligation_id: 'portal.root.performance.search-budget.performance',
    evidence_ids: ['portal.performance.budget'],
    execution_requirement: 'runtime',
    profile: 'local',
  },
  {
    behavior_id: 'portal.root.fixed-commit-audit.visibility',
    scenario: 'compatibility',
    applicability: 'required',
    rationale: '固定clean commit監査をRelease未成立のまま表示し未完成Subjectを昇格させない。',
    proof_obligation_id: 'portal.root.fixed-commit-audit.visibility.compatibility',
    evidence_ids: ['portal.import.integrity', 'portal.ui.build', 'portal.non-regression.baseline'],
    execution_requirement: 'runtime',
    profile: 'local',
  },
]);

export function buildExpectedPortalRootVerificationMatrix() {
  return {
    schema_version: 2,
    atlas_id: 'executable-technology-atlas',
    epoch: '2026-08-28',
    rows: EXPECTED_ROWS.map((row) => ({ ...row })),
  };
}

export async function loadPortalRootVerificationMatrix(root = process.cwd()) {
  const bytes = await readFile(path.join(root, MATRIX_PATH));
  return { path: MATRIX_PATH, bytes, document: parse(bytes.toString('utf8')) };
}

async function fileExists(root, relativePath) {
  try {
    return (await stat(path.join(root, relativePath))).isFile();
  } catch {
    return false;
  }
}

export async function validatePortalRootVerificationMatrix(root = process.cwd(), document = null) {
  const errors = [];
  const loaded = document ? null : await loadPortalRootVerificationMatrix(root);
  const matrix = document ?? loaded.document;
  const { coreDir } = resolveCoreCheckout(root, CORE_COMMIT);
  const schema = JSON.parse(await readFile(path.join(coreDir, 'schemas/verification-matrix.schema.json'), 'utf8'));
  const ajv = new Ajv2020({ allErrors: true, strict: false });
  addFormats(ajv);
  const validate = ajv.compile(schema);
  if (!validate(matrix)) errors.push(`core-schema-invalid: ${ajv.errorsText(validate.errors)}`);

  const expected = buildExpectedPortalRootVerificationMatrix();
  const actualRows = matrix.rows ?? [];
  const expectedRowKeys = expected.rows.map((row) => `${row.behavior_id}:${row.scenario}`);
  const actualRowKeys = actualRows.map((row) => `${row.behavior_id}:${row.scenario}`);
  if (actualRows.some((row) => !row.behavior_id?.startsWith('portal.root.'))) errors.push('portal-root-matrix-subjectized');
  if (canonicalJson(actualRowKeys) !== canonicalJson(expectedRowKeys)) errors.push('matrix-row-denominator-reduced-or-reordered');
  if (matrix.schema_version !== expected.schema_version || matrix.atlas_id !== expected.atlas_id || matrix.epoch !== expected.epoch) errors.push('matrix-header-drift');

  for (const expectedRow of expected.rows) {
    const actual = actualRows.find((row) => row.behavior_id === expectedRow.behavior_id && row.scenario === expectedRow.scenario);
    if (!actual) continue;
    if (canonicalJson(actual.evidence_ids) !== canonicalJson(expectedRow.evidence_ids)) errors.push(`matrix-row-evidence-drift:${expectedRow.behavior_id}:${expectedRow.scenario}`);
    if (actual.execution_requirement !== expectedRow.execution_requirement || actual.profile !== expectedRow.profile || actual.applicability !== expectedRow.applicability || actual.proof_obligation_id !== expectedRow.proof_obligation_id || actual.rationale !== expectedRow.rationale) {
      errors.push(`matrix-row-contract-drift:${expectedRow.behavior_id}:${expectedRow.scenario}`);
    }
  }

  for (const row of actualRows) {
    for (const evidenceId of row.evidence_ids ?? []) {
      const wrapperPath = EVIDENCE_WRAPPERS[evidenceId];
      if (!wrapperPath) {
        errors.push(`matrix-evidence-binding-missing:${evidenceId}`);
        continue;
      }
      const wrapper = JSON.parse(await readFile(path.join(root, wrapperPath), 'utf8'));
      if (wrapper.id !== evidenceId) errors.push(`matrix-evidence-wrapper-id-drift:${evidenceId}`);
      if (wrapper.environment?.profile !== row.profile) errors.push(`matrix-evidence-profile-drift:${evidenceId}`);
      if (!(await fileExists(root, wrapper.artifact?.uri ?? ''))) errors.push(`matrix-artifact-binding-missing:${evidenceId}`);
    }
  }

  return {
    ok: errors.length === 0,
    errors: [...new Set(errors)],
    summary: {
      rows: actualRows.length,
      requiredRows: expected.rows.length,
      runtimeRows: actualRows.filter((row) => row.execution_requirement === 'runtime').length,
      platformRows: actualRows.filter((row) => row.execution_requirement === 'platform').length,
      staticAllowedRows: actualRows.filter((row) => row.execution_requirement === 'static-allowed').length,
      scenarios: actualRows.map((row) => row.scenario),
      digest: loaded ? sha256(loaded.bytes) : null,
    },
  };
}

export function applyPortalRootVerificationMatrixNegative(document, testCase) {
  const mutated = structuredClone(document);
  if (testCase.mutation === 'remove-row') mutated.rows.shift();
  else if (testCase.mutation === 'reorder-rows') mutated.rows = mutated.rows.toReversed();
  else if (testCase.mutation === 'rewrite-evidence-ids') mutated.rows[0].evidence_ids = ['portal.publication.sbom'];
  else if (testCase.mutation === 'subjectize-portal') mutated.rows[0].behavior_id = 'subject.definitive.promoted';
  else throw new Error(`未知のPortal root verification matrix負例です: ${testCase.mutation}`);
  return mutated;
}

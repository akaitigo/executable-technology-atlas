const EXACT = Object.freeze({
  schemaVersion: 1,
  id: 'portal-import-lifecycle-visibility',
  status: 'incomplete',
  actual: {
    subjects: 97,
    verified: 7,
    quarantined: 0,
    absent: 90,
    incompleteCurrentReleases: 7,
    publicTrustedCurrentReleases: 0,
    expiredHistoricalReleases: 0,
    supersededHistoricalReleases: 0,
    archivedHistoricalReleases: 0,
    staleHumanReviewHolds: 3,
    definitiveV2Imports: 0,
  },
  fixtureCoverage: {
    failureScenarios: 11,
    registryNegativeCases: 14,
    staleLockCases: 1,
    revokedLockCases: 1,
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

function isExactBoolean(value, expected) {
  return typeof value === 'boolean' && value === expected;
}

function isExactNumber(value, expected) {
  return isInteger(value) && value === expected;
}

function countBy(items, predicate) {
  return items.reduce((total, item) => total + (predicate(item) ? 1 : 0), 0);
}

export function isPortalImportLifecycleSnapshot(value) {
  const actual = read(value, 'actual');
  const fixtureCoverage = read(value, 'fixtureCoverage');
  const boundary = read(value, 'boundary');
  const scenarios = read(fixtureCoverage, 'scenarios');
  const registryCases = read(fixtureCoverage, 'registryCases');
  return isObject(value)
    && value.schemaVersion === EXACT.schemaVersion
    && value.id === EXACT.id
    && value.status === EXACT.status
    && isObject(actual)
    && isExactNumber(actual.subjects, EXACT.actual.subjects)
    && isExactNumber(actual.verified, EXACT.actual.verified)
    && isExactNumber(actual.quarantined, EXACT.actual.quarantined)
    && isExactNumber(actual.absent, EXACT.actual.absent)
    && isExactNumber(actual.incompleteCurrentReleases, EXACT.actual.incompleteCurrentReleases)
    && isExactNumber(actual.publicTrustedCurrentReleases, EXACT.actual.publicTrustedCurrentReleases)
    && isExactNumber(actual.expiredHistoricalReleases, EXACT.actual.expiredHistoricalReleases)
    && isExactNumber(actual.supersededHistoricalReleases, EXACT.actual.supersededHistoricalReleases)
    && isExactNumber(actual.archivedHistoricalReleases, EXACT.actual.archivedHistoricalReleases)
    && isExactNumber(actual.staleHumanReviewHolds, EXACT.actual.staleHumanReviewHolds)
    && isExactNumber(actual.definitiveV2Imports, EXACT.actual.definitiveV2Imports)
    && isObject(fixtureCoverage)
    && isExactBoolean(fixtureCoverage.fixtureOnly, true)
    && isExactNumber(fixtureCoverage.failureScenarios, EXACT.fixtureCoverage.failureScenarios)
    && isExactNumber(fixtureCoverage.registryNegativeCases, EXACT.fixtureCoverage.registryNegativeCases)
    && isExactNumber(fixtureCoverage.staleLockCases, EXACT.fixtureCoverage.staleLockCases)
    && isExactNumber(fixtureCoverage.revokedLockCases, EXACT.fixtureCoverage.revokedLockCases)
    && isExactNumber(fixtureCoverage.quarantineScenarios, 3)
    && isExactNumber(fixtureCoverage.incompleteScenarios, 1)
    && isExactNumber(fixtureCoverage.excludedScenarios, 1)
    && isExactNumber(fixtureCoverage.infeasibleScenarios, 1)
    && isExactNumber(fixtureCoverage.expiredScenarios, 1)
    && isExactNumber(fixtureCoverage.supersededScenarios, 1)
    && isExactNumber(fixtureCoverage.archivedScenarios, 1)
    && Array.isArray(scenarios)
    && scenarios.length === EXACT.fixtureCoverage.failureScenarios
    && countBy(scenarios, (item) => isObject(item) && item.expected === 'quarantined') === 3
    && countBy(scenarios, (item) => isObject(item) && item.expected === 'incomplete') === 1
    && countBy(scenarios, (item) => isObject(item) && item.state === 'excluded') === 1
    && countBy(scenarios, (item) => isObject(item) && item.state === 'infeasible') === 1
    && countBy(scenarios, (item) => isObject(item) && item.state === 'expired') === 1
    && countBy(scenarios, (item) => isObject(item) && item.status === 'superseded') === 1
    && countBy(scenarios, (item) => isObject(item) && item.status === 'archived') === 1
    && Array.isArray(registryCases)
    && registryCases.length === EXACT.fixtureCoverage.registryNegativeCases
    && countBy(registryCases, (item) => isObject(item) && item.id === 'stale-lock') === 1
    && countBy(registryCases, (item) => isObject(item) && item.id === 'revoked-lock') === 1
    && isObject(boundary)
    && isExactBoolean(boundary.readOnly, true)
    && isExactBoolean(boundary.fixtureIsActual, false)
    && isExactBoolean(boundary.negativeCoverageIsProgress, false)
    && isExactBoolean(boundary.staleLockAccepted, false)
    && isExactBoolean(boundary.revokedLockAccepted, false)
    && isExactBoolean(boundary.hideIncomplete, false)
    && isExactBoolean(boundary.hideExpired, false)
    && isExactBoolean(boundary.autoPromotion, false)
    && boundary.distributionStatus === 'not-established'
    && boundary.completionEffect === 'none';
}

export function assertPortalImportLifecycleSnapshot(value) {
  if (!isPortalImportLifecycleSnapshot(value)) {
    throw new Error('portal import lifecycle response is invalid');
  }
  return value;
}

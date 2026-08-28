export function route(index, request) {
  const query = (request.query ?? '').trim().toLocaleLowerCase('ja');
  const mode = request.mode ?? 'discover';
  if (/(攻撃|侵入|credential theft|bypass)/i.test(query) && !/(防御|検証|許可|lab)/i.test(query)) return { mode, decision: 'refuse-unsafe', candidates: [], reason: 'defensive-only境界外' };
  if (/(公開|publish|修正|変更|deploy)/i.test(query)) return { mode, decision: 'permission-required', candidates: [], reason: 'Read Modelに変更権限はない' };
  let candidates = index.subjects.filter((subject) => !query || subject.searchText.includes(query));
  if (request.audience) candidates = candidates.filter((item) => item.release?.audiences.includes(request.audience));
  if (request.outcome) candidates = candidates.filter((item) => item.release?.outcomes.includes(request.outcome));
  if (request.surface) candidates = candidates.filter((item) => item.release?.surfaces.some((surface) => surface.id === request.surface));
  if (request.environment) candidates = candidates.filter((item) => item.release?.requiredProfiles.includes(request.environment));
  if (request.subjectId) candidates = candidates.filter((item) => item.id === request.subjectId);
  const routeable = candidates.filter((item) => item.release?.verification === 'verified');
  const decision = candidates.length === 0 ? 'coverage-gap' : routeable.length === 0 ? 'catalog-only' : 'route';
  return { mode, decision, candidates: candidates.map((item) => ({ id:item.id, catalogStatus:item.status, completion:item.completion, scope:item.scope, exclusions:item.excludes, release:item.release ? { version:item.release.version, status:item.release.status, completion:item.release.completion, uri:item.release.uri, digest:item.release.digest, verification:item.release.verification, coverage:item.release.coverage, evidenceCount:item.release.evidenceCount, requiredProfiles:item.release.requiredProfiles, observedProfiles:item.release.observedProfiles, skill:item.release.skill } : null })), indexDigest:index.digest };
}

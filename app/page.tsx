'use client';

import { useEffect, useMemo, useRef, useState } from 'react';
import atlasIndex from './data/index.generated.json';
import portalCertificate from '../evidence/completion-certificate.json';
import portalRelease from '../release/manifest.json';

type Release = NonNullable<(typeof atlasIndex.subjects)[number]['release']>;
type Subject = (typeof atlasIndex.subjects)[number];
type EvidenceRecord = { id:string; verdict:string; kind:string; environment:{ profile:string } };
type CoverageTarget = { id:string; title:string; requirement:string; state:string; rationale:string; exclusion?:{ reason:string; reviewed_at:string } | null };
type ReleaseDetail = { evidence:EvidenceRecord[]; targets:CoverageTarget[] };

const PAGE_SIZE = 12;
const catalogLabels: Record<string, string> = { planned:'未着手', active:'活動中', existing:'既存', complete:'Catalog状態 complete', deferred:'保留' };
const releaseLabels: Record<string, string> = { planned:'計画', active:'作業中', incomplete:'未完成', complete:'Epoch完了（Definitive未証明）', superseded:'更新済み', archived:'保守終了' };
const stateLabels: Record<string, string> = { missing:'欠落', planned:'計画', partial:'部分', covered:'証拠あり', excluded:'除外', infeasible:'実行困難', expired:'失効' };
const audienceLabels: Record<string, string> = { learner:'初学者', practitioner:'実務者', architect:'Architect', operator:'Operator', maintainer:'Maintainer', reviewer:'Reviewer', educator:'Educator', agent:'Agent' };
const outcomeLabels: Record<string, string> = { understand:'理解', choose:'選択', build:'構築', verify:'検証', operate:'運用', troubleshoot:'診断', evolve:'進化', delegate:'委任' };
const surfaceLabels: Record<string, string> = { 'orientation-scope':'定義と境界', 'foundations-mechanics':'原理', 'architecture-design':'設計', 'implementation-construction':'実装', 'testing-verification':'検証', 'failure-recovery':'失敗回復', 'operations-observability':'運用', 'security-privacy-safety':'安全性', 'performance-capacity-cost':'性能', 'compatibility-integration':'統合', 'migration-evolution-deprecation':'移行', 'decision-comparison':'比較', 'provenance-rights':'来歴', 'agent-skill':'Agent Skill' };

function coverageCounts(release: Release | null) {
  return release?.coverage.states ?? { missing:0, planned:0, partial:0, covered:0, excluded:0, infeasible:0, expired:0 };
}

function releaseTrustLabel(release: Release) {
  return release.trust.usage === 'public-release' ? '公開署名検証' : release.trust.usage === 'fixture-only' ? 'fixture整合性' : '署名整合性';
}

function completionLabel(release: Release) {
  if (release.completion.definitive) return 'Subject Definitive完成';
  if (release.completion.classification === 'bounded-historical') return 'bounded / epoch完了（履歴）';
  return releaseLabels[release.status] ?? release.status;
}

function completionBadgeClass(release: Release) {
  if (release.completion.definitive) return 'release-definitive';
  if (release.completion.classification === 'bounded-historical' || release.status === 'complete') return 'release-bounded';
  return `release-${release.status}`;
}

export default function Home() {
  const [query, setQuery] = useState('');
  const [domain, setDomain] = useState('');
  const [audience, setAudience] = useState('');
  const [outcome, setOutcome] = useState('');
  const [surface, setSurface] = useState('');
  const [status, setStatus] = useState('');
  const [version, setVersion] = useState('');
  const [environment, setEnvironment] = useState('');
  const [skill, setSkill] = useState('');
  const [sort, setSort] = useState('domain');
  const [page, setPage] = useState(1);
  const [selected, setSelected] = useState<Subject | null>(null);
  const searchRef = useRef<HTMLInputElement>(null);
  const dialogRef = useRef<HTMLDialogElement>(null);

  const domains = useMemo(() => [...new Map(atlasIndex.subjects.map((item) => [item.domain.id, item.domain])).values()], []);
  const versions = useMemo(() => [...new Set(atlasIndex.subjects.flatMap((item) => item.release ? [item.release.version] : []))].sort(), []);

  const filtered = useMemo(() => {
    const normalized = query.trim().toLocaleLowerCase('ja');
    const result = atlasIndex.subjects.filter((item) => {
      const release = item.release;
      const stateMatch = status.startsWith('catalog:') ? item.status === status.slice(8) : status.startsWith('release:') ? release?.status === status.slice(8) : status.startsWith('coverage:') ? (release?.coverage.states as Record<string, number> | undefined)?.[status.slice(9)] : status === 'completion:bounded-historical' ? release?.completion.classification === 'bounded-historical' : status === 'completion:subject-definitive' ? release?.completion.definitive : status === 'completion:not-definitive' ? !release?.completion.definitive : true;
      return (!normalized || item.searchText.includes(normalized)) && (!domain || item.domain.id === domain) && (!audience || release?.audiences.includes(audience)) && (!outcome || release?.outcomes.includes(outcome)) && (!surface || release?.surfaces.some((itemSurface) => itemSurface.id === surface)) && (!status || Boolean(stateMatch)) && (!version || release?.version === version) && (!environment || release?.requiredProfiles.includes(environment) || release?.observedProfiles.includes(environment)) && (!skill || (skill === 'available' ? Boolean(release?.skill?.router) : !release?.skill?.router));
    });
    return result.toSorted((a, b) => sort === 'title' ? a.title.localeCompare(b.title, 'ja') : sort === 'coverage' ? (b.release?.coverage.percent ?? -1) - (a.release?.coverage.percent ?? -1) : `${a.domain.title}${a.title}`.localeCompare(`${b.domain.title}${b.title}`, 'ja'));
  }, [query, domain, audience, outcome, surface, status, version, environment, skill, sort]);

  useEffect(() => {
    const listener = (event: KeyboardEvent) => { if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === 'k') { event.preventDefault(); searchRef.current?.focus(); } };
    window.addEventListener('keydown', listener); return () => window.removeEventListener('keydown', listener);
  }, []);
  useEffect(() => {
    if (selected && dialogRef.current && !dialogRef.current.open) dialogRef.current.showModal();
  }, [selected]);

  const reset = () => { setQuery(''); setDomain(''); setAudience(''); setOutcome(''); setSurface(''); setStatus(''); setVersion(''); setEnvironment(''); setSkill(''); };
  const pageCount = Math.max(1, Math.ceil(filtered.length / PAGE_SIZE));
  const effectivePage = Math.min(page, pageCount);
  const visible = filtered.slice((effectivePage - 1) * PAGE_SIZE, effectivePage * PAGE_SIZE);
  const subjectDefinitive = atlasIndex.subjects.filter((item) => item.release?.completion.definitive && item.release.trust.usage === 'public-release').length;
  const boundedHistorical = atlasIndex.subjects.flatMap((item) => item.releaseHistory).filter((release) => release.completion.classification === 'bounded-historical').length;
  const releaseAbsent = atlasIndex.subjects.filter((item) => !item.release).length;
  const releaseIncomplete = atlasIndex.subjects.filter((item) => item.release?.status === 'incomplete').length;
  const fixtureVerified = atlasIndex.subjects.filter((item) => item.release?.verification === 'verified' && item.release.trust.usage === 'fixture-only').length;

  return (
    <>
      <a className="skip-link" href="#atlas-results">検索結果へ移動</a>
      <header className="site-header">
        <a className="brand" href="#top" aria-label="実行可能技術アトラス ホーム"><span className="brand-mark" aria-hidden="true">97</span><span><strong>実行可能技術アトラス</strong><small>Executable Technology Atlas</small></span></a>
        <nav aria-label="主要ナビゲーション"><a href="#explorer">探索</a><a href="#verification">検証</a><a href="#portal-certificate">Portal証明</a><a href="#contract">契約</a></nav>
        <span className="epoch">Epoch <b>{atlasIndex.catalog.coverageEpoch}</b></span>
      </header>

      <main id="top">
        <section className="hero" aria-labelledby="hero-title">
          <div className="hero-copy"><p className="eyebrow">固定Releaseを横断する検証済みRead Model</p><h1 id="hero-title">完成だけを<br />数えない。<em>欠けている<br />証拠まで探せる。</em></h1></div>
          <div className="hero-aside"><p>97 Subject AtlasのManifest、Mastery、Coverage、Evidence、Skill Package、Completion Certificateを索引します。</p><p className="boundary-note"><strong>境界:</strong> Source Tree・Default Branchは参照しません。v1 Certificateは固定Epochのbounded historicalとして保持し、Definitive完成には数えません。公開Trust KeyとCore v2 Definitive Certificateが揃うまで自動昇格しません。現在の{fixtureVerified}件は再現可能なfixture候補です。</p></div>
          <div className="metrics" aria-label="Catalog 概要"><div><strong>97</strong><span>Catalog subjects</span></div><div><strong>{releaseAbsent}</strong><span>固定Releaseなし</span></div><div><strong>{releaseIncomplete}</strong><span>未完成Release候補</span></div><div><strong>{boundedHistorical}</strong><span>bounded履歴証明</span></div><div><strong>{subjectDefinitive}</strong><span>Subject Definitive完成</span></div></div>
        </section>

        <section className="explorer" id="explorer" aria-labelledby="explorer-title">
          <div className="section-heading"><div><p className="eyebrow">Atlas Explorer</p><h2 id="explorer-title">技術を探索する</h2></div><p><span className="live-dot" aria-hidden="true" /> Index digest <code>{atlasIndex.digest.slice(7, 19)}</code></p></div>
          <label className="search-field"><span>検索</span><input ref={searchRef} value={query} onChange={(event) => setQuery(event.target.value)} type="search" placeholder="技術、分野、Outcome、Skill、Canonical ID…" /><kbd aria-hidden="true">⌘ K</kbd></label>
          <div className="facets" aria-label="探索条件">
            <Facet label="分野" value={domain} onChange={setDomain} options={domains.map((item) => [item.id,item.title])} />
            <Facet label="Audience" value={audience} onChange={setAudience} options={Object.entries(audienceLabels)} />
            <Facet label="Outcome" value={outcome} onChange={setOutcome} options={Object.entries(outcomeLabels)} />
            <Facet label="Surface" value={surface} onChange={setSurface} options={Object.entries(surfaceLabels)} />
            <Facet label="状態" value={status} onChange={setStatus} options={[["completion:subject-definitive","完成契約: Subject Definitive"],["completion:bounded-historical","完成契約: bounded履歴"],["completion:not-definitive","完成契約: Definitive未証明"],["catalog:planned","Catalog: 未着手"],["catalog:active","Catalog: 活動中"],["catalog:existing","Catalog: 既存"],["catalog:complete","Catalog状態: complete（完成証明ではない）"],["catalog:deferred","Catalog: 保留"],["release:planned","Release: 計画"],["release:active","Release: 作業中"],["release:incomplete","Release: 未完成"],["release:complete","Manifest: complete（Definitive未証明）"],["release:superseded","Release: 更新済み"],["release:archived","Release: 保守終了"],...["missing","planned","partial","covered","excluded","infeasible","expired"].map((state) => [`coverage:${state}`,`Coverage: ${stateLabels[state]}`])] as [string,string][]} />
            <Facet label="Version" value={version} onChange={setVersion} options={versions.map((item) => [item,item])} />
            <Facet label="環境（宣言/観測）" value={environment} onChange={setEnvironment} options={['local','container','vm','cluster','simulator','cloud-live','hardware-in-the-loop'].map((item) => [item,item])} />
            <Facet label="Skill" value={skill} onChange={setSkill} options={[["available","Routerあり"],["absent","Routerなし"]]} />
          </div>
          <div className="result-tools"><p role="status" aria-live="polite"><strong>{filtered.length}</strong> / 97 subjects <span>— 未完成・除外・実行困難・失効を既定で隠しません</span></p><div><button className="text-button" type="button" onClick={reset}>条件をすべて解除</button><label>並び順<select value={sort} onChange={(event) => setSort(event.target.value)}><option value="domain">分野</option><option value="title">名称</option><option value="coverage">Coverage</option></select></label></div></div>

          <div className="atlas-grid" id="atlas-results" tabIndex={-1}>
            {visible.map((item, index) => <AtlasCard item={item} key={item.id} index={(effectivePage - 1) * PAGE_SIZE + index + 1} onOpen={setSelected} />)}
          </div>
          {visible.length === 0 && <div className="empty-state"><strong>該当するSubjectはありません</strong><p>Coverage Gapを0件の成功として扱いません。条件を解除するか、Catalog正本への追加提案を検討してください。</p><button type="button" onClick={reset}>すべて表示</button></div>}
          <nav className="pagination" aria-label="検索結果ページ"><button type="button" disabled={effectivePage === 1} onClick={() => setPage(effectivePage - 1)}>← 前へ</button><span>{effectivePage} / {pageCount}</span><button type="button" disabled={effectivePage === pageCount} onClick={() => setPage(effectivePage + 1)}>次へ →</button></nav>
        </section>

        <section className="verification-section" id="verification" aria-labelledby="verification-title">
          <div><p className="eyebrow">Verification ledger</p><h2 id="verification-title">検証に失敗したReleaseは、公開Indexへ混ぜない。</h2><p>署名、Digest、Core Schema、Atlas ID、Coverage Epoch、Router、Target Setを順に検証します。失敗時は隔離し、最後に検証済みのIndexを維持します。</p></div>
          <dl className="ledger"><div><dt>Catalog release</dt><dd><code>{atlasIndex.catalog.release.version}</code><span className="pass">署名検証済み {atlasIndex.catalog.trust.usage}</span><span>公開Catalog Releaseではありません</span></dd></div><div><dt>Core v1 正本</dt><dd><code>{atlasIndex.catalog.canonical.commit}</code><span>Completion Policy {atlasIndex.catalog.canonical.policyVersion}</span></dd></div><div><dt>Catalog状態</dt><dd>90 planned / 6 active / 1 existing</dd></div><div><dt>Catalog digest</dt><dd><code>{atlasIndex.catalog.release.digest}</code></dd></div><div><dt>Release candidates</dt><dd>{atlasIndex.verification.verified} integrity verified / {atlasIndex.verification.quarantined} quarantined</dd></div><div><dt>Fallback</dt><dd>last-known-good / stale明示 / atomic replace</dd></div><div><dt>Source policy</dt><dd>fixed-release-only</dd></div></dl>
        </section>

        <section className="certificate-section" id="portal-certificate" aria-labelledby="portal-certificate-title">
          <div><p className="eyebrow">Portal Completion Certificate</p><h2 id="portal-certificate-title">Subjectの完成数と、Portal自身の完成を混ぜない。</h2><p>Portal RepositoryはGitHub PUBLICのmainを正本とします。Portal v1 Certificateも固定Epochのbounded証明です。Subject Definitive完成{subjectDefinitive}件とは別軸で検証・表示します。</p></div>
          <dl className="certificate-ledger"><div><dt>Atlas / Release</dt><dd><code>{portalCertificate.atlas_id}</code><span>{portalCertificate.atlas_release}</span></dd></div><div><dt>Coverage / Policy</dt><dd>{portalCertificate.coverage_epoch}<span>Core {portalCertificate.core_policy_version}</span></dd></div><div><dt>Required profile</dt><dd>{portalCertificate.required_profiles.map((item) => `${item.profile}: ${item.result}`).join(', ')}</dd></div><div><dt>Router Skill Eval</dt><dd>{Math.round(portalCertificate.skill_eval.pass_rate * 100)}% pass</dd></div><div><dt>Source commit</dt><dd><code>{portalCertificate.commit}</code></dd></div><div><dt>Certificate digest</dt><dd><code>{portalCertificate.signature.digest}</code><span className="pass">payload-sha256</span></dd></div><div><dt>Portal Release</dt><dd><code>{portalRelease.release.digest}</code><span>GitHub PUBLIC / {portalRelease.signature.identity}署名</span></dd></div></dl>
        </section>

        <section className="contract-section" id="contract" aria-labelledby="contract-title"><p className="eyebrow">Bounded Completion Contract v1 / Definitive Gate v2 pending</p><h2 id="contract-title">v1 Closureは、固定Epochの履歴証明。</h2><div className="closure-grid">{['Authority','Coverage','Mastery','Claim','Execution','Operational','Skill','Publication'].map((item,index) => <div key={item}><span>{String(index+1).padStart(2,'0')}</span><strong>{item}</strong></div>)}</div><p>Core v1は固定したRelease、Authority Lock、環境、Evidence Setに対するbounded証明です。<code>superseded</code>後も履歴として保持します。Authority由来Inventory Closure、実Runtime Profile、Gapと除外・実行困難のv2判定は、Core v2 Schema/Migration確定後にのみ受理します。</p></section>
      </main>

      <footer><span>Executable Technology Atlas</span><span>日本語UI正本 · Apache-2.0 · Telemetryなし</span></footer>

      <dialog ref={dialogRef} className="subject-dialog" onClose={() => setSelected(null)} aria-labelledby="detail-title">{selected && <SubjectDetail subject={selected} close={() => dialogRef.current?.close()} />}</dialog>
    </>
  );
}

function Facet({ label, value, onChange, options }: { label:string; value:string; onChange:(value:string)=>void; options:[string,string][] }) {
  return <label className={value ? 'facet active' : 'facet'}><span>{label}</span><select value={value} onChange={(event) => onChange(event.target.value)}><option value="">すべて</option>{options.map(([key,text]) => <option key={key} value={key}>{text}</option>)}</select></label>;
}

function AtlasCard({ item, index, onOpen }: { item:Subject; index:number; onOpen:(item:Subject)=>void }) {
  const release = item.release; const counts = coverageCounts(release);
  return <article className="atlas-card"><div className="card-index">{String(index).padStart(2,'0')}</div><div className="card-top"><span>{item.domain.title}</span><span className={`status catalog-${item.status}`}>{catalogLabels[item.status] ?? item.status}</span></div><h3>{item.title}</h3><code lang="en">{item.id}</code><p className="scope">{item.scope}</p>
    {release ? <><div className="release-line"><span className={`status ${completionBadgeClass(release)}`}>{completionLabel(release)}</span><code>{release.version}</code><span className="integrity">✓ {releaseTrustLabel(release)}</span></div><div className="coverage"><div><span>必須Coverage closure</span><strong>{release.coverage.percent}%</strong></div><progress value={release.coverage.percent} max="100">{release.coverage.percent}%</progress><p>{counts.covered} covered · {counts.partial} partial · {counts.planned} planned · {counts.excluded} excluded · {counts.infeasible} infeasible · {counts.expired} expired</p>{release.coverage.unresolvedCoveredEvidence > 0 && <p className="fail">Evidence実体未収集: covered {release.coverage.unresolvedCoveredEvidence}件</p>}</div></> : <div className="no-release"><strong>固定Releaseなし</strong><span>Manifest / Evidence / Certificate 未収集</span></div>}
    <div className="card-footer"><span>{item.stage1_required ? 'Stage 1 必須' : 'Seed / 任意'}</span><button type="button" onClick={() => onOpen(item)}>検証情報を見る <span aria-hidden="true">→</span></button></div></article>;
}

function SubjectDetail({ subject, close }: { subject:Subject; close:()=>void }) {
  const release = subject.release; const counts = coverageCounts(release);
  const [detail, setDetail] = useState<ReleaseDetail | null>(null);
  const [detailError, setDetailError] = useState(false);
  useEffect(() => {
    if (!release) return;
    let active=true;
    fetch(release.detailUrl).then((response)=>{if(!response.ok)throw new Error('detail unavailable');return response.json();}).then((value)=>{if(active)setDetail({ evidence:value.evidence??[], targets:value.targets??[] });}).catch(()=>{if(active)setDetailError(true);});
    return ()=>{active=false;};
  },[release,subject.id]);
  const gaps = detail?.targets.filter((target) => target.state !== 'covered') ?? [];
  return <div className="detail"><header><div><p className="eyebrow">{subject.domain.title} / {subject.id}</p><h2 id="detail-title">{subject.title}</h2></div><button className="close" type="button" onClick={close} aria-label="詳細を閉じる">×</button></header><section><h3>Catalog境界</h3><p>{subject.scope}</p><ul>{subject.excludes.map((item) => <li key={item}>{item}</li>)}</ul></section>
    {!release ? <section className="detail-warning"><h3>固定Releaseはありません</h3><p>Catalogには存在しますが、Manifest、Mastery、Evidence、Skill、Certificateを検証できません。完成済みとしてRouteしません。</p></section> : <>
      <section><h3>固定Releaseと信頼</h3><dl><div><dt>Version / 状態</dt><dd><code>{release.version}</code><span>{completionLabel(release)}</span><span>Manifest status: <code>{release.status}</code></span></dd></div><div><dt>URI</dt><dd><code>{release.uri}</code></dd></div><div><dt>Release digest</dt><dd><code>{release.digest}</code></dd></div><div><dt>署名</dt><dd>{release.signature.algorithm} / <code>{release.signature.keyId}</code>（{release.trust.usage}）</dd></div><div><dt>Authority Lock</dt><dd><code>{release.authorityLockDigest}</code><span>Authority-derived inventory closure: Core v2未確定 / 未証明</span></dd></div><div><dt>Publication</dt>{release.completion.definitive ? <dd className="pass">公開Trust Key・v2 Definitive Certificate検証済み</dd> : release.completion.classification === 'bounded-historical' ? <dd><span>v1 Certificate検証済み — bounded historical</span><code>{release.certificateVerification.digest}</code><span className="fail">Subject Definitive未認定</span></dd> : <dd className="fail">Subject Definitive未証明 — 自動昇格しません</dd>}</div></dl></section>
      <section><h3>Certificate履歴</h3>{subject.releaseHistory.some((item) => item.certificateVerification.present) ? <ul className="history-list">{subject.releaseHistory.filter((item) => item.certificateVerification.present).map((item) => <li key={item.digest}><code>{item.version}</code><span>{completionLabel(item)}</span><span>Epoch {item.completion.coverageEpoch}</span><code>{item.certificateVerification.digest}</code></li>)}</ul> : <p>取込済みCertificate履歴はありません。既存v1証明を追加した場合も削除せず、bounded historicalとしてDigest固定で保持します。</p>}</section>
      <section><h3>Mastery</h3><p className="token-list">{release.audiences.map((item) => <span key={item}>{audienceLabels[item] ?? item}</span>)}</p><p className="token-list">{release.outcomes.map((item) => <span key={item}>{outcomeLabels[item] ?? item}</span>)}</p><p className="token-list">{release.surfaces.map((item) => <span key={item.id}>{surfaceLabels[item.id] ?? item.id}{item.applicability === 'not-applicable' ? '（非適用）' : ''}</span>)}</p></section>
      <section><h3>Coverage状態</h3><div className="state-grid">{Object.entries(counts).map(([state,count]) => <div key={state}><strong>{count}</strong><span>{stateLabels[state] ?? state}<code>{state}</code></span></div>)}</div>{detail && (gaps.length ? <ul className="gap-list">{gaps.map((target) => <li key={target.id}><span className={`status target-${target.state}`}>{stateLabels[target.state] ?? target.state}</span><strong>{target.title}</strong><code>{target.id}</code><p>{target.rationale}</p>{target.exclusion && <p><b>理由:</b> {target.exclusion.reason} <b>再評価日:</b> {target.exclusion.reviewed_at}</p>}</li>)}</ul> : <p>このv1 bundleのTarget Gapは0件です。ただしAuthority-derived inventory closureを証明しないため、Subject Definitive完成には昇格しません。</p>)}</section>
      <section><h3>Evidence / Runtime環境</h3><p>{release.evidenceCount} Evidence records</p><dl><div><dt>宣言Required Profile</dt><dd>{release.requiredProfiles.length ? release.requiredProfiles.join(', ') : 'なし'}</dd></div><div><dt>Evidence観測Profile</dt><dd>{release.observedProfiles.length ? release.observedProfiles.join(', ') : '観測Evidenceなし'}</dd></div><div><dt>v2実Runtime Profile</dt><dd>Core v2判定規則未確定 / 未証明</dd></div></dl>{detailError ? <p className="fail" role="alert">Evidence詳細を読み込めません。概要Indexをlast-known-goodとして表示しています。</p> : detail === null ? <p role="status">Evidence詳細を読み込み中…</p> : <ul className="evidence-list">{detail.evidence.slice(0,8).map((item) => <li key={item.id}><span className={`verdict verdict-${item.verdict}`}>{item.verdict}</span><code>{item.id}</code><span>{item.kind} / {item.environment.profile}</span></li>)}</ul>}</section>
      <section><h3>Router Skill</h3><dl><div><dt>Router</dt><dd><code>{release.skill.router.id}</code></dd></div><div><dt>固定先</dt><dd><code>{release.skill.atlas_release}</code></dd></div><div><dt>Adapters</dt><dd>{release.skill.adapters.join(', ')}</dd></div><div><dt>Eval threshold</dt><dd>{Math.round(release.skill.evals.minimum_pass_rate*100)}%</dd></div></dl></section>
    </>}
  </div>;
}

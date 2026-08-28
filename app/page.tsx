'use client';

import { useEffect, useMemo, useRef, useState } from 'react';
import atlasIndex from './data/index.generated.json';

type Release = NonNullable<(typeof atlasIndex.subjects)[number]['release']>;
type Subject = (typeof atlasIndex.subjects)[number];

const PAGE_SIZE = 12;
const catalogLabels: Record<string, string> = { planned:'未着手', active:'活動中', existing:'既存', complete:'完了', deferred:'保留' };
const releaseLabels: Record<string, string> = { planned:'計画', active:'作業中', incomplete:'未完成', complete:'完成', superseded:'更新済み', archived:'保守終了' };
const stateLabels: Record<string, string> = { missing:'欠落', planned:'計画', partial:'部分', covered:'証拠あり', excluded:'除外', infeasible:'実行困難', expired:'失効' };
const audienceLabels: Record<string, string> = { learner:'初学者', practitioner:'実務者', architect:'Architect', operator:'Operator', maintainer:'Maintainer', reviewer:'Reviewer', educator:'Educator', agent:'Agent' };
const outcomeLabels: Record<string, string> = { understand:'理解', choose:'選択', build:'構築', verify:'検証', operate:'運用', troubleshoot:'診断', evolve:'進化', delegate:'委任' };
const surfaceLabels: Record<string, string> = { 'orientation-scope':'定義と境界', 'foundations-mechanics':'原理', 'architecture-design':'設計', 'implementation-construction':'実装', 'testing-verification':'検証', 'failure-recovery':'失敗回復', 'operations-observability':'運用', 'security-privacy-safety':'安全性', 'performance-capacity-cost':'性能', 'compatibility-integration':'統合', 'migration-evolution-deprecation':'移行', 'decision-comparison':'比較', 'provenance-rights':'来歴', 'agent-skill':'Agent Skill' };

function coverageCounts(release: Release | null) {
  return release?.coverage.states ?? { missing:0, planned:0, partial:0, covered:0, excluded:0, infeasible:0, expired:0 };
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
      const stateMatch = status.startsWith('catalog:') ? item.status === status.slice(8) : status.startsWith('release:') ? release?.status === status.slice(8) : status.startsWith('coverage:') ? (release?.coverage.states as Record<string, number> | undefined)?.[status.slice(9)] : true;
      return (!normalized || item.searchText.includes(normalized)) && (!domain || item.domain.id === domain) && (!audience || release?.audiences.includes(audience)) && (!outcome || release?.outcomes.includes(outcome)) && (!surface || release?.surfaces.some((itemSurface) => itemSurface.id === surface)) && (!status || Boolean(stateMatch)) && (!version || release?.version === version) && (!environment || release?.requiredProfiles.includes(environment)) && (!skill || (skill === 'available' ? Boolean(release?.skill?.router) : !release?.skill?.router));
    });
    return result.toSorted((a, b) => sort === 'title' ? a.title.localeCompare(b.title, 'ja') : sort === 'coverage' ? (b.release?.coverage.percent ?? -1) - (a.release?.coverage.percent ?? -1) : `${a.domain.title}${a.title}`.localeCompare(`${b.domain.title}${b.title}`, 'ja'));
  }, [query, domain, audience, outcome, surface, status, version, environment, skill, sort]);

  useEffect(() => setPage(1), [query, domain, audience, outcome, surface, status, version, environment, skill, sort]);
  useEffect(() => {
    const listener = (event: KeyboardEvent) => { if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === 'k') { event.preventDefault(); searchRef.current?.focus(); } };
    window.addEventListener('keydown', listener); return () => window.removeEventListener('keydown', listener);
  }, []);
  useEffect(() => {
    if (selected && dialogRef.current && !dialogRef.current.open) dialogRef.current.showModal();
  }, [selected]);

  const reset = () => { setQuery(''); setDomain(''); setAudience(''); setOutcome(''); setSurface(''); setStatus(''); setVersion(''); setEnvironment(''); setSkill(''); };
  const pageCount = Math.max(1, Math.ceil(filtered.length / PAGE_SIZE));
  const visible = filtered.slice((page - 1) * PAGE_SIZE, page * PAGE_SIZE);
  const complete = atlasIndex.subjects.filter((item) => item.release?.status === 'complete' && item.release?.certificate).length;
  const incomplete = atlasIndex.subjects.filter((item) => !item.release || item.release.status !== 'complete' || !item.release.certificate).length;

  return (
    <>
      <a className="skip-link" href="#atlas-results">検索結果へ移動</a>
      <header className="site-header">
        <a className="brand" href="#top" aria-label="実行可能技術アトラス ホーム"><span className="brand-mark" aria-hidden="true">97</span><span><strong>実行可能技術アトラス</strong><small>Executable Technology Atlas</small></span></a>
        <nav aria-label="主要ナビゲーション"><a href="#explorer">探索</a><a href="#verification">検証</a><a href="#contract">契約</a></nav>
        <span className="epoch">Epoch <b>{atlasIndex.catalog.coverageEpoch}</b></span>
      </header>

      <main id="top">
        <section className="hero" aria-labelledby="hero-title">
          <div className="hero-copy"><p className="eyebrow">固定Releaseを横断する検証済みRead Model</p><h1 id="hero-title">完成だけを<br />数えない。<em>欠けている<br />証拠まで探せる。</em></h1></div>
          <div className="hero-aside"><p>97 Subject AtlasのManifest、Mastery、Coverage、Evidence、Skill Package、Completion Certificateを索引します。</p><p className="boundary-note"><strong>境界:</strong> Source Tree・Default Branchは参照しません。現時点で実在する署名済み公開ReleaseとCertificateは0件です。7件は再現可能なfixture署名付き候補であり、完成証明ではありません。</p></div>
          <div className="metrics" aria-label="Catalog 概要"><div><strong>97</strong><span>Catalog subjects</span></div><div><strong>{complete}</strong><span>Certificate付き完成</span></div><div><strong>{atlasIndex.verification.verified}</strong><span>Fixture整合性検証</span></div><div><strong>{incomplete}</strong><span>未完成・Releaseなし</span></div></div>
        </section>

        <section className="explorer" id="explorer" aria-labelledby="explorer-title">
          <div className="section-heading"><div><p className="eyebrow">Atlas Explorer</p><h2 id="explorer-title">技術を探索する</h2></div><p><span className="live-dot" aria-hidden="true" /> Index digest <code>{atlasIndex.digest.slice(7, 19)}</code></p></div>
          <label className="search-field"><span>検索</span><input ref={searchRef} value={query} onChange={(event) => setQuery(event.target.value)} type="search" placeholder="技術、分野、Outcome、Skill、Canonical ID…" /><kbd aria-hidden="true">⌘ K</kbd></label>
          <div className="facets" aria-label="探索条件">
            <Facet label="分野" value={domain} onChange={setDomain} options={domains.map((item) => [item.id,item.title])} />
            <Facet label="Audience" value={audience} onChange={setAudience} options={Object.entries(audienceLabels)} />
            <Facet label="Outcome" value={outcome} onChange={setOutcome} options={Object.entries(outcomeLabels)} />
            <Facet label="Surface" value={surface} onChange={setSurface} options={Object.entries(surfaceLabels)} />
            <Facet label="状態" value={status} onChange={setStatus} options={[["catalog:planned","Catalog: 未着手"],["catalog:active","Catalog: 活動中"],["catalog:existing","Catalog: 既存"],["release:incomplete","Release: 未完成"],["release:complete","Release: 完成"],["release:superseded","Release: 更新済み"],["release:archived","Release: 保守終了"],...["missing","planned","partial","covered","excluded","infeasible","expired"].map((state) => [`coverage:${state}`,`Coverage: ${stateLabels[state]}`])] as [string,string][]} />
            <Facet label="Version" value={version} onChange={setVersion} options={versions.map((item) => [item,item])} />
            <Facet label="環境" value={environment} onChange={setEnvironment} options={['local','container','vm','cluster','simulator','cloud-live','hardware-in-the-loop'].map((item) => [item,item])} />
            <Facet label="Skill" value={skill} onChange={setSkill} options={[["available","Routerあり"],["absent","Routerなし"]]} />
          </div>
          <div className="result-tools"><p role="status" aria-live="polite"><strong>{filtered.length}</strong> / 97 subjects <span>— 未完成・除外・実行困難・失効を既定で隠しません</span></p><div><button className="text-button" type="button" onClick={reset}>条件をすべて解除</button><label>並び順<select value={sort} onChange={(event) => setSort(event.target.value)}><option value="domain">分野</option><option value="title">名称</option><option value="coverage">Coverage</option></select></label></div></div>

          <div className="atlas-grid" id="atlas-results" tabIndex={-1}>
            {visible.map((item, index) => <AtlasCard item={item} key={item.id} index={(page - 1) * PAGE_SIZE + index + 1} onOpen={setSelected} />)}
          </div>
          {visible.length === 0 && <div className="empty-state"><strong>該当するSubjectはありません</strong><p>Coverage Gapを0件の成功として扱いません。条件を解除するか、Catalog正本への追加提案を検討してください。</p><button type="button" onClick={reset}>すべて表示</button></div>}
          <nav className="pagination" aria-label="検索結果ページ"><button type="button" disabled={page === 1} onClick={() => setPage((value) => value - 1)}>← 前へ</button><span>{page} / {pageCount}</span><button type="button" disabled={page === pageCount} onClick={() => setPage((value) => value + 1)}>次へ →</button></nav>
        </section>

        <section className="verification-section" id="verification" aria-labelledby="verification-title">
          <div><p className="eyebrow">Verification ledger</p><h2 id="verification-title">検証に失敗したReleaseは、公開Indexへ混ぜない。</h2><p>署名、Digest、Core Schema、Atlas ID、Coverage Epoch、Router、Target Setを順に検証します。失敗時は隔離し、最後に検証済みのIndexを維持します。</p></div>
          <dl className="ledger"><div><dt>Catalog release</dt><dd><code>{atlasIndex.catalog.release.version}</code><span className="pass">署名検証済み fixture</span></dd></div><div><dt>Catalog digest</dt><dd><code>{atlasIndex.catalog.release.digest}</code></dd></div><div><dt>Release candidates</dt><dd>{atlasIndex.verification.verified} integrity verified / {atlasIndex.verification.quarantined} quarantined</dd></div><div><dt>Fallback</dt><dd>last-known-good / stale明示 / atomic replace</dd></div><div><dt>Source policy</dt><dd>fixed-release-only</dd></div></dl>
        </section>

        <section className="contract-section" id="contract" aria-labelledby="contract-title"><p className="eyebrow">Completion Contract 1.0.0</p><h2 id="contract-title">完成は、固定Epochに対する8つのClosure。</h2><div className="closure-grid">{['Authority','Coverage','Mastery','Claim','Execution','Operational','Skill','Publication'].map((item,index) => <div key={item}><span>{String(index+1).padStart(2,'0')}</span><strong>{item}</strong></div>)}</div><p>世界知識の網羅ではなく、固定したRelease、Authority Lock、環境、Evidence Setに対する証明です。<code>superseded</code>になっても当時のCertificateは履歴として保持されます。</p></section>
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
    {release ? <><div className="release-line"><span className={`status release-${release.status}`}>{releaseLabels[release.status] ?? release.status}</span><code>{release.version}</code><span className="integrity">✓ fixture整合性</span></div><div className="coverage"><div><span>必須Coverage closure</span><strong>{release.coverage.percent}%</strong></div><progress value={release.coverage.percent} max="100">{release.coverage.percent}%</progress><p>{counts.covered} covered · {counts.partial} partial · {counts.planned} planned · {counts.excluded} excluded · {counts.infeasible} infeasible · {counts.expired} expired</p></div></> : <div className="no-release"><strong>固定Releaseなし</strong><span>Manifest / Evidence / Certificate 未収集</span></div>}
    <div className="card-footer"><span>{item.stage1_required ? 'Stage 1 必須' : 'Seed / 任意'}</span><button type="button" onClick={() => onOpen(item)}>検証情報を見る <span aria-hidden="true">→</span></button></div></article>;
}

function SubjectDetail({ subject, close }: { subject:Subject; close:()=>void }) {
  const release = subject.release; const counts = coverageCounts(release);
  return <div className="detail"><header><div><p className="eyebrow">{subject.domain.title} / {subject.id}</p><h2 id="detail-title">{subject.title}</h2></div><button className="close" type="button" onClick={close} aria-label="詳細を閉じる">×</button></header><section><h3>Catalog境界</h3><p>{subject.scope}</p><ul>{subject.excludes.map((item) => <li key={item}>{item}</li>)}</ul></section>
    {!release ? <section className="detail-warning"><h3>固定Releaseはありません</h3><p>Catalogには存在しますが、Manifest、Mastery、Evidence、Skill、Certificateを検証できません。完成済みとしてRouteしません。</p></section> : <>
      <section><h3>固定Releaseと信頼</h3><dl><div><dt>Version</dt><dd><code>{release.version}</code> / {releaseLabels[release.status] ?? release.status}</dd></div><div><dt>URI</dt><dd><code>{release.uri}</code></dd></div><div><dt>Release digest</dt><dd><code>{release.digest}</code></dd></div><div><dt>署名</dt><dd>{release.signature.algorithm} / <code>{release.signature.keyId}</code>（fixture-only）</dd></div><div><dt>Authority Lock</dt><dd><code>{release.authorityLockDigest}</code></dd></div><div><dt>Publication</dt><dd className="fail">Certificateなし — 未完成</dd></div></dl></section>
      <section><h3>Mastery</h3><p className="token-list">{release.audiences.map((item) => <span key={item}>{audienceLabels[item] ?? item}</span>)}</p><p className="token-list">{release.outcomes.map((item) => <span key={item}>{outcomeLabels[item] ?? item}</span>)}</p><p className="token-list">{release.surfaces.map((item) => <span key={item.id}>{surfaceLabels[item.id] ?? item.id}{item.applicability === 'not-applicable' ? '（非適用）' : ''}</span>)}</p></section>
      <section><h3>Coverage状態</h3><div className="state-grid">{Object.entries(counts).map(([state,count]) => <div key={state}><strong>{count}</strong><span>{stateLabels[state] ?? state}<code>{state}</code></span></div>)}</div></section>
      <section><h3>Evidence / 環境</h3><p>{release.evidence.length} Evidence records · Required: {release.requiredProfiles.join(', ')}</p><ul className="evidence-list">{release.evidence.slice(0,8).map((item) => <li key={item.id}><span className={`verdict verdict-${item.verdict}`}>{item.verdict}</span><code>{item.id}</code><span>{item.kind} / {item.environment.profile}</span></li>)}</ul></section>
      <section><h3>Router Skill</h3><dl><div><dt>Router</dt><dd><code>{release.skill.router.id}</code></dd></div><div><dt>固定先</dt><dd><code>{release.skill.atlas_release}</code></dd></div><div><dt>Adapters</dt><dd>{release.skill.adapters.join(', ')}</dd></div><div><dt>Eval threshold</dt><dd>{Math.round(release.skill.evals.minimum_pass_rate*100)}%</dd></div></dl></section>
    </>}
  </div>;
}

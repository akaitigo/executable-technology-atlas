'use client';

import { useEffect, useMemo, useRef, useState } from 'react';
import type atlasIndexShape from './data/index.generated.json';
import indexBootstrap from './data/index-bootstrap.generated.json';
import portalCertificate from '../evidence/completion-certificate.json';
import nonRegressionReport from '../evidence/non-regression-report.json';
import portalRelease from '../release/manifest.json';

type AtlasIndex = typeof atlasIndexShape;
type Release = NonNullable<AtlasIndex['subjects'][number]['release']>;
type Subject = AtlasIndex['subjects'][number];
type EvidenceRecord = { id:string; verdict:string; kind:string; environment:{ profile:string } };
type CoverageTarget = { id:string; title:string; requirement:string; state:string; rationale:string; exclusion?:{ reason:string; reviewed_at:string } | null };
type DepthCheck = { id:string; status:string; required:string; observed:unknown; evidence:string[] };
type DepthAxis = { id:string; title:string; portableCriterion:string; denominator:string; status:string; checks:DepthCheck[]; gaps:string[] };
type DepthReference = { id:string; status:string; completionClaim:string; summary:{axes:number;satisfied:number;partial:number;missing:number}; denominatorPolicy:{source:string;transplantAbsoluteCounts:boolean;note:string}; observedDensity:{lockedE2ETests:number;[key:string]:unknown}; axes:DepthAxis[]; source:{repository:string;commit:string;path:string;digest:string;envelopeDigest:string;trust:{usage:string}}; completion:{definitive:boolean;bounded:boolean;reason:string} };
type ReleaseDetail = { evidence:EvidenceRecord[]; targets:CoverageTarget[]; depthReference:DepthReference | null };
type ReviewProjection = { edge_id:string;reference_url:string;pattern_id:string;pattern_kind:string;candidate_behavior_id:string;capability_id:string;target_id:string;claim_id:string;variant_ids:string[];surface_ids:string[];classification_basis:'domain-contract-projection-unreviewed' };
type ReviewPacket = { packet_id:string;priority:0;status:'pending-human';read_only:true;semantic_decision:'none-by-export';source_binding:{anchor_id:string;document_id:string;document_url:string;source_ids:string[];locked_source_digest:string;inventory_tool_digest:string;review_queue_tool_digest:string;locator:string;locator_kind:string;context_start:number;context_end:number;context_unit:string;context_digest:string};semantic_hint:{semantic_kind:string;tag:string;heading_level:number|null};deep_link:{url:string;kind:string;resolves_from_locked_locator:true};candidate_domain_projections:ReviewProjection[];proposed_cluster_ids:string[];review_prompts:{id:string;prompt_ja:string}[];decision_boundary:{write_mode:string;accepted_actions:string[];required_fields:string[];decision_ids:string[];human_decision_recorded:boolean} };
type AuthorityReviewIndex = { subjectId:string;atlasId:string;status:string;mode:'read-only';queueId:string;summary:{packets:number;unique_anchors:number;candidate_domain_projections:number;deep_links:number;pending_human:number;human_reviewed:number;proposed_clusters:number;semantic_decisions_by_export:number;stale_document_holds:number;decisions:number;has_human_progress:boolean};capabilities:{write_decisions:false;promote_human_review:false};exportUrl:string;source:{repository:string;commit:string;exportDigest:string;exportSchemaDigest:string;packetSchemaDigest:string;trust:{usage:string}} };
type AuthorityReviewExport = { schema_version:1;contract_id:string;atlas_id:string;status:string;mode:'read-only';capabilities:{write_decisions:false;promote_human_review:false};summary:AuthorityReviewIndex['summary'];packets:{id:string;anchor_id:string;deep_link:string;candidate_edges:number;proposed_cluster_ids:string[]}[];proposed_clusters:{id:string;proposal_type:string;basis:string;basis_value:string;packet_ids:string[];candidate_edge_ids:string[];semantic_decision:'none-machine-proposal-only';human_reviewed:false}[];stale_holds:{document_id:string;document_url:string;locator:string;status:string;reason:string;locked_source_digest:string;fetched_digest:string}[];stale_candidate_report:{status:string;locked_digests_updated:0;human_choices:0};decision_boundary:{export_accepts_writes:false;decisions_observed:0} };
type EvidenceDependencyIndex = { subjectId:string;availability:'available'|'missing';status:'current'|'stale-or-incomplete'|'missing-required-output';graphStatus:string|null;summary:{inputs:number;inputChanged:number;inputCurrent:number;outputs:number;outputStale:number;outputCurrent:number;impactedOutputs:number;runs:number;missingRequiredOutputs:number;structureDrift:number};coreGate:{result:string;command:string;coreCommit:string|null;runtimeIdentity:Record<string,unknown>|null;diagnostics:string[]};missingRequiredOutputs?:string[];structures?:{id:string;status:string}[];detailUrl:string|null;readOnly?:boolean;autoPromotion?:boolean };
type EvidenceDependencyDetail = EvidenceDependencyIndex & { inputs:{id:string;kind:string;members:string[];baseline_digest:string;current_digest:string;observed_at:string;state:'current'|'changed'}[];outputs:{id:string;kind:string;path:string;digest:string;status:'current'|'stale';impacted_by:string[];run:{id:string;command:string;result:string;attempts:number;started_at:string;completed_at:string;execution_kind:string;runtime_identity:Record<string,unknown>|null;input_bindings:{input_id:string;digest:string}[]}|null}[];requiredOutputs:string[];structures:{id:string;kind:string;path:string;baseline_digest:string;gate:{id:string;status:string;detail:string}}[];coreGate:EvidenceDependencyIndex['coreGate'] & {executedAt?:string;missingRequiredOutputs?:string[];structureResults?:unknown[]} };
type DefinitiveV2Index = { subjectId:string;atlasId:string|null;availability:'available'|'missing';status:'subject-definitive'|'subject-definitive-incomplete'|'subject-definitive-input-missing';completionClass:'subject-definitive'|'not-definitive';coreContract:{status:'final';commit:string};coreGate:{result:string;command:string;diagnostics:string[];runtimeIdentity?:Record<string,unknown>};migration:{status:string;requiredActions:string[];historicalCertificate:unknown};inventoryClosure:{status:string;required:number|null;classified:number|null;unclassified:number|null;openRequired:number|null;excluded:number;infeasible:number};runtimeProfiles:{profile?:string;id?:string;status:string;runtimeIdentity?:Record<string,unknown>|null}[];gapIds:string[];certificate:{schemaVersion:number;completionClass:string;issuedAt:string;commit:string;digest:string;trust:{usage:string}}|null;detailUrl:string|null;readOnly:boolean;autoPromotion:boolean };
type DefinitiveV2Summary = { coreCommit:string;contractStatus:string;subjects:number;available:number;definitive:number;incomplete:number;missing:number;inventoryUnevaluated:number;openRequiredKnown:number;excluded:number;infeasible:number;runtimeProfiles:number;runtimeProfilesCurrent:number;runtimeProfilesUnverified:number;gapInstances:number;gapCounts:{id:string;count:number}[];autoPromotion:boolean };
type FixedCommitGate = {result:string;summary:Record<string,unknown>;diagnostics?:string[]};
type FixedCommitDepthReference = {sourcePath:string;status:'incomplete';summary:{axes:18;satisfied:number;partial:number;missing:number};denominatorPolicy:{source:string;requiredAtomicItems:number;transplantFrontendCounts:false;rule:string};axes:{id:string;status:'satisfied'|'partial'|'missing';denominator:string;proofGranularity:string;evidencePaths:string[];gaps:string[]}[]};
type FixedCommitAudit = { schemaVersion:1;subjectId:string;atlasId:string;status:'fixed-commit-incomplete';source:{repository:string;commit:string;tree:string;mode:'fixed-clean-commit';attestationDigest:string;trust:{usage:string}};releaseBoundary:{status:'unpublished-fixed-commit';tag:string|null;signedManifest:false;publicTrustKey:false;definitiveCertificate:false};manifest:{status:'incomplete';completionClass:'incomplete';targets:number;openRequired:number;claims:number;evidence:number};core:{commit:string;audit:FixedCommitGate;evidenceDependency:FixedCommitGate;authorityExtraction:FixedCommitGate;authorityBody:FixedCommitGate;authorityReview:FixedCommitGate;definitive:FixedCommitGate;scenarioTrace?:FixedCommitGate;nonRegression?:FixedCommitGate;evidenceDurability?:FixedCommitGate};depthReference?:FixedCommitDepthReference;gaps:{id:string;status:'open';detail:string;count:number}[];readOnly:true;autoPromotion:false };
type FixedCommitAuditAvailableIndex = {schemaVersion:1;subjectId:string;atlasId:string;availability:'available';status:'fixed-commit-incomplete';source:{repository:string;commit:string;tree:string;attestationDigest:string};manifest:{status:'incomplete';openRequired:number};gapCount:number;gapIds:string[];detailUrl:string;coreGate:{result:'fail';command:string;diagnostics:string[]};readOnly:true;autoPromotion:false};
type FixedCommitAuditMissingIndex = {schemaVersion:1;subjectId:string;atlasId:null;availability:'missing';status:'fixed-commit-input-missing';source:null;manifest:{status:'not-evaluated';openRequired:null};gapCount:1;gapIds:['fixed-clean-commit-audit-input-missing'];detailUrl:null;coreGate:{result:'not-run';command:string;diagnostics:string[]};readOnly:true;autoPromotion:false};
type FixedCommitAuditIndex = FixedCommitAuditAvailableIndex | FixedCommitAuditMissingIndex;

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

function isBoundIndex(value:unknown):value is AtlasIndex {
  if(!value||typeof value!=='object')return false;
  const candidate=value as Partial<AtlasIndex>;
  return candidate.digest===indexBootstrap.indexDigest
    &&candidate.subjects?.length===indexBootstrap.subjects
    &&candidate.completionSummary?.subjectDefinitive===indexBootstrap.completionSummary.subjectDefinitive
    &&candidate.definitiveV2Summary?.missing===indexBootstrap.definitiveV2Summary.missing
    &&candidate.definitiveV2Summary?.autoPromotion===false
    &&candidate.fixedCommitAuditSummary?.missing===indexBootstrap.fixedCommitAuditSummary.missing
    &&candidate.fixedCommitAuditSummary?.releaseEligible===0
    &&candidate.fixedCommitAuditSummary?.autoPromotion===false;
}

async function parseVerifiedIndex(response:Response):Promise<AtlasIndex> {
  if(!response.ok)throw new Error(`index HTTP ${response.status}`);
  const bytes=await response.arrayBuffer();
  const hash=await crypto.subtle.digest('SHA-256',bytes);
  const observed=`sha256:${[...new Uint8Array(hash)].map((value)=>value.toString(16).padStart(2,'0')).join('')}`;
  if(observed!==indexBootstrap.artifactDigest)throw new Error('index artifact digest mismatch');
  const value:unknown=JSON.parse(new TextDecoder().decode(bytes));
  if(!isBoundIndex(value))throw new Error('index binding mismatch');
  return value;
}

export default function Home() {
  const [atlasIndex,setAtlasIndex]=useState<AtlasIndex|null>(null);
  const [loadFailed,setLoadFailed]=useState(false);
  useEffect(()=>{
    const controller=new AbortController();
    fetch(indexBootstrap.publicUrl,{cache:'force-cache',credentials:'same-origin',signal:controller.signal})
      .then(parseVerifiedIndex)
      .then(setAtlasIndex)
      .catch((error:unknown)=>{if(error instanceof DOMException&&error.name==='AbortError')return;setLoadFailed(true);});
    return()=>controller.abort();
  },[]);
  if(!atlasIndex)return <IndexLoadBoundary failed={loadFailed}/>;
  return <AtlasHome atlasIndex={atlasIndex}/>;
}

function IndexLoadBoundary({failed}:{failed:boolean}) {
  const summary=indexBootstrap.definitiveV2Summary;
  return <main id="top"><section className="hero" aria-labelledby="index-boundary-title" role={failed?'alert':'status'} aria-live="polite"><div className="hero-copy"><p className="eyebrow">Digest固定Read Model</p><h1 id="index-boundary-title">{failed?'検証済みIndexを読み込めません':'検証済みIndexを読み込んでいます'}</h1></div><div className="hero-aside"><p>{failed?indexBootstrap.fallback.message:'Subject一覧を表示する前に、固定URL・Index digest・件数・完成境界を照合しています。'}</p><p className="boundary-note"><strong>Fail closed:</strong> この画面はSubject 0件や完成0件という判定ではありません。直前に生成された集約ではSubject Definitive {summary.definitive}件、v2入力missing {summary.missing}件、固定commit監査入力missing {indexBootstrap.fixedCommitAuditSummary.missing}件、既知Gap {summary.gapInstances}件です。未取得の詳細を完成・推奨へ昇格しません。</p></div><div className="metrics" aria-label="固定bootstrapの未完了集約"><div><strong>{indexBootstrap.subjects}</strong><span>期待するCatalog subjects</span></div><div><strong>{summary.missing}</strong><span>Definitive v2 input missing</span></div><div><strong>{indexBootstrap.fixedCommitAuditSummary.missing}</strong><span>固定commit監査 input missing</span></div><div><strong>{summary.gapInstances}</strong><span>既知Gap</span></div><div><strong>{indexBootstrap.fixedCommitAuditSummary.incomplete}</strong><span>固定commit監査 incomplete</span></div><div><strong>{indexBootstrap.evidenceDependencySummary.missing}</strong><span>Dependency Graph missing</span></div><div><strong>{summary.definitive}</strong><span>Subject Definitive（固定集約）</span></div></div></section></main>;
}

function AtlasHome({atlasIndex}:{atlasIndex:AtlasIndex}) {
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
  const subjects=atlasIndex.subjects;

  const domains = useMemo(() => [...new Map(subjects.map((item) => [item.domain.id, item.domain])).values()], [subjects]);
  const versions = useMemo(() => [...new Set(subjects.flatMap((item) => item.release ? [item.release.version] : []))].sort(), [subjects]);

  const filtered = useMemo(() => {
    const normalized = query.trim().toLocaleLowerCase('ja');
    const result = subjects.filter((item) => {
      const release = item.release;
      const stateMatch = status.startsWith('catalog:') ? item.status === status.slice(8) : status.startsWith('release:') ? release?.status === status.slice(8) : status.startsWith('coverage:') ? (release?.coverage.states as Record<string, number> | undefined)?.[status.slice(9)] : status.startsWith('dependency:') ? item.evidenceDependency.status===status.slice(11) : status.startsWith('definitive:') ? item.definitiveV2.status===status.slice(11) : status.startsWith('audit:') ? item.fixedCommitAudit?.status===status.slice(6) : status === 'completion:bounded-historical' ? release?.completion.classification === 'bounded-historical' : status === 'completion:subject-definitive' ? release?.completion.definitive : status === 'completion:not-definitive' ? !release?.completion.definitive : true;
      return (!normalized || item.searchText.includes(normalized)) && (!domain || item.domain.id === domain) && (!audience || release?.audiences.includes(audience)) && (!outcome || release?.outcomes.includes(outcome)) && (!surface || release?.surfaces.some((itemSurface) => itemSurface.id === surface)) && (!status || Boolean(stateMatch)) && (!version || release?.version === version) && (!environment || release?.requiredProfiles.includes(environment) || release?.observedProfiles.includes(environment)) && (!skill || (skill === 'available' ? Boolean(release?.skill?.router) : !release?.skill?.router));
    });
    return result.toSorted((a, b) => sort === 'title' ? a.title.localeCompare(b.title, 'ja') : sort === 'coverage' ? (b.release?.coverage.percent ?? -1) - (a.release?.coverage.percent ?? -1) : `${a.domain.title}${a.title}`.localeCompare(`${b.domain.title}${b.title}`, 'ja'));
  }, [subjects, query, domain, audience, outcome, surface, status, version, environment, skill, sort]);

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
  const boundedHistorical = atlasIndex.completionSummary.boundedHistorical;
  const openRequired = atlasIndex.completionSummary.openRequired;
  const unclassified = atlasIndex.completionSummary.unclassified;
  const releaseAbsent = atlasIndex.subjects.filter((item) => !item.release).length;
  const releaseIncomplete = atlasIndex.subjects.filter((item) => item.release?.status === 'incomplete').length;
  const fixtureVerified = atlasIndex.subjects.filter((item) => item.release?.verification === 'verified' && item.release.trust.usage === 'fixture-only').length;
  const dependencyMissing=atlasIndex.evidenceDependencySummary.missing;
  const fixedCommitIncomplete=atlasIndex.fixedCommitAuditSummary.incomplete;
  const fixedCommitMissing=atlasIndex.fixedCommitAuditSummary.missing;

  return (
    <>
      <a className="skip-link" href="#atlas-results">検索結果へ移動</a>
      <header className="site-header">
        <a className="brand" href="#top" aria-label="実行可能技術アトラス ホーム"><span className="brand-mark" aria-hidden="true">97</span><span><strong>実行可能技術アトラス</strong><small>Executable Technology Atlas</small></span></a>
        <nav aria-label="主要ナビゲーション"><a href="#explorer">探索</a><a href="#definitive-v2">Definitive v2</a><a href="#authority-review">Human Review</a><a href="#evidence-dependency">Dependency Graph</a><a href="#verification">検証</a><a href="#portal-certificate">Portal証明</a><a href="#contract">契約</a></nav>
        <span className="epoch">Epoch <b>{atlasIndex.catalog.coverageEpoch}</b></span>
      </header>

      <main id="top">
        <section className="hero" aria-labelledby="hero-title">
          <div className="hero-copy"><p className="eyebrow">固定Releaseを横断する検証済みRead Model</p><h1 id="hero-title">完成だけを<br />数えない。<em>欠けている<br />証拠まで探せる。</em></h1></div>
          <div className="hero-aside"><p>97 Subject AtlasのManifest、Mastery、Coverage、Evidence、Skill Package、Completion Certificateを索引します。</p><p className="boundary-note"><strong>境界:</strong> Source Tree・Default Branchは参照しません。v1 Certificateは固定Epochのbounded historicalとして保持し、Definitive完成には数えません。公開Trust KeyとCore v2 Definitive Certificateが揃うまで自動昇格しません。現在の{fixtureVerified}件は再現可能なfixture候補です。</p></div>
          <div className="metrics" aria-label="Catalog 概要"><div><strong>97</strong><span>Catalog subjects</span></div><div><strong>{releaseAbsent}</strong><span>固定Releaseなし</span></div><div><strong>{fixedCommitMissing}</strong><span>固定commit監査 input missing</span></div><div><strong>{fixedCommitIncomplete}</strong><span>固定commit監査 / Release未成立</span></div><div><strong>{openRequired}</strong><span>open required Targets</span></div><div><strong>{unclassified}</strong><span>unclassified / 未完了</span></div><div><strong>{dependencyMissing}</strong><span>Dependency Graph missing</span></div><div><strong>{boundedHistorical}</strong><span>bounded履歴証明</span></div><div><strong>{subjectDefinitive}</strong><span>Subject Definitive完成</span></div></div>
        </section>

        <section className="explorer" id="explorer" aria-labelledby="explorer-title">
          <div className="section-heading"><div><p className="eyebrow">Atlas Explorer</p><h2 id="explorer-title">技術を探索する</h2></div><p><span className="live-dot" aria-hidden="true" /> Index digest <code>{atlasIndex.digest.slice(7, 19)}</code></p></div>
          <label className="search-field"><span>検索</span><input ref={searchRef} value={query} onChange={(event) => setQuery(event.target.value)} type="search" placeholder="技術、分野、Outcome、Skill、Canonical ID…" /><kbd aria-hidden="true">⌘ K</kbd></label>
          <div className="facets" aria-label="探索条件">
            <Facet label="分野" value={domain} onChange={setDomain} options={domains.map((item) => [item.id,item.title])} />
            <Facet label="Audience" value={audience} onChange={setAudience} options={Object.entries(audienceLabels)} />
            <Facet label="Outcome" value={outcome} onChange={setOutcome} options={Object.entries(outcomeLabels)} />
            <Facet label="Surface" value={surface} onChange={setSurface} options={Object.entries(surfaceLabels)} />
            <Facet label="状態" value={status} onChange={setStatus} options={[["completion:subject-definitive","完成契約: Subject Definitive"],["completion:bounded-historical","完成契約: bounded履歴"],["completion:not-definitive","完成契約: Definitive未証明"],["audit:fixed-commit-input-missing","固定commit監査: 入力なし / 未評価"],["audit:fixed-commit-incomplete","固定commit監査: incomplete / Release未成立"],["definitive:subject-definitive-input-missing","Definitive v2: 固定入力なし"],["definitive:subject-definitive-incomplete","Definitive v2: Gate未通過"],["definitive:subject-definitive","Definitive v2: Gate pass"],["dependency:current","Dependency: current / Core Gate pass"],["dependency:stale-or-incomplete","Dependency: stale / incomplete"],["dependency:missing-required-output","Dependency: required output missing"],["catalog:planned","Catalog: 未着手"],["catalog:active","Catalog: 活動中"],["catalog:existing","Catalog: 既存"],["catalog:complete","Catalog状態: complete（完成証明ではない）"],["catalog:deferred","Catalog: 保留"],["release:planned","Release: 計画"],["release:active","Release: 作業中"],["release:incomplete","Release: 未完成"],["release:complete","Manifest: complete（Definitive未証明）"],["release:superseded","Release: 更新済み"],["release:archived","Release: 保守終了"],...["missing","planned","partial","covered","excluded","infeasible","expired"].map((state) => [`coverage:${state}`,`Coverage: ${stateLabels[state]}`])] as [string,string][]} />
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

        <DefinitiveV2Workspace subjects={atlasIndex.subjects.map((item)=>({id:item.id,title:item.title,definitive:item.definitiveV2 as DefinitiveV2Index}))} summary={atlasIndex.definitiveV2Summary as DefinitiveV2Summary} />
        <AuthorityReviewWorkspace subjects={atlasIndex.subjects.filter((item)=>item.authorityReview).map((item)=>({id:item.id,title:item.title,review:item.authorityReview as AuthorityReviewIndex}))} />
        <EvidenceDependencyWorkspace subjects={atlasIndex.subjects.map((item)=>({id:item.id,title:item.title,dependency:item.evidenceDependency as EvidenceDependencyIndex}))} coreCommit={atlasIndex.evidenceDependencySummary.coreCommit} />

        <section className="verification-section" id="verification" aria-labelledby="verification-title">
          <div><p className="eyebrow">Verification ledger</p><h2 id="verification-title">検証に失敗したReleaseは、公開Indexへ混ぜない。</h2><p>署名、Digest、Core Schema、Atlas ID、Coverage Epoch、Router、Target Setを順に検証します。失敗時は隔離し、最後に検証済みのIndexを維持します。</p></div>
          <dl className="ledger"><div><dt>Catalog release</dt><dd><code>{atlasIndex.catalog.release.version}</code><span className="pass">署名検証済み {atlasIndex.catalog.trust.usage}</span><span>公開Catalog Releaseではありません</span></dd></div><div><dt>Core v1 正本</dt><dd><code>{atlasIndex.catalog.canonical.commit}</code><span>Completion Policy {atlasIndex.catalog.canonical.policyVersion}</span></dd></div><div><dt>Core Definitive v2</dt><dd><code>{atlasIndex.completionPolicy.coreCommit}</code><span>契約確定 / Subject入力は{atlasIndex.definitiveV2Summary.missing}件missing</span></dd></div><div><dt>bounded / definitive</dt><dd>{boundedHistorical} bounded historical / {subjectDefinitive} subject-definitive<span>v2公開Trust・固定bundle・Core Gate passなしでは自動昇格しません</span></dd></div><div><dt>未完了分類</dt><dd>{openRequired} open required / {unclassified} unclassified<span>{releaseIncomplete} incomplete Release / {releaseAbsent} 固定Releaseなし</span></dd></div><div><dt>Non-regression</dt><dd className={nonRegressionReport.verdict === 'pass' ? 'pass' : 'fail'}>{nonRegressionReport.verdict.toUpperCase()}<span>{nonRegressionReport.summary.baselineSubjects} Subjects / {nonRegressionReport.summary.baselineTargets} Targets / {nonRegressionReport.summary.baselineEvidence} Evidence / {nonRegressionReport.summary.violations} violations</span></dd></div><div><dt>Failure visibility baseline</dt><dd>{atlasIndex.failureVisibility.scenarios.map((scenario) => <span key={scenario.id}><code>{scenario.id}</code> — {scenario.state ?? scenario.status ?? scenario.verdict ?? scenario.expected}</span>)}</dd></div><div><dt>Catalog digest</dt><dd><code>{atlasIndex.catalog.release.digest}</code></dd></div><div><dt>Release candidates</dt><dd>{atlasIndex.verification.verified} integrity verified / {atlasIndex.verification.quarantined} quarantined</dd></div><div><dt>Fallback</dt><dd>last-known-good / stale明示 / atomic replace</dd></div><div><dt>Source policy</dt><dd>fixed-release-only</dd></div></dl>
        </section>

        <section className="certificate-section" id="portal-certificate" aria-labelledby="portal-certificate-title">
          <div><p className="eyebrow">Portal Completion Certificate</p><h2 id="portal-certificate-title">Subjectの完成数と、Portal自身の完成を混ぜない。</h2><p>Portal RepositoryはGitHub PUBLICのmainを正本とします。Portal v1 Certificateも固定Epochのbounded証明です。Subject Definitive完成{subjectDefinitive}件とは別軸で検証・表示します。</p></div>
          <dl className="certificate-ledger"><div><dt>Atlas / Release</dt><dd><code>{portalCertificate.atlas_id}</code><span>{portalCertificate.atlas_release}</span></dd></div><div><dt>Coverage / Policy</dt><dd>{portalCertificate.coverage_epoch}<span>Core {portalCertificate.core_policy_version}</span></dd></div><div><dt>Required profile</dt><dd>{portalCertificate.required_profiles.map((item) => `${item.profile}: ${item.result}`).join(', ')}</dd></div><div><dt>Router Skill Eval</dt><dd>{Math.round(portalCertificate.skill_eval.pass_rate * 100)}% pass</dd></div><div><dt>Source commit</dt><dd><code>{portalCertificate.commit}</code></dd></div><div><dt>Certificate digest</dt><dd><code>{portalCertificate.signature.digest}</code><span className="pass">payload-sha256</span></dd></div><div><dt>Portal Release</dt><dd><code>{portalRelease.release.digest}</code><span>GitHub PUBLIC / {portalRelease.signature.identity}署名</span></dd></div></dl>
        </section>

        <section className="contract-section" id="contract" aria-labelledby="contract-title"><p className="eyebrow">Bounded Completion Contract v1 / Definitive Gate v2 final</p><h2 id="contract-title">v1 Closureは、固定Epochの履歴証明。</h2><div className="closure-grid">{['Authority','Coverage','Mastery','Claim','Execution','Operational','Skill','Publication'].map((item,index) => <div key={item}><span>{String(index+1).padStart(2,'0')}</span><strong>{item}</strong></div>)}</div><p>Core v1は固定したRelease、Authority Lock、環境、Evidence Setに対するbounded証明です。<code>superseded</code>後も履歴として保持します。Core v2契約は正式main <code>{atlasIndex.completionPolicy.coreCommit}</code> で確定しています。Portalは署名済みv2 bundle、公開Trust、Core Definitive Gate passを固定Releaseへ結び付けて検証できた場合だけSubject Definitiveを表示します。</p></section>
      </main>

      <footer><span>Executable Technology Atlas</span><span>日本語UI正本 · Apache-2.0 · Telemetryなし</span></footer>

      <dialog ref={dialogRef} className="subject-dialog" onClose={() => setSelected(null)} aria-labelledby="detail-title">{selected && <SubjectDetail key={selected.id} subject={selected} close={() => dialogRef.current?.close()} />}</dialog>
    </>
  );
}

function Facet({ label, value, onChange, options }: { label:string; value:string; onChange:(value:string)=>void; options:[string,string][] }) {
  return <label className={value ? 'facet active' : 'facet'}><span>{label}</span><select value={value} onChange={(event) => onChange(event.target.value)}><option value="">すべて</option>{options.map(([key,text]) => <option key={key} value={key}>{text}</option>)}</select></label>;
}

function AtlasCard({ item, index, onOpen }: { item:Subject; index:number; onOpen:(item:Subject)=>void }) {
  const release = item.release; const counts = coverageCounts(release);
  return <article className="atlas-card"><div className="card-index">{String(index).padStart(2,'0')}</div><div className="card-top"><span>{item.domain.title}</span><span className={`status catalog-${item.status}`}>{catalogLabels[item.status] ?? item.status}</span></div><h3>{item.title}</h3><code lang="en">{item.id}</code><p className="scope">{item.scope}</p>
    {release ? <><div className="release-line"><span className={`status ${completionBadgeClass(release)}`}>{completionLabel(release)}</span><code>{release.version}</code><span className="integrity">✓ {releaseTrustLabel(release)}</span></div><div className="coverage"><div><span>必須Coverage closure</span><strong>{release.coverage.percent}%</strong></div><progress value={release.coverage.percent} max="100">{release.coverage.percent}%</progress><p>{counts.covered} covered · {counts.partial} partial · {counts.planned} planned · {counts.excluded} excluded · {counts.infeasible} infeasible · {counts.expired} expired</p>{release.coverage.unresolvedCoveredEvidence > 0 && <p className="fail">Evidence実体未収集: covered {release.coverage.unresolvedCoveredEvidence}件</p>}{item.depthReference && <p className="depth-card"><strong>FE Depth: {item.depthReference.summary.satisfied}/{item.depthReference.summary.axes} satisfied</strong> · {item.depthReference.summary.partial} partial · status {item.depthReference.status}</p>}</div></> : <div className="no-release"><strong>固定Releaseなし</strong><span>Manifest / Evidence / Certificate 未収集</span></div>}
    <p className={`dependency-card ${item.evidenceDependency.status==='current'?'pass':'fail'}`}><strong>Evidence Dependency: {item.evidenceDependency.status}</strong><span>Core Gate: {item.evidenceDependency.coreGate.result}</span></p>
    {item.fixedCommitAudit.availability==='available'?<p className="dependency-card fail"><strong>固定commit監査: incomplete / Release未成立</strong><span><code>{item.fixedCommitAudit.source.commit.slice(0,12)}</code> · open required {item.fixedCommitAudit.manifest.openRequired} · Gap {item.fixedCommitAudit.gapCount}種</span></p>:<p className="dependency-card fail"><strong>固定commit監査: input missing / 未評価</strong><span>Core Gate: not-run · Gap {item.fixedCommitAudit.gapIds[0]}</span></p>}
    <p className={`definitive-card ${item.definitiveV2.status==='subject-definitive'?'pass':'fail'}`}><strong>Definitive v2: {item.definitiveV2.status}</strong><span>Core Gate: {item.definitiveV2.coreGate.result}</span></p>
    <div className="card-footer"><span>{item.stage1_required ? 'Stage 1 必須' : 'Seed / 任意'}</span><button type="button" onClick={() => onOpen(item)}>検証情報を見る <span aria-hidden="true">→</span></button></div></article>;
}

function SubjectDetail({ subject, close }: { subject:Subject; close:()=>void }) {
  const release = subject.release; const counts = coverageCounts(release);
  const [detail, setDetail] = useState<ReleaseDetail | null>(null);
  const [detailError, setDetailError] = useState(false);
  const [fixedAuditDetail,setFixedAuditDetail]=useState<FixedCommitAudit|null>(null);
  const [fixedAuditError,setFixedAuditError]=useState(false);
  useEffect(() => {
    if (!release) return;
    let active=true;
    fetch(release.detailUrl).then((response)=>{if(!response.ok)throw new Error('detail unavailable');return response.json();}).then((value)=>{if(active)setDetail({ evidence:value.evidence??[], targets:value.targets??[], depthReference:value.depthReference??null });}).catch(()=>{if(active)setDetailError(true);});
    return ()=>{active=false;};
  },[release,subject.id]);
  useEffect(()=>{const audit=subject.fixedCommitAudit as FixedCommitAuditIndex;if(audit.availability!=='available')return;let active=true;fetch(audit.detailUrl).then((response)=>{if(!response.ok)throw new Error('fixed audit detail unavailable');return response.json();}).then((value)=>{if(active)setFixedAuditDetail(value);}).catch(()=>{if(active)setFixedAuditError(true);});return()=>{active=false;};},[subject.fixedCommitAudit]);
  const gaps = detail?.targets.filter((target) => target.state !== 'covered') ?? [];
  return <div className="detail"><header><div><p className="eyebrow">{subject.domain.title} / {subject.id}</p><h2 id="detail-title">{subject.title}</h2></div><button className="close" type="button" onClick={close} aria-label="詳細を閉じる">×</button></header><section><h3>Catalog境界</h3><p>{subject.scope}</p><ul>{subject.excludes.map((item) => <li key={item}>{item}</li>)}</ul></section><DefinitiveV2View definitive={subject.definitiveV2 as DefinitiveV2Index} />{fixedAuditDetail?<FixedCommitAuditView audit={fixedAuditDetail}/>:subject.fixedCommitAudit.availability==='available'?<section className="detail-warning"><h3>固定commit監査詳細</h3><p className="fail" role={fixedAuditError?'alert':'status'}>{fixedAuditError?'監査詳細を読み込めません。Indexのincomplete / Release未成立状態を維持します。':'固定Core GateとGap詳細を読み込み中…'}</p></section>:<section className="detail-warning"><h3>固定commit監査入力はありません</h3><p className="fail"><code>{subject.fixedCommitAudit.status}</code> — 固定clean commitまたは署名済みReleaseの監査入力がないため、Core Gateはnot-runです。未評価をincompleteや完成へ読み替えません。</p><p><code>{subject.fixedCommitAudit.gapIds[0]}</code> / <code>readOnly={String(subject.fixedCommitAudit.readOnly)}</code> / <code>autoPromotion={String(subject.fixedCommitAudit.autoPromotion)}</code></p></section>}
    {!release ? <section className="detail-warning"><h3>固定Releaseはありません</h3><p>Catalogには存在しますが、Manifest、Mastery、Evidence、Skill、Certificateを検証できません。完成済みとしてRouteしません。</p></section> : <>
      <section><h3>固定Releaseと信頼</h3><dl><div><dt>Version / 状態</dt><dd><code>{release.version}</code><span>{completionLabel(release)}</span><span>Manifest status: <code>{release.status}</code></span></dd></div><div><dt>URI</dt><dd><code>{release.uri}</code></dd></div><div><dt>Release digest</dt><dd><code>{release.digest}</code></dd></div><div><dt>署名</dt><dd>{release.signature.algorithm} / <code>{release.signature.keyId}</code>（{release.trust.usage}）</dd></div><div><dt>Authority Lock</dt><dd><code>{release.authorityLockDigest}</code><span>Authority-derived inventory closure: Core v2契約確定 / Subject v2入力で未評価</span></dd></div><div><dt>Publication</dt>{release.completion.definitive ? <dd className="pass">公開Trust Key・v2 Definitive Certificate検証済み</dd> : release.completion.classification === 'bounded-historical' ? <dd><span>v1 Certificate検証済み — bounded historical</span><code>{release.certificateVerification.digest}</code><span className="fail">Subject Definitive未認定</span></dd> : <dd className="fail">Subject Definitive未証明 — 自動昇格しません</dd>}</div></dl></section>
      <section><h3>固定Release履歴</h3><ul className="history-list">{subject.releaseHistory.map((item) => <li key={item.digest}><code>{item.version}</code><span>{completionLabel(item)}</span><span>Epoch {item.completion.coverageEpoch}</span><code>{item.digest}</code><span>{item.certificateVerification.present ? `Certificate: ${item.certificateVerification.status}` : 'Certificateなし / unclassifiedまたは未完了'}</span><a href={item.detailUrl}>Target・Evidenceの固定詳細JSON</a></li>)}</ul><p>旧Release、Target、Evidenceはcurrent Releaseへの集約で削除せず、Digest固定の履歴として残します。</p></section>
      {detail?.depthReference && <DepthReferenceView reference={detail.depthReference} />}
      <section><h3>Mastery</h3><p className="token-list">{release.audiences.map((item) => <span key={item}>{audienceLabels[item] ?? item}</span>)}</p><p className="token-list">{release.outcomes.map((item) => <span key={item}>{outcomeLabels[item] ?? item}</span>)}</p><p className="token-list">{release.surfaces.map((item) => <span key={item.id}>{surfaceLabels[item.id] ?? item.id}{item.applicability === 'not-applicable' ? '（非適用）' : ''}</span>)}</p></section>
      <section><h3>Coverage状態</h3><div className="state-grid">{Object.entries(counts).map(([state,count]) => <div key={state}><strong>{count}</strong><span>{stateLabels[state] ?? state}<code>{state}</code></span></div>)}</div>{detail && (gaps.length ? <ul className="gap-list">{gaps.map((target) => <li key={target.id}><span className={`status target-${target.state}`}>{stateLabels[target.state] ?? target.state}</span><strong>{target.title}</strong><code>{target.id}</code><p>{target.rationale}</p>{target.exclusion && <p><b>理由:</b> {target.exclusion.reason} <b>再評価日:</b> {target.exclusion.reviewed_at}</p>}</li>)}</ul> : <p>このv1 bundleのTarget Gapは0件です。ただしAuthority-derived inventory closureを証明しないため、Subject Definitive完成には昇格しません。</p>)}</section>
      <section><h3>Evidence / Runtime環境</h3><p>{release.evidenceCount} Evidence records — 集約や上限切捨てを行わず全件表示します。</p><dl><div><dt>宣言Required Profile</dt><dd>{release.requiredProfiles.length ? release.requiredProfiles.join(', ') : 'なし'}</dd></div><div><dt>Evidence観測Profile</dt><dd>{release.observedProfiles.length ? release.observedProfiles.join(', ') : '観測Evidenceなし'}</dd></div><div><dt>v2実Runtime Profile</dt><dd>{subject.definitiveV2.runtimeProfiles.length ? subject.definitiveV2.runtimeProfiles.map((item:{profile?:string;id?:string;status:string})=>`${item.profile??item.id??'unknown'} (${item.status})`).join(', ') : 'v2 verified Runtime Profileなし'}</dd></div></dl>{detailError ? <p className="fail" role="alert">Evidence詳細を読み込めません。概要Indexをlast-known-goodとして表示しています。</p> : detail === null ? <p role="status">Evidence詳細を読み込み中…</p> : <ul className="evidence-list">{detail.evidence.map((item) => <li key={item.id}><span className={`verdict verdict-${item.verdict}`}>{item.verdict}</span><code>{item.id}</code><span>{item.kind} / {item.environment.profile}</span></li>)}</ul>}</section>
      <section><h3>Router Skill</h3><dl><div><dt>Router</dt><dd><code>{release.skill.router.id}</code></dd></div><div><dt>固定先</dt><dd><code>{release.skill.atlas_release}</code></dd></div><div><dt>Adapters</dt><dd>{release.skill.adapters.join(', ')}</dd></div><div><dt>Eval threshold</dt><dd>{Math.round(release.skill.evals.minimum_pass_rate*100)}%</dd></div></dl></section>
    </>}
  </div>;
}

function FixedCommitAuditView({ audit }: { audit:FixedCommitAudit }) {
  const body=audit.core.authorityBody.summary as {candidateAnchors?:number;classified?:number;unclassified?:number;humanReviewed?:number};const review=audit.core.authorityReview.summary as {pendingHuman?:number;decisions?:number};const dependency=audit.core.evidenceDependency.summary as {inputs?:number;outputs?:number;runs?:number;missingRequiredOutputs?:number};const definitive=audit.core.definitive.summary as {completionClass?:string;declaredCompletionClass?:string;openRequired?:number};const gateRows=[['Evidence Dependency',audit.core.evidenceDependency],['Authority extraction',audit.core.authorityExtraction],['Authority body',audit.core.authorityBody],['Authority review',audit.core.authorityReview],['Definitive',audit.core.definitive],['Scenario trace',audit.core.scenarioTrace],['Non-regression',audit.core.nonRegression],['Evidence durability',audit.core.evidenceDurability]].filter((row):row is [string,FixedCommitGate]=>Boolean(row[1]));
  return <section className="definitive-detail" aria-labelledby={`fixed-commit-audit-${audit.subjectId}`}><p className="eyebrow">実Subject固定commit監査 / read-only</p><h3 id={`fixed-commit-audit-${audit.subjectId}`}>固定Evidenceはあるが、署名済みReleaseではない。</h3><p className="detail-warning"><strong>{audit.status}</strong> — working treeやDefault Branchを読まず、Git object <code>{audit.source.commit}</code>を監査した結果です。Release、Certificate、Subject Definitiveへ自動昇格しません。</p><dl><div><dt>Repository / tree</dt><dd><code>{audit.source.repository}@{audit.source.commit}</code><code>{audit.source.tree}</code></dd></div><div><dt>Portal attestation</dt><dd><code>{audit.source.attestationDigest}</code><span>{audit.source.trust.usage} / observation-only</span></dd></div><div><dt>Release boundary</dt><dd><code>{audit.releaseBoundary.status}</code><span>signed manifest={String(audit.releaseBoundary.signedManifest)} / public trust={String(audit.releaseBoundary.publicTrustKey)} / definitive certificate={String(audit.releaseBoundary.definitiveCertificate)}</span></dd></div><div><dt>bounded Audit</dt><dd><code>{audit.manifest.status}</code><span>{audit.manifest.targets} targets / bounded open required {audit.manifest.openRequired} / {audit.manifest.evidence} evidence</span></dd></div><div><dt>Definitive inventory</dt><dd className="fail">open required {definitive.openRequired??'未評価'}<span>bounded open required 0でもSubject Definitive完成ではありません。</span></dd></div><div><dt>Core Evidence Dependency</dt><dd className={audit.core.evidenceDependency.result==='pass'?'pass':'fail'}>{audit.core.evidenceDependency.result}<span>{dependency.inputs??0} inputs / {dependency.outputs??0} outputs / {dependency.runs??0} runs / missing required output {dependency.missingRequiredOutputs??0}</span></dd></div><div><dt>Core Definitive</dt><dd className="fail">{audit.core.definitive.result}<span>{definitive.declaredCompletionClass?`自己宣言 ${definitive.declaredCompletionClass} / Core判定 ${definitive.completionClass??'not-definitive'}。`:''}{(audit.core.definitive.diagnostics??[]).join(' / ')}</span></dd></div><div><dt>Authority denominator</dt><dd>{body.candidateAnchors??0} anchors / {body.unclassified??0} unclassified / {body.humanReviewed??0} reviewed<span>{review.pendingHuman??0} pending / {review.decisions??0} decisions</span></dd></div></dl><h4>固定Gate結果</h4><ul className="definitive-gap-list">{gateRows.map(([label,gate])=><li key={label}><code>{label}</code><strong className={gate.result==='pass'?'pass':'fail'}>{gate.result}</strong><span><code>{gate.command}</code>{gate.diagnostics?.join(' / ')||'diagnosticなし'}</span></li>)}</ul>{audit.depthReference&&<><h4>Subject Depth Reference: 18軸の状態・分母・Proof・Gap</h4><p className="detail-warning"><strong>{audit.depthReference.status}</strong> — {audit.depthReference.summary.satisfied} satisfied / {audit.depthReference.summary.partial} partial / {audit.depthReference.summary.missing} missing。Testや集約実行件数を完成へ読み替えません。</p><dl><div><dt>固定入力</dt><dd><code>{audit.depthReference.sourcePath}</code></dd></div><div><dt>Authority-derived denominator</dt><dd>{audit.depthReference.denominatorPolicy.source}<span>required atomic items {audit.depthReference.denominatorPolicy.requiredAtomicItems} / frontend count transplant={String(audit.depthReference.denominatorPolicy.transplantFrontendCounts)}</span></dd></div></dl><ol className="depth-axis-list">{audit.depthReference.axes.map((axis)=><li key={axis.id}><header><span className={`status depth-${axis.status}`}>{axis.status}</span><code>{axis.id}</code></header><dl><div><dt>分母</dt><dd>{axis.denominator}</dd></div><div><dt>Proof粒度</dt><dd>{axis.proofGranularity}</dd></div></dl><h5>Proof</h5><p>{axis.evidencePaths.length?axis.evidencePaths.map((evidence)=><code key={evidence}>{evidence}</code>):'固定Proofなし'}</p><h5>Gap</h5>{axis.gaps.length?<ul className="axis-gap-list">{axis.gaps.map((gap)=><li key={gap}>{gap}</li>)}</ul>:<p>固定入力上のGapなし</p>}</li>)}</ol></>}<h4>固定commitの既知Gap</h4><ul className="definitive-gap-list">{audit.gaps.map((gap)=><li key={gap.id}><code>{gap.id}</code><strong>{gap.count}</strong><span>{gap.detail}</span></li>)}</ul><p><code>readOnly={String(audit.readOnly)}</code> / <code>autoPromotion={String(audit.autoPromotion)}</code>。固定commit監査はRelease入力欠落を埋めません。</p></section>;
}

function DepthReferenceView({ reference }: { reference:DepthReference }) {
  return <section className="depth-reference" aria-labelledby="depth-reference-title"><p className="eyebrow">Subject別 Depth Reference / fail closed</p><h3 id="depth-reference-title">FE Depth Reference: 18軸の状態・分母・Proof・Gap</h3><div className="depth-summary" aria-label="Depth Reference集計"><div><strong>{reference.summary.axes}</strong><span>全軸</span></div><div><strong>{reference.summary.satisfied}</strong><span>satisfied</span></div><div><strong>{reference.summary.partial}</strong><span>partial</span></div><div><strong>{reference.summary.missing}</strong><span>missing</span></div></div><p className="detail-warning"><strong>状態: {reference.status}</strong> — boundedでもSubject Definitiveでもありません。{reference.observedDensity.lockedE2ETests}/{reference.observedDensity.lockedE2ETests}などのTest成功は各軸のProofであり、完成判定へ読み替えません。</p><dl><div><dt>正本</dt><dd><code>{reference.source.repository}@{reference.source.commit}</code><code>{reference.source.path}</code></dd></div><div><dt>Source digest</dt><dd><code>{reference.source.digest}</code></dd></div><div><dt>分母Policy</dt><dd>{reference.denominatorPolicy.source}<span>{reference.denominatorPolicy.note}</span></dd></div><div><dt>Completion claim</dt><dd><code>{reference.completionClaim}</code><span>bounded={String(reference.completion.bounded)} / definitive={String(reference.completion.definitive)}</span></dd></div></dl><ol className="depth-axis-list">{reference.axes.map((axis)=><li key={axis.id}><header><span className={`status depth-${axis.status}`}>{axis.status}</span><div><strong>{axis.title}</strong><code>{axis.id}</code></div></header><dl><div><dt>分母</dt><dd>{axis.denominator}</dd></div><div><dt>判定条件</dt><dd>{axis.portableCriterion}</dd></div></dl><h4>Proof</h4><ul className="proof-list">{axis.checks.map((check)=><li key={check.id}><span className={`verdict verdict-${check.status}`}>{check.status}</span><code>{check.id}</code><p>{check.required}</p><p><b>観測:</b> <code>{typeof check.observed === 'object' ? JSON.stringify(check.observed) : String(check.observed)}</code></p><p><b>Evidence:</b> {check.evidence.map((item)=><code key={item}>{item}</code>)}</p></li>)}</ul><h4>Gap</h4>{axis.gaps.length ? <ul className="axis-gap-list">{axis.gaps.map((gap)=><li key={gap}>{gap}</li>)}</ul> : <p>正本上のGapなし</p>}</li>)}</ol></section>;
}

function DefinitiveV2View({ definitive }: { definitive:DefinitiveV2Index }) {
  const inventory=definitive.inventoryClosure;
  return <section className="definitive-detail" aria-labelledby={`definitive-detail-${definitive.subjectId}`}><p className="eyebrow">Core Definitive Gate v2 / read-only</p><h3 id={`definitive-detail-${definitive.subjectId}`}>bounded-completeとSubject Definitiveを分離</h3><p className={definitive.status==='subject-definitive'?'pass':'detail-warning'}><strong>{definitive.status}</strong> — Core Gate: <code>{definitive.coreGate.result}</code>。v1 CertificateやTest件数から自動昇格しません。</p><dl><div><dt>Core正式main</dt><dd><code>{definitive.coreContract.commit}</code></dd></div><div><dt>Inventory closure</dt><dd><code>{inventory.status}</code><span>required {inventory.required??'未評価'} / classified {inventory.classified??'未評価'} / unclassified {inventory.unclassified??'未評価'} / open required {inventory.openRequired??'未評価'}</span><span>excluded {inventory.excluded} / infeasible {inventory.infeasible}</span></dd></div><div><dt>Migration</dt><dd><code>{definitive.migration.status}</code><span>{definitive.migration.requiredActions.length?definitive.migration.requiredActions.join(' / '):'Subject v2 migration入力なし'}</span></dd></div><div><dt>Certificate</dt><dd>{definitive.certificate?<><code>schema {definitive.certificate.schemaVersion}</code><span>{definitive.certificate.completionClass} / {definitive.certificate.trust.usage}</span></>:'v2 Definitive Certificateなし'}</dd></div></dl><h4>既知Gap</h4><ul className="definitive-gap-list">{definitive.gapIds.map((gap)=><li key={gap}><code>{gap}</code></li>)}</ul><p><code>readOnly={String(definitive.readOnly)}</code> / <code>autoPromotion={String(definitive.autoPromotion)}</code></p></section>;
}

function DefinitiveV2Workspace({ subjects, summary }: { subjects:{id:string;title:string;definitive:DefinitiveV2Index}[];summary:DefinitiveV2Summary }) {
  const [subjectId,setSubjectId]=useState(subjects[0]?.id??'');
  const selected=subjects.find((item)=>item.id===subjectId)??subjects[0];
  const definitive=selected?.definitive;
  const definitiveCount=subjects.filter((item)=>item.definitive.status==='subject-definitive').length;
  const incomplete=subjects.filter((item)=>item.definitive.status==='subject-definitive-incomplete').length;
  const missing=subjects.filter((item)=>item.definitive.status==='subject-definitive-input-missing').length;
  if(!definitive)return <section className="definitive-workspace" id="definitive-v2"><h2>Core Definitive Gate v2</h2><p>Subject Indexがありません。</p></section>;
  const inventory=definitive.inventoryClosure;
  return <section className="definitive-workspace" id="definitive-v2" aria-labelledby="definitive-v2-title">
    <div className="definitive-heading"><div><p className="eyebrow">Core Definitive Gate v2 / fail closed</p><h2 id="definitive-v2-title">履歴上のClosureと、現在の完成を混同しない。</h2></div><p>Core正式mainの確定Schema・Migration・Gate結果を固定Digestで検証するread-only表示です。署名済みSubject bundle、公開Trust、Gate passが揃わないSubjectは未完成のままです。</p></div>
    <div className="definitive-summary" aria-label="Definitive v2集計"><div><strong>{subjects.length}</strong><span>Subject</span></div><div><strong>{definitiveCount}</strong><span>subject-definitive</span></div><div><strong>{incomplete}</strong><span>Gate未通過</span></div><div><strong>{missing}</strong><span>固定入力なし</span></div><div><strong>{summary.inventoryUnevaluated}</strong><span>Inventory未評価</span></div><div><strong>{summary.openRequiredKnown}</strong><span>既知open required</span></div><div><strong>{summary.excluded}</strong><span>excluded</span></div><div><strong>{summary.infeasible}</strong><span>infeasible</span></div><div><strong>{summary.runtimeProfilesUnverified}</strong><span>Runtime未検証</span></div><div><strong>{summary.runtimeProfilesCurrent}</strong><span>Runtime current</span></div><div><strong>{summary.gapInstances}</strong><span>既知Gap instance</span></div></div>
    <p className="definitive-warning"><strong>非昇格:</strong> これらは達成件数ではなく、欠落・分類・検証状態の集約です。bounded-complete / bounded historical、Manifest <code>complete</code>、Test成功件数だけではSubject Definitiveではありません。既知Gap、excluded、infeasible、unclassified、open requiredを隠しません。</p>
    <div className="definitive-gap-summary"><h3>全SubjectのGap内訳</h3><ul>{summary.gapCounts.map((gap)=><li key={gap.id}><code>{gap.id}</code><strong>{gap.count}</strong><span>Subject</span></li>)}</ul></div>
    <label className="dependency-select">Subject<select value={subjectId} onChange={(event)=>setSubjectId(event.target.value)}>{subjects.map((item)=><option key={item.id} value={item.id}>{item.title} · {item.definitive.status}</option>)}</select></label>
    <div className="definitive-gate"><span className={`status ${definitive.status==='subject-definitive'?'release-definitive':'release-incomplete'}`}>{definitive.status}</span><dl><div><dt>Core正式main</dt><dd><code>{definitive.coreContract.commit}</code></dd></div><div><dt>Gate command</dt><dd><code>{definitive.coreGate.command}</code></dd></div><div><dt>Gate result</dt><dd className={definitive.coreGate.result==='pass'?'pass':'fail'}>{definitive.coreGate.result}</dd></div><div><dt>Certificate</dt><dd>{definitive.certificate?<><code>schema {definitive.certificate.schemaVersion}</code><span>{definitive.certificate.completionClass} / {definitive.certificate.trust.usage}</span></>:'署名済みv2 Certificateなし'}</dd></div></dl></div>
    <div className="definitive-grid"><section><h3>Authority-derived inventory closure</h3><dl><div><dt>Status</dt><dd>{inventory.status}</dd></div><div><dt>Required / classified</dt><dd>{inventory.required??'未評価'} / {inventory.classified??'未評価'}</dd></div><div><dt>Unclassified</dt><dd>{inventory.unclassified??'未評価'}</dd></div><div><dt>Open required</dt><dd>{inventory.openRequired??'未評価'}</dd></div><div><dt>Excluded / infeasible</dt><dd>{inventory.excluded} / {inventory.infeasible}</dd></div></dl></section><section><h3>実Runtime Profile</h3>{definitive.runtimeProfiles.length?<ul>{definitive.runtimeProfiles.map((profile,index)=><li key={`${profile.id??profile.profile??'profile'}-${index}`}><code>{profile.profile??profile.id??'unknown'}</code><span>{profile.status}</span><small>identity <code>{profile.runtimeIdentity?JSON.stringify(profile.runtimeIdentity):'v2未検証'}</code></small></li>)}</ul>:<p>v2 verified Runtime Profileなし。Evidence観測Profileをv2実Runtime identityへ読み替えません。</p>}</section></div>
    <div className="definitive-grid"><section><h3>Migration actions</h3>{definitive.migration.requiredActions.length?<ul>{definitive.migration.requiredActions.map((action)=><li key={action}><code>{action}</code></li>)}</ul>:<p>Subject v2 migration入力なし。</p>}</section><section><h3>既知Gap</h3>{definitive.gapIds.length?<ul>{definitive.gapIds.map((gap)=><li key={gap}><code>{gap}</code></li>)}</ul>:<p>Core Gate検証上のGapなし。</p>}</section></div>
    <p className="definitive-contract"><code>readOnly={String(definitive.readOnly)}</code> / <code>autoPromotion={String(definitive.autoPromotion)}</code>。Portalは書込みも自動昇格も行いません。digest変更だけを復旧済みとは表示せず、Core Gate結果を正本にします。</p>
  </section>;
}

function AuthorityReviewWorkspace({ subjects }: { subjects:{id:string;title:string;review:AuthorityReviewIndex}[] }) {
  const [subjectId,setSubjectId]=useState(subjects[0]?.id??'');
  const [reviewExport,setReviewExport]=useState<AuthorityReviewExport|null>(null);
  const [packetId,setPacketId]=useState('');
  const [packet,setPacket]=useState<ReviewPacket|null>(null);
  const [loadError,setLoadError]=useState(false);
  const selectedSubject=subjects.find((item)=>item.id===subjectId)??subjects[0];
  const review=selectedSubject?.review;
  const fullReview=reviewExport?.atlas_id===review?.atlasId?reviewExport:null;
  const effectivePacketId=fullReview?.packets.some((item)=>item.id===packetId)?packetId:(fullReview?.packets[0]?.id??'');
  useEffect(()=>{if(!review)return;let active=true;fetch(review.exportUrl).then((response)=>{if(!response.ok)throw new Error('export unavailable');return response.json();}).then((value)=>{if(active){setReviewExport(value);setLoadError(false);}}).catch(()=>{if(active){setReviewExport(null);setLoadError(true);}});return()=>{active=false}},[review]);
  useEffect(()=>{if(!effectivePacketId||!fullReview||!review)return;let active=true;fetch(`/data/authority-reviews/${review.subjectId}/packets/${effectivePacketId}.json`).then((response)=>{if(!response.ok)throw new Error('packet unavailable');return response.json();}).then((value)=>{if(active){setPacket(value);setLoadError(false);}}).catch(()=>{if(active){setPacket(null);setLoadError(true);}});return()=>{active=false}},[effectivePacketId,fullReview,review]);
  if(!review)return <section className="review-workspace" id="authority-review"><h2>Authority Human Review</h2><p>固定read-only exportはありません。</p></section>;
  const counts=review.summary;
  const proposals=packet&&fullReview?fullReview.proposed_clusters.filter((item)=>packet.proposed_cluster_ids.includes(item.id)):[];
  return <section className="review-workspace" id="authority-review" aria-labelledby="authority-review-title">
    <div className="review-heading"><div><p className="eyebrow">Authority Human Review / Subject横断</p><h2 id="authority-review-title">固定Exportから一次資料へ進む。</h2></div><p>Portalはread-only exportを表示し、本文を複製しません。URL＋locator、固定digest、未review projection、機械proposalをHuman decisionから分離します。</p></div>
    <div className="review-summary" aria-label="Authority review集計"><div><strong>{counts.packets}</strong><span>packet / deep-link</span></div><div><strong>{counts.candidate_domain_projections}</strong><span>projection</span></div><div><strong>{counts.proposed_clusters}</strong><span>machine proposal</span></div><div><strong>{counts.pending_human}</strong><span>pending</span></div><div><strong>{counts.human_reviewed}</strong><span>reviewed</span></div><div><strong>{counts.stale_document_holds}</strong><span>stale hold</span></div></div>
    {!counts.has_human_progress&&<p className="review-zero" role="status"><strong>Human review進捗なし:</strong> human decision 0件を進捗として扱いません。80件はpendingのままです。機械proposal 113件もreviewedへ算入しません。</p>}
    <div className="action-ledger" aria-label="Decision状態"><span>include 0</span><span>exclude 0</span><span>merge 0</span><span>split 0</span><span>defer 0（reviewed非算入）</span></div>
    <div className="review-filters"><label>Subject<select value={subjectId} onChange={(event)=>{setSubjectId(event.target.value);setReviewExport(null);setPacketId('');setPacket(null);setLoadError(false)}}>{subjects.map((item)=><option key={item.id} value={item.id}>{item.title}</option>)}</select></label><label>Priority<select value="0" disabled aria-describedby="priority-note"><option value="0">P0 / 固定Export 80件</option></select><span id="priority-note">正本Exportが選定したPriority 0のみ</span></label><label>Packet<select value={effectivePacketId} onChange={(event)=>{setPacketId(event.target.value);setPacket(null);setLoadError(false)}}>{(fullReview?.packets??[]).map((item)=><option key={item.id} value={item.id}>{item.id} · {item.candidate_edges} projection</option>)}</select></label></div>
    <p className="review-batch-note">Batch: <code>priority-0.snapshot</code> / export・2 Schema・packet digestを固定検証。Default BranchやSubject Source Treeを参照しません。</p>
    <div className="review-grid"><div><h3>Review packet</h3>{loadError?<p className="fail" role="alert">Packetを読み込めません。固定概要をlast-known-goodとして表示します。</p>:packet===null||packet.packet_id!==effectivePacketId?<p role="status">Packetを読み込み中…</p>:<article className="review-packet"><div className="packet-status"><span className="status depth-missing">pending-human</span><span>P{packet.priority}</span><span>read-only</span><span>Human decision: なし</span></div><h4><code>{packet.source_binding.anchor_id}</code></h4><a href={packet.deep_link.url} target="_blank" rel="noopener noreferrer">一次資料をURL＋locatorで開く ↗</a><dl><div><dt>URL</dt><dd>{packet.source_binding.document_url}</dd></div><div><dt>locator</dt><dd><code>{packet.source_binding.locator}</code></dd></div><div><dt>context digest</dt><dd><code>{packet.source_binding.context_digest}</code></dd></div><div><dt>source digest</dt><dd><code>{packet.source_binding.locked_source_digest}</code></dd></div></dl><h4>Candidate domain projection</h4><p>すべて <code>domain-contract-projection-unreviewed</code>。分類候補であり、人の決定ではありません。</p><ul className="projection-list">{packet.candidate_domain_projections.map((item)=><li key={item.edge_id}><span className="machine-label">未review projection</span><code>{item.pattern_id}</code><span>{item.pattern_kind}</span><a href={item.reference_url} target="_blank" rel="noopener noreferrer">参照URL ↗</a><span>Target <code>{item.target_id}</code></span></li>)}</ul><h4>Machine proposal</h4>{proposals.length?<ul className="proposal-list">{proposals.map((item)=><li key={item.id}><span className="machine-label">機械proposal / Human decisionではない</span><code>{item.id}</code><span>{item.proposal_type} · {item.basis_value}</span><span>{item.candidate_edge_ids.length} candidate edge</span></li>)}</ul>:<p>このpacketに機械proposalはありません。</p>}<h4>Human review prompt</h4><ul>{packet.review_prompts.map((item)=><li key={item.id}>{item.prompt_ja}</li>)}</ul></article>}
      <h3>Stale relock hold</h3><p>選択前の候補です。read-only holdのためDecision対象にできません。</p><ul className="stale-list">{(fullReview?.stale_holds??[]).map((hold)=><li key={hold.document_id}><span className="status depth-missing">read-only stale hold</span><a href={hold.document_url} target="_blank" rel="noopener noreferrer">{hold.document_url} ↗</a><code>{hold.reason}</code><span>locked <code>{hold.locked_source_digest}</code></span><span>fetched <code>{hold.fetched_digest}</code></span><button type="button" disabled>relock未選択</button></li>)}</ul></div>
      <aside className="decision-form" aria-labelledby="decision-boundary-title"><h3 id="decision-boundary-title">Decision書込み境界</h3><p><code>write_decisions=false</code>。このPortalはCandidate JSONもDecisionも保存・送信しません。将来の書込みはCore共通APIと共通Schemaへ分離します。</p><div className="disabled-actions" aria-label="無効なDecision操作">{['include','exclude','merge','split','defer'].map((item)=><button key={item} type="button" disabled>{item}</button>)}</div><p className="fail"><strong>操作を拒否:</strong> Core共通API未接続です。reviewer、time、reason、manual-primary-source、source/tool/context digest、old-to-new mappingが全て揃わない操作もfail-closedで拒否します。</p><dl className="review-contract"><div><dt>Export mode</dt><dd><code>{review.mode}</code></dd></div><div><dt>Status</dt><dd>{review.status}</dd></div><div><dt>Human reviewed</dt><dd>{counts.human_reviewed}</dd></div><div><dt>Machine proposals</dt><dd>{counts.proposed_clusters}（decisionではない）</dd></div><div><dt>Source commit</dt><dd><code>{review.source.commit}</code></dd></div><div><dt>Export digest</dt><dd><code>{review.source.exportDigest}</code></dd></div></dl></aside></div>
  </section>;
}

function EvidenceDependencyWorkspace({ subjects, coreCommit }: { subjects:{id:string;title:string;dependency:EvidenceDependencyIndex}[]; coreCommit:string }) {
  const [subjectId,setSubjectId]=useState(subjects[0]?.id??'');
  const [detail,setDetail]=useState<EvidenceDependencyDetail|null>(null);
  const [loadError,setLoadError]=useState(false);
  const selected=subjects.find((item)=>item.id===subjectId)??subjects[0];
  const dependency=selected?.dependency;
  useEffect(()=>{
    if(!dependency?.detailUrl)return;
    let active=true;
    fetch(dependency.detailUrl).then((response)=>{if(!response.ok)throw new Error('dependency detail unavailable');return response.json();}).then((value)=>{if(active){setDetail(value);setLoadError(false);}}).catch(()=>{if(active){setDetail(null);setLoadError(true);}});
    return()=>{active=false};
  },[dependency]);
  const current=subjects.filter((item)=>item.dependency.status==='current').length;
  const stale=subjects.filter((item)=>item.dependency.status==='stale-or-incomplete').length;
  const missing=subjects.filter((item)=>item.dependency.status==='missing-required-output').length;
  const view=detail?.subjectId===subjectId?detail:null;
  if(!dependency)return <section className="dependency-workspace" id="evidence-dependency"><h2>Evidence Dependency Graph</h2><p>Subject Indexはありません。</p></section>;
  const missingOutputs=view?.coreGate.missingRequiredOutputs??dependency.missingRequiredOutputs??[];
  const structures=view?.structures??(dependency.structures??[]).map((item)=>({id:item.id,kind:item.id,path:'未観測',baseline_digest:'未観測',gate:{id:item.id,status:item.status,detail:'Core Gate結果なし'}}));
  return <section className="dependency-workspace" id="evidence-dependency" aria-labelledby="evidence-dependency-title">
    <div className="dependency-heading"><div><p className="eyebrow">Evidence Dependency Graph / read-only</p><h2 id="evidence-dependency-title">入力変化から再実行結果まで、Core Gateの判定を表示する。</h2></div><p>PortalはGraphも状態も書き換えず、自動昇格しません。digest更新だけを「復旧済み」と表示せず、正式mainのCore Gate結果を正本にします。</p></div>
    <div className="dependency-summary" aria-label="Evidence Dependency Graph集計"><div><strong>{subjects.length}</strong><span>Subjects</span></div><div><strong>{current}</strong><span>current / Gate pass</span></div><div><strong>{stale}</strong><span>stale / incomplete</span></div><div><strong>{missing}</strong><span>missing required output</span></div></div>
    <label className="dependency-select">Subject<select value={subjectId} onChange={(event)=>{setSubjectId(event.target.value);setDetail(null);setLoadError(false)}}>{subjects.map((item)=><option key={item.id} value={item.id}>{item.title} — {item.dependency.status}</option>)}</select></label>
    <div className="dependency-gate"><span className={`status ${dependency.status==='current'?'release-definitive':'release-incomplete'}`}>{dependency.status}</span><dl><div><dt>Core正式main / CI成功</dt><dd><code>{coreCommit}</code></dd></div><div><dt>Gate command</dt><dd><code>{dependency.coreGate.command}</code></dd></div><div><dt>Gate result</dt><dd className={dependency.coreGate.result==='passed'?'pass':'fail'}>{dependency.coreGate.result}</dd></div><div><dt>Runtime identity</dt><dd><code>{dependency.coreGate.runtimeIdentity?JSON.stringify(dependency.coreGate.runtimeIdentity):'未観測'}</code></dd></div></dl></div>
    {loadError&&<p className="fail" role="alert">固定Graph詳細を読み込めません。署名検証済み概要をlast-known-goodとして表示します。</p>}
    {dependency.availability==='missing'?<p className="dependency-warning" role="status"><strong>Required output missing:</strong> <code>evidence/dependency-graph.json</code> とCore Gate結果が固定Releaseにありません。Subjectの既存status=incomplete、Human review、Gapはそのまま保持し、完成へ昇格しません。</p>:view===null?<p role="status">固定Graph詳細を読み込み中…</p>:<>
      <div className="dependency-grid"><section><h3>Inputs — changed / current</h3><ul>{view.inputs.map((input)=><li key={input.id}><span className={`status ${input.state==='current'?'release-definitive':'release-incomplete'}`}>{input.state}</span><code>{input.id}</code><span>{input.kind} · {input.members.length} members</span><small>baseline <code>{input.baseline_digest}</code></small><small>current <code>{input.current_digest}</code></small><small>observed <time>{input.observed_at}</time></small></li>)}</ul></section><section><h3>Impacted outputs — stale / current</h3><ul>{view.outputs.map((output)=><li key={output.id}><span className={`status ${output.status==='current'?'release-definitive':'release-incomplete'}`}>{output.status}</span><code>{output.id}</code><span>{output.kind} · {output.path}</span><small>影響input: {output.impacted_by.length?output.impacted_by.join(', '):'なし'}</small>{output.run?<details><summary>Rerun / runtime</summary><dl><div><dt>Command</dt><dd><code>{output.run.command}</code></dd></div><div><dt>Result / attempts</dt><dd>{output.run.result} / {output.run.attempts}</dd></div><div><dt>Runtime identity</dt><dd><code>{output.run.runtime_identity?JSON.stringify(output.run.runtime_identity):'対象外 / 未観測'}</code></dd></div><div><dt>Time</dt><dd>{output.run.started_at} → {output.run.completed_at}</dd></div></dl></details>:<small className="fail">対応するrerun記録なし</small>}</li>)}</ul></section></div>
    </>}
    <div className="dependency-grid"><section><h3>Missing required output</h3>{missingOutputs.length?<ul>{missingOutputs.map((item)=><li key={item}><code>{item}</code></li>)}</ul>:<p>{dependency.coreGate.result==='passed'?'Core Gate上の欠落なし':'Core Gate未実行のため確定不可'}</p>}</section><section><h3>Proof / Closure structure drift</h3><ul>{structures.map((item)=><li key={item.id}><span className={`status ${item.gate.status==='current'?'release-definitive':'release-incomplete'}`}>{item.gate.status}</span><code>{item.id}</code><span>{item.kind}</span><small>{item.gate.detail}</small></li>)}</ul></section></div>
    <p className="dependency-contract"><strong>非昇格契約:</strong> read-only=true / autoPromotion=false。input digestが更新されても、再実行・required output・Proof/Closure構造・runtime identityをCore Gateがpassと判定するまでcurrent/復旧済みとは表示しません。</p>
  </section>;
}

---
name: technology-atlas-router
description: 97 Subject Atlasから、分野・Audience・Outcome・Surface・状態・Version・環境・Skillを使って固定ReleaseとEvidenceを探索・検証する。個別技術の解説生成ではなく、Canonical IndexへのRouteやCoverage Gap確認に使う。
---

# Technology Atlas Router

Portalの生成Indexを検索し、技術知識を複製せず、固定ReleaseのManifest、Coverage、Evidence、Skill Package、Completion Certificateへ案内する。

## Route

1. 問いを`discover | compare | verify | evidence | skill | gap`のModeへ分類する。返却契約が必要なら[Mode一覧](references/modes.md)を読む。
2. `scripts/search.mjs <query>`でCanonical Indexを検索する。分野、Audience、Outcome、Surface、状態、Version、環境、Skillの条件を維持する。
3. 候補のCatalog状態と固定Releaseの有無を先に確認する。Source Tree、Default Branch、浮動URLへRouteしない。
4. Releaseがある場合はURI、Digest、署名、検証状態を確認してからCoverageとEvidenceへ進む。
5. Route可能性と完成判定を必ず分離し、`release.completion`を返す。v1 Certificateは`bounded-historical`としてのみ案内する。
6. Subject Definitive完成を主張する場合は、Core正式main `072d7ca77981f51754e824d70c6d4ecd55ea67e5` の確定Schema/Migration、公開Trust Key、署名済みv2 bundle、固定Release binding、`atlas audit . --gate definitive` passをすべて要求する。入力欠落またはGate未通過は未証明と返す。
7. `evidence/non-regression-report.json`が`pass`であることを確認し、open required、unclassified、bounded historical、非後退違反数を省略しない。
8. `depthReference`があるSubjectでは、18軸を省略せず状態、分母、各CheckのProof、GapへRouteする。Test成功件数はProofとして返し、`depthReference.status`、`completion.bounded`、`completion.definitive`を別々に返す。
9. `definitiveV2`はInventory Closure、unclassified、open required、excluded、infeasible、実Runtime identity、Gap、Migration actionを省略せず返す。`bounded-historical`を`subject-definitive`へ読み替えず、Portalから書込み・自動昇格を行わない。
9. `authorityReview`があるSubjectでは固定read-only exportのpriority、packet、projection、machine proposal、stale hold、pending、reviewedとinclude/exclude/merge/split/defer境界へRouteする。decision 0件は進捗0として返し、URLとlocatorから一次資料を人が確認する導線を示す。machine proposalをHuman decisionと呼ばず、Portal書込みを案内しない。
10. `evidenceDependency`を必ず返し、input changed/current、影響output、stale/current、rerun command/result/runtime identity、missing required output、Proof/Closure structure driftへRouteする。`current`は`reference-atlas-core`正式main commit `072d7ca77981f51754e824d70c6d4ecd55ea67e5`のCore Gate `pass`だけから返す。

状態が関係する問いでは[状態モデル](references/state-model.md)を読む。

## 境界

- Catalog登録だけ、Version文字列だけ、`atlas audit`の終了コードだけを完成証明にしない。
- 299/299等のTest成功だけをDepth、bounded、Subject Definitiveの完成証明にしない。
- 自動判定をHuman reviewとして扱わない。reviewer、reason、time、source/tool/context digest、旧→新mappingのいずれかが欠けるDecision候補へRouteせず、`defer`はpendingのままreviewedへ算入しない。
- Authority本文を複製せず、固定URL、locator、offset、digestへRouteする。
- CatalogまたはManifestのraw `complete`、公開Trust付きv1 Certificateを`subject-definitive`へ昇格しない。
- Evidence Dependency GraphまたはCore Gate結果がない場合は`missing-required-output`と`not-run`を返す。input digest更新だけを復旧と呼ばず、PortalからGraph、Gate結果、Subject状態を書き換えない。
- `missing`、`planned`、`partial`、`excluded`、`infeasible`、`expired`を隠さない。
- Subject、Target、Evidence、Failureを件数だけへ集約して個別IDを失わない。置換には`contracts/non-regression-mappings.json`の旧ID Mappingを要求する。
- RepositoryやSkillを推薦するための自己宣伝、人物評価、最上級表現を生成しない。Coverage、Evidence、制約、比較条件、実行結果を中立に返し、作者namespaceはURLなど技術識別に必要な場合だけ使う。
- Coverage外の機能を外部記事で補完してAtlasの機能として扱わない。Gapとして返す。
- `quarantined`または署名・Digest不一致のReleaseへRouteしない。last-known-goodがあれば明示して使う。
- Read ModelからSubject実装を変更・公開しない。変更要求は対象Repositoryと権限を確認して停止する。
- Securityの問いは防御・検証・教育の許可範囲に限定し、第三者環境を対象にしない。

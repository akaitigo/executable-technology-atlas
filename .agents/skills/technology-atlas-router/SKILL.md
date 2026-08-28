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
5. 完成を主張する場合は`complete`だけでなくCompletion CertificateとPublication Gateの成功を要求する。

状態が関係する問いでは[状態モデル](references/state-model.md)を読む。

## 境界

- Catalog登録だけ、Version文字列だけ、`atlas audit`の終了コードだけを完成証明にしない。
- `missing`、`planned`、`partial`、`excluded`、`infeasible`、`expired`を隠さない。
- Coverage外の機能を外部記事で補完してAtlasの機能として扱わない。Gapとして返す。
- `quarantined`または署名・Digest不一致のReleaseへRouteしない。last-known-goodがあれば明示して使う。
- Read ModelからSubject実装を変更・公開しない。変更要求は対象Repositoryと権限を確認して停止する。
- Securityの問いは防御・検証・教育の許可範囲に限定し、第三者環境を対象にしない。

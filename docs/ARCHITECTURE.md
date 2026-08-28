# Architecture

このPortalは97 Subject AtlasのRead Modelであり、個別技術の説明やSubject実装を所有しない。

```text
signed Catalog release + signed Subject release bundles
  -> Ed25519 / SHA-256
  -> Core JSON Schema + cross-manifest audit
  -> quarantine or verified candidate
  -> atomic generated Index
  -> Japanese search / detail / Router Skill
```

Runtimeは`fixtures/`のcontent-addressed bundleと生成済み`app/data/index.generated.json`だけを読み、Subject Source Tree、Git submodule、Default Branchへ依存しない。`scripts/generate-fixtures.mjs`はfixture更新時に明示された固定checkoutを入力として受ける開発用Exportであり、Runtime取込経路ではない。

現時点で組込Indexが検証できる署名済み公開Releaseは0件である。7件のSubject bundleはtest-only鍵で署名した再現可能fixture候補であり、UI・Indexとも`fixture-only`として完成証明と分離する。

Core v1 Completion Certificateは固定Epochの`bounded-historical`として分類する。Releaseのraw `complete`、v1 Certificate検証、`public-release` Trustだけでは`subject-definitive`へ昇格しない。ReleaseはRepositoryごとの履歴配列とDigest固定の詳細Fileで保持し、current pointerをIndexで明示する。

Core Definitive Gate v2のSchema/Migrationが正本へcommitされるまでは、`completionPolicy.definitiveGate`を`pending-core-v2`としてfail closedにする。確定後の受理条件は[DEFINITIVE_GATE_V2.md](DEFINITIVE_GATE_V2.md)で管理する。

非後退BaselineはSubject、Target、Evidence、FailureをID単位で保持し、生成Indexとは独立した固定契約として扱う。Importer後に`scripts/check-non-regression.mjs`が現行Read ModelとDigest固定詳細を照合し、Publication Gateが結果の再現一致まで検証する。置換は明示Mappingが必要で、件数集約だけでは元のID、理由、環境、Evidenceを代替できない。

公開表示Projectionは署名済み入力を信頼判定の正本として保持しつつ、画面・公開詳細・Portal文書へ自己宣伝や人物評価を複製しない。変換の有無とsource Release Digestを固定詳細へ記録し、Portalが表示する判断材料をCoverage、Evidence、制約、比較条件、実行結果に限定する。

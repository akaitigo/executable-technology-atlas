# Atlas｜来歴policyの前提と原典





同repo `learning/continuations/software-supply-chain/transitive-material-closure/` は受入済みです。READMEとcoverage.json、experiment.py closure:7–18 / run:19–40は到達集合・申告集合・material digestと直接名故障を扱います。古い元LEARNING_PATHの「すべて未実行」を、この推移閉包教材の現在状態へ適用しません。Agentの具体call承認は主体/計画/call/引数の操作許可であり、build来歴のclaimと生成者認証とは別の入口です。

2026-10-06に次の公式本文を実読しました。第三者本文は転載しません。

- [SLSA v1.2 Verifying artifacts](https://slsa.dev/spec/v1.2/verifying-artifacts#step-1-check-slsa-build-level)：Step 1の署名・subject照合とroot of trust。今回の文字列比較はこの手順を実行していません。
- [同 Step 2](https://slsa.dev/spec/v1.2/verifying-artifacts#step-2-check-expectations)：builder/source/buildType/externalParametersの期待照合。未知parameterを区別する根拠。
- [同 Forming Expectations](https://slsa.dev/spec/v1.2/verifying-artifacts#forming-expectations)：期待を決め変更から保護する道筋。今回の別fixture保護は仮定です。
- [SLSA v1.2 Build Provenance](https://slsa.dev/spec/v1.2/build-provenance#builddefinition)：buildTypeはparameterの意味を定める識別子。外部parameterと解決済み依存は別に扱います。

builder_id/source_id/build_typeは説明のための独自短縮field名です。SLSAのrunDetails.builder.id、buildDefinition等をそのまま実装した形式ではありません。既存の内容・baseline・推移閉包は前提へ戻し、再制作や加算をしません。

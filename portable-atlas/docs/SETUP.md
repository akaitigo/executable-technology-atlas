# 配置と隣接repo

このコピーを `executable-technology-atlas/` として置きます。教材ディレクトリはrepo内の相対pathです。絶対ユーザーディレクトリや以前のPID・sessionは引き継ぎません。

元の入口教材7件は別repoにあります。次の配置を参照構造として使います。これらのrepoは本コピーに含めておらず、内容の公開検査も今回の対象外です。

| repoからの相対path | 元の入口 |
|---|---|
| `../frontend-behavior-atlas/learning` | FE |
| `../flutter-reference-atlas/learning/widget-state-lifecycle` | Flutter |
| `../kotlin-reference-atlas/learning/nullability-diagnostics` | Kotlin |
| `../argocd-reference-atlas/learning/reconciliation-drift` | Argo CD |
| `../postgresql-reference-atlas/learning` | PostgreSQL |
| `../rabbitmq-reference-atlas/learning` | RabbitMQ |
| `../zero-trust-reference-atlas/learning` | Zero Trust |

各repoを別途用意してREADMEを読み、必要なSDK・Docker等を確認します。一括clone、インストール、Docker設定の変更は行いません。readerは隣接repoを自動で配信しません。未検査内容を取り込まず、必要なファイルを別途選別してから接続してください。

`ATLAS_ROOT`、`ATLAS_WORKSPACE`、`LOCAL_HOME` は旧絶対pathを除いた説明用記号です。これらを含む実験用scriptは、対象教材で相対pathや環境変数へ移す必要があります。記号を設定するだけで全producerが起動するという意味ではありません。

収録されたテストにも、非同梱の旧原票や旧状態の正確なSHAを要求するものがあります。教材の計算検証と過去の証拠検証を分け、後者を新しい実行結果に置換しないでください。reader全体の軽い検査はREADMEの専用コマンドを使います。

任意のGUI検査sourceは旧端末の隠しdirectoryを参照せず、通常の playwright package を解決します。保存readerや npm test にPlaywrightは不要です。GUI検査の依存install・browser起動・実行は今回行っていません。

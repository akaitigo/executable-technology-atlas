# この配送コピーを別PCへ復元する

必要なのはNode.js 22.13以上と、配送manifestにある全ファイルです。ネットワーク、compiler、Docker、隣接repoは保存readerの起動には不要です。別repoにある入口7件や新しい実験は別の前提です。

1. 配送archiveを使う場合はSHA-256を配送記録と照合します。Gitの場合は移行ブランチをcloneし、公開されたcommit IDとHEADを照合して `portable-atlas/` に入ります。
2. 新しい空の場所へ展開・cloneします。元のrepoや他人の作業directoryへ上書きしません。
3. archiveの展開root、またはGit cloneの `portable-atlas/` で次を実行します。

```sh
node scripts/verify-delivery.mjs
npm test
node scripts/local-learning-preview.mjs
```

最初のコマンドは全配送fileのSHA・サイズ・余分なfile・symlinkを検査します。npm test はNode標準機能だけを使い、パッケージのinstall、API、browserを起動しません。最後のコマンドで表示されたlocalhost URLを、自分でブラウザに開きます。終了はCtrl+Cです。

既定は従来の正式142です。候補6とその他未統合43は別一覧です。このコピーの作成や局所テストで受入数を増やしていません。

ast-stack・threshold-curves・fairness-starvation は、原本から必要な観測と固定期待値を選別した配布用schemaを照合します。WAL stale-reader-upgrade は、保存13条件と内容確認済みのSQLite DB 8個を持ちます。各教材のMIGRATION.mdに、元SHA・必要file・保存再生と新規実験の違いを記載しています。

古い全文原票、未検査画像・binary、機械固有情報は公開配送に含めません。必要な原本の場所とSHAは別の私的保全manifestにあります。公開archiveだけで私的原票・隣接7repo・旧PCの認証やSDKまで復元できるとは主張しません。私的保全物の外部退避は別の配送先・確認が必要です。

局所テストは保存データ、JSの状態変更、読取り境界と配送bytesを対象にしています。ブラウザの描画・実ポインター操作、別PCのnative producerや専用APIは未検証です。

非秘密データを新しく作る場合は [REGENERATION.md](REGENERATION.md) を参照します。過去の画像・実測原票はseedから再生成した結果へ置換しません。

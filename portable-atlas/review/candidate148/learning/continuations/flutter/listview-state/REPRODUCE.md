# 再現手順と実行前の条件

**初回実行を完了しました。** 2026-10-06、最初の資源ゲート停止後に親担当が基準を見直し、Kotlinの実行枠も解放されました。直前readはload 4.77 / 12CPU、idle 67.84%、`memory_pressure -Q`の指標44%、throttled 0でした。この44%を物理RAMの未使用量とは扱いません。全体資源と既知SRE状況から余裕を判断し、compile 1回・tester 1回だけ実行しています。browser・画像readは0回です。[実行前読取](verification/resource-before-attempt-01.json)、[実行原票](probe/observations/attempt-01/run.json)、[自分のPID終了確認](verification/process-cleanup-attempt-01.json)を保存しています。

## 今できる読取確認

[expectations.json](expectations.json)の2条件×5段階を、[Widget](probe/lib/listview_probe.dart)と[観測プログラム](probe/test/native_probe.dart)で照合します。Pythonの構文確認は`ast.parse`を使い、runnerをimportして副作用を起こす必要はありません。今回のDart構文/APIは保存済み3.47.1でcompileできました。別SDK・platformの適合は未確認です。

## 実行前に必要な条件

1. 最新基準による資源確認と、担当間のcompiler/browser実行枠調整ができていること。正規の読取で12CPU全体のCPU/load・空きメモリー・既知SRE処理を確認します。ISU/SREを優先し、DeepSeekUIの固定CPU 0.5 / RAM 768MiBや他プロセスの設定・稼働を変更しません。このrunnerは資源条件の代替判定を行いません。
2. 保存済みFlutter 3.47.1、framework revision `6655482ec06e547f90abf8ae7590466f4415978d`、Dart 3.13.1とローカルpackage cacheが読めること。不足時は停止し、install・download・upgrade・pub getを行わないこと。
3. 書込先をこの教材の`probe/observations/attempt-NN`に限定できること。新しいattemptだけを作り、既存原票や他作者のpathを上書きしないこと。
4. compilerとtesterの各起動前に`os.nice(10)`が成功すること。失敗時は通常優先度で続行しません。権限が必要になった場合は目的・コマンドを具体化して正規reviewを使用し、拒否された経路を迂回しません。

## 読取専用の計画表示

次は将来の利用者向け例です。`FLUTTER_ATLAS`を既存repoのパスに設定し、この教材のディレクトリから実行します。SDK CLIを起動せず、既存metadata・artifactの存在とpackage参照を読みます。**`--execute`なしでは出力ファイルも作らず、compiler/testerも起動しません。**

```sh
python3 probe/run_probe.py \
  --sdk "$FLUTTER_ATLAS/.tools/flutter-3.47.1/flutter" \
  --cached-package-config "$FLUTTER_ATLAS/learning/widget-state-lifecycle/.dart_tool/package_config.json"
```

## 実行枠を確保した後の1 batch

前述の条件を満たした時だけ、次を1回実行します。初回のattempt 1は既に存在するため上書きできません。次の例は将来、再検証の必要が生じた場合のattempt 2です。今回の成功確認のために追加実行する必要はありません。

```sh
python3 probe/run_probe.py \
  --sdk "$FLUTTER_ATLAS/.tools/flutter-3.47.1/flutter" \
  --cached-package-config "$FLUTTER_ATLAS/learning/widget-state-lifecycle/.dart_tool/package_config.json" \
  --attempt 2 --execute
```



## 原票の読み方

attemptには、実行前入力コピー、入力hash、優先度、exit code、所要時間、stdout/stderrと`run.json`が保存されます。engineが観測を開始できた場合は`actual.json`に次を残します。初回は2条件・10段階すべてを保存できました。

- 条件ごとの5段階。現在項目・生成時項目・State識別子・回数・実ElementのText。
- builder呼出indexと回数、callback呼出と返したindex、生成・更新・非活性化・破棄イベント。
- 各段階の固定予測と差分。比較前に実測を保存し、差分があっても可能な範囲で後続を観測。
- 終了時の生存Stateが0になったか。途中失敗・タイムアウト・FlutterErrorも失敗として保持。

`passed=false`やexit 1は無効な原票という意味ではありません。予測不一致を含む失敗の証拠です。境界itemが余分に生成されても、その状態とイベントを捨てずに原因を分けます。初期表を都合よく修正して同じattemptを成功へ変えてはいけません。

## 実測受入と次の工程

初回は2条件×5段階がそろい、State対応・回数・生成/破棄・実Text・cleanupの固定表照合が成立しました。さらに別Pythonチェッカーがproducerの`passed`や予測行を使わず原票の関係を再照合し、163確認が通っています。これは同一作者による別実装の照合です。次の読取コマンドにはcompiler・tester起動はありません。

```sh
python3 probe/verify_observation.py --attempt probe/observations/attempt-01
```

今後不一致が出た場合は記録を維持し、コード不具合・予測不具合・fixture/SDK差を分類します。必要な改訂と再実行は別attemptにします。

保存観測readerは別工程として実装・確認しました。原実Widget検証の`browser0`記録は当時の履歴を保ち、今回のreader操作記録とは混ぜません。FlutterライブGUIのポインター・ドラッグは引き続き未確認です。

## 学習画面を開く

この教材のディレクトリで次を実行し、表示されたloopback URLをブラウザーで開きます。SDKやnodeは教材閲覧には不要です。原票をfetchするため、HTMLをファイルとして直接開く方式にはしません。

```sh
python3 serve.py
```

標準URLは`http://127.0.0.1:18751/`です。既に使われているportを停止せず、必要なら`--port 0`で空きportを選びます。配信対象は教材と固定原票・実行時ソースだけです。SDK/cache設定などは配信しません。終了はCtrl+Cです。

予想を選んで入替後を再生し、対照・原典・答え合わせへ進みます。条件変更は予想も消し、予想変更は新しい予想を残して準備時点へ戻します。原票再読込の開始・失敗では過去の行、対照、答え、ソースを消し、古い値を表示し続けません。

## GUI検証を再現する場合

保存証拠は`ui-qa/run-2026-10-06T061122810Z/`です。16確認・43ポインター操作・9captureが成功し、browser/profile/serverはcleanup済みです。再検証の必要がある時だけ、他担当とのブラウザー枠を調整し、全体資源を確認してから`python3 check_gui.py`を実行します。既存Playwright/Chromiumのみを使い、nice 10が適用できなければ起動しません。専用profile、sandbox有効、loopback以外の通信遮断、終了時cleanupを使います。installや他ブラウザーの停止は行いません。

失敗試験はブラウザー内のHTTP応答だけを差し替えます。原票ファイルを編集しません。遅延2件はAbortControllerを含む実際の経路を検証し、世代番号判定だけを独立に強制した試験とは扱いません。保存画像はreaderの実Chromium captureであり、実Flutter描画ではありません。

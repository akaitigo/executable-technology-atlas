# 再現と実行前の条件

**初回実Widget検証が完了しました。** Kotlinの枠解放後、fresh readでload13.56/12CPU、全体idle45.31%、memory_pressure指標42%、inactive約4.89GiB、throttled0を確認し、nice10の短いbatchを実行しました。単一processの使用率やloadだけで判断していません。[資源read](verification/resource-before-attempt-01.json)を保存しています。予測表は書き換えず、実測を別の原票へ保存しました。

## 実行計画

保存実測を学ぶだけなら、先に次のreaderを使ってください。以下のnative実行計画は新たな観測が必要な場合のものです。

### 保存実測readerを開く

この教材のディレクトリで`python3 serve.py`を実行し、`http://127.0.0.1:18753/`を開きます。loopbackだけに配信し、終了時はCtrl+Cで止めます。SDK/外部サービスは起動しません。

保持要求と予想を選択→遠方の保存実測を再生→先頭へ戻る→原典/実行時ソース→答え合わせの順で使います。状態のカードは実Widget原票を分類したDOMで、Flutter描画ではありません。原票と実行時ソースのdigest照合が必要です。

readerの検証を再現する必要がある場合だけ、共有browser枠とfresh資源確認後に`python3 check_gui.py`を実行します。既存Playwright/Chromium、sandbox有効、専用profile、nice10、1context、短いtimeoutを使用し、外部接続を遮断します。終了時に自分のbrowser/profile/serverだけをcleanupします。初回は[16確認・51操作・11画像](ui-qa/run-2026-10-06T064226909Z/report.json)で成功し、追加native実行はありません。取得失敗・digest不一致・旧遅延応答はHTTP応答へ注入したケースで、保存原票を書き換えません。遅延ケースはAbortを含む実経路であり、世代番号ガードだけの単独試験ではありません。

### 新たなnative観測が必要な場合

- 保存済みFlutter 3.47.1 / Dart 3.13.1と既存ローカルcacheだけを使う。
- 12項目、320×160、itemExtent 80、cache 0、offset 0→640→0。保持要求あり/なしの2条件×4段階。
- compile 1回（45秒上限）→tester 1回（25秒上限）、内部probeは20秒上限。一度に自分の子プロセスは1つ。
- 各起動前にnice 10を適用し、失敗したらexec前で停止。通常優先度で続行しない。
- 実行直前に12CPU全体のCPU/load・空きメモリー・既知SRE処理を正規readで確認。単一processの高CPUだけで可否を決めない。DeepSeekUIや他processの設定・稼働は変更しない。

原票の比較だけならcompilerもブラウザーも不要です。将来の再実行も必要がある時だけ別attemptで行い、失敗を上書きしません。SDK install、pub get、download、upgrade、Docker/OS設定変更は行いません。

## 読取専用の計画

`FLUTTER_ATLAS`を既存repoのパスに設定し、この教材のディレクトリで使います。`--execute`なしでは、metadataとcache参照を読むだけで、ファイル出力やcompiler/tester起動はありません。

```sh
python3 probe/run_probe.py \
  --sdk "$FLUTTER_ATLAS/.tools/flutter-3.47.1/flutter" \
  --cached-package-config "$FLUTTER_ATLAS/learning/widget-state-lifecycle/.dart_tool/package_config.json"
```

## 枠付与・資源確認後の1 batch

初回attempt 1はcompile3.067秒・tester0.677秒、両nice10/exit0で成功しました。次は必要が生じた時だけ、実行枠と資源の条件を確認して別attemptを使う例です。成功確認のためだけに再実行しません。

```sh
python3 probe/run_probe.py \
  --sdk "$FLUTTER_ATLAS/.tools/flutter-3.47.1/flutter" \
  --cached-package-config "$FLUTTER_ATLAS/learning/widget-state-lifecycle/.dart_tool/package_config.json" \
  --attempt 2 --execute
```

標準`flutter test`ではなく、保存済みfrontend serverとflutter_testerの直接起動です。SDK lockや設定を書き換えず、package configはcache参照を複製した専有attempt内へ作ります。入力snapshot・hash・優先度・終了値・所要時間・stdout/stderrを保存します。

## 観測と判定

`actual.json`に初期・準備・遠方・戻りを保存します。全生存StateとSliverの`keptAlive`による区分を記録し、cached状態のTextを「画面に表示していた証拠」とは扱いません。Textは生存Element subtreeからの読取です。プローブにGUI操作・画像captureはありません。

初回原票は`probe/observations/attempt-01/actual.json`です。別Python実装の照合は次で再現でき、compiler/testerを起動しません。初回は191確認passでした。自分のcompiler/tester記録済み2PIDが残っていないことも[確認済み](verification/process-cleanup-attempt-01.json)です。

```sh
python3 probe/verify_observation.py --attempt probe/observations/attempt-01
```

固定予測との比較前に原票を保存します。不一致でも可能な限り後続を観測し、cleanupを行います。API/実装の誤りか予測の誤りかを分け、修正する場合は変更前snapshot・差分を保存して必要な範囲だけ再検証します。readerのGUI/画像QAは完了していますが、FlutterライブGUI/pointer/drag・Flutter描画画像の確認は未実施です。

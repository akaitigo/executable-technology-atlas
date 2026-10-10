# 再現手順と実行前の条件

保存済みFlutter 3.47.1 / Dart 3.13.1と既存package cacheを使います。install/pub get/download/upgrade、OS/他process設定変更は行いません。旧教材はread-onlyです。

初回attemptは2026-10-06に成功しました。fresh readはload6.22/12CPU、CPU idle55.77%、memory_pressure指標74%、inactive約8.07GiB、unused1164MiB、throttled0、観測区間swap0でした。[資源判断](verification/resource-before-attempt-01.json)と[実行記録](probe/observations/attempt-01/run.json)を保存し、compile2.258秒・tester0.771秒、両nice10で終了しました。成功を再確認するためだけの再実行は不要です。

## 保存実測readerを使う

この教材ディレクトリで`python3 serve.py`を実行し、`http://127.0.0.1:18754/`を開きます。loopbackだけに配信し、終了時はCtrl+Cで止めます。条件と予想→移動/除去の保存実測→右に置いた後→原典/実行時ソース→答え合わせの順に読みます。原票取得があるためindex.htmlの直接ファイル表示は使いません。

readerの検証が必要な場合だけ共有browser枠とfresh資源確認後に`python3 check_gui.py`を実行します。既存Playwright/Chromium、sandbox有効、専用profile、nice10、1contextと短いtimeoutを使い、外部接続を遮断します。初回は[17確認・60操作・13画像](ui-qa/run-2026-10-06T071105414Z/report.json)で成功し、browser/profile/serverはcleanup済みです。503/digest不一致/旧遅延応答はブラウザー応答への限定注入です。原票・runtime入力を変更しません。

画面操作は保存原票の選択・再生、画像は実Chromiumのreader captureです。Flutterのライブ実行・pointer入力・描画画像とは区別します。GUI QAに伴うnative再実行はありません。

## nativeを新たに観測する必要がある場合

`FLUTTER_ATLAS`を既存Flutter repoに設定し、この教材ディレクトリで次を実行すると、metadata/cacheを読むだけの計画を確認できます。compiler/testerや出力の作成はありません。

```sh
python3 probe/run_probe.py \
  --sdk "$FLUTTER_ATLAS/.tools/flutter-3.47.1/flutter" \
  --cached-package-config "$FLUTTER_ATLAS/learning/widget-state-lifecycle/.dart_tool/package_config.json"
```

nativeの実行はrootの枠調整とfresh資源read後のみです。全体CPU/load・メモリー・既知SRE重処理を確認し、単一processの使用率だけで停止判断をしません。保護対象DeepSeekUIや他作者の資源・設定は変更しません。

```sh
python3 probe/run_probe.py \
  --sdk "$FLUTTER_ATLAS/.tools/flutter-3.47.1/flutter" \
  --cached-package-config "$FLUTTER_ATLAS/learning/widget-state-lifecycle/.dart_tool/package_config.json" \
  --execute --attempt 2
```

3条件×4時点、compile1回45秒上限→tester1回25秒上限、内部20秒上限です。自分のcompiler/testerは同時に1つ、nice10成功をexecの前提とします。失敗時に通常優先度で続行しません。原票・実行時input snapshot・hash・優先度・終了値をattempt内へ保存し、上書きや自動retryはしません。

上記は将来必要が生じた場合の別attempt例です。初回原票を上書きしません。

標準flutter testではなく保存済みfrontend serverとflutter_testerの直接起動です。SDK lock/設定を書き換えず、cache参照を複製するpackage configと一時pathは自分のattempt内だけです。想定と異なる結果も保存し、原票・コード/API・予測のどこに差があるかを切り分けます。

原票照合は次の読取だけで再現できます。compilerやbrowserは起動しません。

```sh
python3 probe/verify_observation.py --attempt probe/observations/attempt-01
```

初回の原票照合は245確認pass、記録済みPID63183/63189は終了を確認しました。native実験自体にGUI/browser操作はありません。その後のreader QAと分け、Stateメソッドの実Widget検証をライブpointer操作やFlutter画像確認と呼びません。

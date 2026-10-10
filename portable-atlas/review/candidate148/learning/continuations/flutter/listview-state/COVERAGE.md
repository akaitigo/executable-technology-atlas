# この教材が扱う範囲

状態：**2条件×5段階の実Widgetを局所受入し、保存実測readerのブラウザー操作・画像QAも確認。FlutterライブGUIは未確認。** 既存repoのcoverageや、前のColumn教材の受入記録は変更していません。

## 分野ゴール45との対応

「Widget・Element・StateとKeyを説明し、入替の状態を予想・操作し、実Widgetの生成・保持・破棄を照合する」というゴールのうち、遅延生成一覧に限った次の境界を切り出しています。

| 要求 | 今回用意したもの | 受入状態 |
| --- | --- | --- |
| WidgetのKeyとState同一性を説明 | Key→現在index→既存Elementの説明・固定ソース | ソース照合＋実WidgetのState対応一致 |
| 入替前後を予想する | 2条件・5段階の事前固定表 | 事前予測を変更せず実測と一致 |
| 遅延生成を操作・観測 | 12項目、固定viewport/cache、builder・State別記録のprobe | programmatic操作で10段階を観測 |
| 正常な対応とState喪失を比べる | callbackあり/なしの同一fixture | 実測差分0、独立Python照合163確認pass |
| 状態の所有と保存方法を選ぶ | 生存中の対応付けと、破棄後のデータ所有を分離 | 外部保存実装は未対応 |
| 予想・対照・答え合わせを操作する | 保存観測reader、条件/予想/reset、読込失敗時の古い結果消去 | Chromium16確認・43ポインター・9capture目視。Flutterライブ操作ではない |

## 重複調査の根拠

2026-10-06に既存`flutter-reference-atlas`の`learning`、`labs`、`coverage.yaml`、`atlas/definitive`、`reference-systems`を読取・語句検索しました。探索範囲で見つからなかった教材を、Atlas全体に存在しないとは判断していません。

| 既存成果 | 見つかった内容 | 今回の境界 |
| --- | --- | --- |
| `learning/widget-state-lifecycle/README.md` 106–107行 | ListView並べ替え/Key、keep-aliveを未教材として列挙 | ListViewのcallbackとState対応を切り出す |
| `labs/framework-element-reconciliation/README.md`、同Labのtest | Column直接兄弟のKeyあり/なし比較 | 同時に存在するColumn兄弟から、indexを使う遅延生成へ進む |
| `coverage.yaml` 58–66行 | `framework.key-controls-state-identity`は既存Labでcovered | 既存claimを未実装に戻さない。学習境界を補う |
| `reference-systems/operations-workspace/lib/src/presentation/workspace_app.dart` 240–285行 | 実務一覧にListView.builderとListTileがある | callbackとStateの入替対照実験ではない。既存ListView利用は尊重する |
| 前単元`flutter-next-design` | ColumnのKey階層、5条件25状態、実rasterと保存実測reader | 原票・文書修正記録・受入を変更せず別pathで制作 |

検索範囲内に`findChildIndexCallback`の既存教材は見つかりませんでした。SDKの同API実装は教材の不存在根拠ではなく、今回の予測根拠として使います。

## 範囲外

keep-aliveは「無効・要求しない」という固定条件だけです。有効/無効の比較、メモリーの評価、GlobalKey、restoration、削除/挿入、可変itemExtent、複数Sliver、キー重複、任意位置の大規模並べ替え、外部ストアの実装は含めません。

表の「初期2項目」「遠方I/Jだけ」は実行前に固定した予測で、今回の実renderer原票と一致しました。固定fixture以外への一般化はしません。境界の追加生成やAPI差異が現れた場合は観測原票を先に保存し、根拠を調べて次の改訂を分けます。固定表そのものを実測証拠へ転用せず、[実原票](probe/observations/attempt-01/actual.json)を参照します。Flutter全体の完了件数は更新しません。

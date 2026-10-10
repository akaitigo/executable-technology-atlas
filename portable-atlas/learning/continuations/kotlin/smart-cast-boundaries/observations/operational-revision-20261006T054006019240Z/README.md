# smart castの境界：今回の実測と答え合わせ

2026年10月6日 05:46:42–05:46:53 UTC（日本時間14:46:42–14:46:53）、既存のKotlin 2.4.10 / OpenJDK 17.0.17で、固定したcompile 3条件とruntime 6条件を実行しました。独立検証は49項目すべて通過しました。収集全体は10.835秒、再試行は0回です。

この記録が今回の実測です。教材直下のREADME・対応範囲・Skill・画面・statusは、親担当の追加指示により今回の状態を最小限反映しました。更新前の説明は[before/current-docs](before/current-docs/)へ保存しています。以前の保留原票、固定期待値、Kotlinソース3本、原典対応表、独立検証器は変更していません。

実行記録は[run.json](run.json)、照合結果は[verification.json](verification.json)、件数と資源の要約は[result-summary.json](result-summary.json)です。ブラウザ操作・画像QA・Atlas受入・統合は未実施です。

## 予想してから記録を読む

まず[固定期待値](../../expected.json)を開かずに、次の3点を予想してください。

1. `var` propertyをnull検査した後、再び読んで `.length` にアクセスできるか。
2. `val` propertyに独自getterがあっても、2回の読取りは同じ値か。
3. 最初の値をローカル`val snapshot`へ保存したとき、後のproperty変更はsnapshotに反映されるか。

操作の順序は[SnapshotAndContrast.kt](../../src/SnapshotAndContrast.kt)で確認できます。変更可能なpropertyは、snapshotの受取り後に明示的・逐次的に変更しています。独自getterは最初の読取りで初期値、その後はnullを返します。並行処理や偶然の競合を再現した実験ではありません。

## 正常な対照と失敗を比較する

| compile条件 | 実測exit | JAR | 分類 |
|---|---:|---|---|
| ローカルvalのsnapshotと比較用コード | 0 | 生成あり | 受理 |
| var propertyを検査後に再読取り | 1 | なし | 期待した`SMARTCAST_IMPOSSIBLE` |
| 独自getterのval propertyを検査後に再読取り | 1 | なし | 期待した`SMARTCAST_IMPOSSIBLE` |

拒否された2本は実行していません。runtime 6条件は、受理された同じJARを入力・経路だけ変えて実行しました。

| 経路と入力 | 実測の要点 | exitと分類 |
|---|---|---|
| mutable-snapshot / Ada | 元propertyはnullへ変更。snapshotはAda、長さ3 | 0・正常 |
| mutable-snapshot / null | 元propertyはAdaへ変更。snapshotはnull、利用を省略 | 0・正常 |
| getter-snapshot / Ada | 最初のAdaを保存して長さ3を利用。その後の比較用読取りはnull | 0・正常 |
| getter-snapshot / null | 最初のnullで利用を省略。その後の比較用読取りもnull | 0・正常 |
| getter-repeated-assertion / Ada | guardの1回目はAda、2回目はnull。`!!`でNPE | 1・意図した実行時異常 |
| getter-repeated-assertion / null | 最初のnullでguardを通らず、2回目は読まない | 0・正常 |

正常終了は5条件です。意図したNPEの1条件を正常終了へ加算していません。NPEは`java.lang.NullPointerException`として記録され、診断位置は`SnapshotAndContrast.kt:55`です。compile拒否2条件も、実行時異常とは別に記録しています。各stdoutの全文、stderr、終了値は変更していない独立検証器で固定期待値と照合しました。

## 原典・実装から答え合わせする

[Kotlin公式の固定版「Smart cast prerequisites」](https://github.com/JetBrains/kotlin-web-site/blob/135c79983f678c6367c5cc19eb5d8445eb3c95ce/docs/topics/typecasts.md#smart-cast-prerequisites)と、[今回のソース](../../src/SnapshotAndContrast.kt)を対応させてください。検査したローカルvalをそのまま利用する場合と、propertyをもう一度読む場合では、compilerが利用できる前提が違います。

答えは「同じ名前のpropertyを検査したから、次の読取りも必ず非null」ではありません。今回はローカルvalへ一度受け取った値を検査し、その同じ値から長さを求めました。元propertyが後で変化しても、`SOURCE_NOW`と`SNAPSHOT`が違うことに矛盾はありません。

getter-snapshotの`GET#2`は、snapshotを使い終えた後の比較用読取りです。これに対し、getter-repeated-assertionはguard後にもう一度getterを呼び、その結果へ`!!`を適用します。[非null表明の固定原典](https://github.com/JetBrains/kotlin-web-site/blob/135c79983f678c6367c5cc19eb5d8445eb3c95ce/docs/topics/null-safety.md#not-null-assertion-operator)が扱う別の操作であり、smart castを成立させたわけではありません。

mutable propertyのcompiler診断には「concurrently」の語がありますが、この実験で並行変更が起きた証拠ではありません。compilerがそのpropertyの安定性を前提にできない理由を示した診断です。

## 保存結果だけを再検証する

教材のルートで次を実行すると、KotlinやJVMを追加起動せず、今回保存した記録を検証できます。

~~~sh
python3 -B verify.py observations/operational-revision-20261006T054006019240Z/run.json
~~~

配布archiveのSHA256は`473dd66c7a3ef4b182065b3da670466c1bf2773a9dbb0ed8b33a39fe9d4f876d`、launcherは`7082c4cdf466d4a8c0879eccd2bbd0011204ff10267a7eba921c08982201ec92`です。展開済み125ファイルをarchiveと照合し、版表示も実行して確認しました。固定期待値やソースの不変確認は[開始前記録](authorization-and-baseline.json)と[結果要約](result-summary.json)にあります。

このattemptは完了しており、収集器は同じ`run.json`を上書きして実行しません。追加実験は今回行っていません。

## 実行時の資源判断



新しい条件は、全体CPU idle 30%以上、1分load/論理CPU数0.75以下、メモリqueryのfree 15%以上、free＋speculative＋inactiveの推定2 GiB以上、既知benchmark/compiler名の検出なしです。読取り失敗や不明な値は0件に置き換えず保留します。これらは、この小さい逐次batchを始めるための運用条件です。

| 観測 | 論理CPU | load 1分 | CPU idle | memory query free | 回収可能量の推定 | 既知重処理 |
|---|---:|---:|---:|---:|---:|---:|
| 開始前 | 12 | 4.10 | 75.84% | 40% | 約4.86 GiB | 0件 / 776 processを読取 |
| 代表1compile・1runtimeの後 | 12 | 4.54 | 54.47% | 39% | 約4.65 GiB | 0件 / 778 processを読取 |

原票は[開始前](resource-gate.json)と[代表後](resource-gate-after-representative.json)です。代表が固定期待値と一致し、資源条件も維持されたので、代表を重複実行せず同じattemptで残りへ進みました。

版確認を含む11個の子commandすべてで、exec前のnice実値10を[priority記録](priority/)へ保存しています。compiler heap上限256 MiB、runtime heap上限64 MiB、`ActiveProcessorCount=1`、各command 15秒、batch 45秒上限、逐次実行、再試行0回です。timeoutは0件、command終了後に残る自分のprocess groupも0件でした。他process、OS、daemon、保護対象DeepSeekUIの設定は変更していません。

メモリの数値は回収可能量の推定で、直ちに確保できる保証ではありません。XmxはJava heapの上限で、process全体の常駐メモリ上限ではありません。`ActiveProcessorCount`はJVMが使うprocessor数の設定で、OSのCPU使用量を厳密に制限するquotaではありません。既知process名の読取りも、未知の重処理が存在しないという保証にはなりません。

## 実務判断と残る範囲

判定と処理を一度読んだ同じ値へ揃えたい場合は、ローカルvalへの受取りが候補です。処理時点の最新値が必要なら、このsnapshotだけでは要件を満たしません。今回のString参照の受取りを、deep copy、複数fieldのatomic snapshot、lock、transactionや大域的な並行安全性の証明として扱いません。

今回実測した範囲は、この固定toolchainと3本のコードです。全property、open/module境界、委譲、captured local var、contract、Java境界、他compiler版、JVM以外は未検証です。ブラウザ・画像QAは未実施で、captureは作っていません。学習画面の模型とこの実行原票を区別し、Atlasの受入・統合は親担当の判断に残しています。

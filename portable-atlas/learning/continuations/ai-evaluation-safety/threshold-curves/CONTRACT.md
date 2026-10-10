# Atlas：閾値と陽性 ID 集合から ROC / PR を読む

この契約と手書き期待表を、計算プログラムの実装前に固定します。専有先はこのディレクトリだけ。元分野 owner の現状は未確認で、旧教材・Kotlin・compiler・共有台帳は読取り専用です。

## Atlas の到達点と前提



score が閾値以上なら陽性とする規則で、異なる score の全境界と最大より上の端点を列挙します。閾値を下げたとき、追加される ID、陽性 ID の包含関係、混同行列、ROC と PR の座標を対応させられることが目標です。最適閾値の自動推奨や安全認定はしません。

## Atlas の入力と有限な期待

元の [20件](inputs/predictions.json) を完全一致コピーしました。陽性2・陰性18で、score は20種類あり同点はありません。旧 `evaluate.py` の現物は4閾値 `(0.30, 0.50, 0.80, 0.90)` を使います。依頼要約の3閾値との差を [記録](records/input-provenance.json) に残し、旧結果を再実行・再加算しません。既存 Brier 教材の確率損失も今回の範囲には含めません。

主表は「最大 score より大きい」と全20個の異なる score、計21状態。同点の一括判定だけは [別の3件](inputs/tie.json) で対照します：陽性 `t-high`=0.90、陽性 `t-positive` と陰性 `t-negative` は共に0.50。こちらは3状態です。元20件を改変して同点を作ったことにはしません。

[expected.json](expected.json) に各状態の陽性 ID 全集合・追加 ID・TP/FP/FN/TN・約分した有理数を手で固定します。元表の閾値0.40では `{p01,n01,n02}`、0.35ではそこへ `p02` が入ります。Recall は1/2→1、FPR は1/9のまま、Precision は1/3→1/2です。Precision の単調減少を規則にしません。

同点対照は `>0.90` で空、`>=0.90` で `{t-high}`、`>=0.50` で3件全部。0.50で同点の片方だけを先に含む中間点を作りません。

## Atlas の計算と図の規則

JSON の数値は Decimal として読取り、同点判定に二進浮動小数点への丸めを挟みません。score の大小は Decimal、ID 集合の保存順は辞書順。閾値は異なる score の降順です。最大より上の端点は `kind: above-maximum, value: null` と最大値の情報で表し、Infinity や範囲外の数値を旧 runner へ渡しません。全陰性という数学上の別条件です。

- Recall / TPR = TP / (TP+FN)、FPR = FP / (FP+TN)、Precision = TP / (TP+FP)。分子・分母と約分した有理数を保存し、小数は図の表示用にだけ使います。
- 分母0は `fraction: null, value: null, status: undefined-zero-denominator`。全陰性端点の Precision を0や1に置き換えません。
- ROC は (FPR, TPR)、PR は (Recall, Precision)。PR 未定義点は座標なしと明記し、0で描画・補間しません。
- 点を結ぶ線は読む順の案内で、途中の全座標が決定的閾値で実現する保証ではありません。AUC・補間規則・積分は今回計算しません。

全24状態に ID の追加/残存、4分類の ID と件数、座標を保存します。入力拒否の広い網羅や、陽性/陰性自体が0の別標本は今回実測しません。保存検査では同点の分割、`>` への誤変更、分母の混同、未定義→0、座標軸逆転、IDの脱落などの故障を改変したコピーで検出します。

## Atlas の原典・実装・受入

Google の公式 [ROC and AUC](https://developers.google.com/machine-learning/crash-course/classification/roc-and-auc) の ROC / Precision-recall curve / threshold choice と、[Accuracy, recall, precision](https://developers.google.com/machine-learning/crash-course/classification/accuracy-precision-recall) の Recall / FPR / Precision / NaN を2026-10-06に実読しました。前者の更新表示は2026-05-11、後者は2026-01-12です。本文・図の大量複製はせず、出典対応を自分の短い説明で残します。全 unique 境界、同点の同時追加、Decimal、有理数と null の表現は今回の実装契約です。

既存 Python 標準ライブラリーのみ。子1件・worker0・対象再試行0、子の開始前に nice10以上の実値を確認し、失敗なら本処理を開始しません。CPU2秒・経過3秒、全手順10秒を目安とし、自己所有 group の TERM後0.5秒/KILL後1秒回収を有限に行います。完全 stdout/stderr、部分結果、固定入力 hash、環境、回収を保存します。

直前に load<6、idle25%以上、メモリ空き照会20%以上・推定2GiB以上、既知重処理/他headlessなしを正式に読みます。ps が空・解析失敗・自身PID不在なら不明として停止し、必要なら同じ無害な読取の通常審査を使います。余裕値はメモリ確保保証ではありません。

別担当は実装前の独立期待と保存した値を照合します。予想→閾値操作/ID集合対照→公式資料/コード→答え→実務判断と限界の画面と限定 Skill を用意します。図は保存計算値の模型で、実モデルや実画面の画像ではありません。新規 Chrome 起動・前面化は保留。実 DOM/画像0なら独立受入は false を維持します。

学習済みモデル、API、実世界の標本、確率較正、汎化、信頼区間、公平性、AUC、性能、安全認定は扱いません。旧元 repo への統合、正式分類、作者による教材加算は0です。

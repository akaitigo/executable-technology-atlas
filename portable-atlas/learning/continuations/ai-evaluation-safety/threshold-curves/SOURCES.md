# Atlas：公式規則と独自の実装を分ける

|公式本文と実読箇所|Atlas で使う規則|
|---|---|
|[Google: ROC and AUC](https://developers.google.com/machine-learning/crash-course/classification/roc-and-auc)、ROC、Precision-recall curve、threshold choice。2026-10-06実読、更新表示2026-05-11|ROC は横軸 FPR・縦軸 TPR。PR は横軸 Recall・縦軸 Precision。閾値を選ぶ際は誤警報と見逃しの費用を考える|
|[Google: Accuracy, recall, precision](https://developers.google.com/machine-learning/crash-course/classification/accuracy-precision-recall)、Recall / FPR / Precision / NaN。2026-10-06実読、更新表示2026-01-12|各割合の分母は別。陽性予測が空なら Precision の分母が0になる|

Atlas の全 unique score 境界、同点の同時追加、最大値より上を数値でない端点として扱うこと、Decimal と厳密分数、未定義を null に保存することは [今回の契約](CONTRACT.md) です。Google の図や本文を複製していません。ページの更新表示は確認しましたが、固定版の全文 hash を取得したという意味ではありません。

元 [20件の入力](inputs/predictions.json) は人が作った score です。学習済みモデルから出た値でも、較正された確率でもありません。旧混同行列の少数閾値や Brier の既存実験を、今回の全境界の新しい実測と混ぜません。[出所と完全一致コピー](records/input-provenance.json) を参照してください。

同点対照 [3件](inputs/tie.json) は、同じ score が境界で分割されない規則を見るための別入力です。元20件には同点がないため、元データだけで同点処理を実測したとは言いません。

# 閾値が変える見逃し・誤警報と、Accuracyの限界

20件の固定合成データ（実陽性2件・実陰性18件）で、混同行列、Accuracy、Precision、Recall、FPRをPython標準ライブラリで実計算する教材です。scoreは作者が置いた値で、学習済みモデルの出力ではありません。

## 予想してから操作する

1. 閾値を0.30から0.90へ上げると、見逃しFNと誤警報FPはどう変わるか。
2. Accuracyが90%の3つの設定は、同じ性能だと言えるか。
3. 陽性予測が0件ならPrecisionは0%、100%、未定義のどれか。
4. scoreが閾値と等しいsampleはどちらへ分類されるか。

## 実行・操作

Module rootで実行する。

```bash
python3 verify.py
python3 observe.py --check
python3 evaluate.py --threshold 0.50
```

保存済み原票を再生成する場合は `python3 observe.py --write` を使う。checker成功後に新しいbundleをstagingへ生成し、directory renameで公開する。失敗時は前のbundleを保持する。

画面は依存のない静的HTMLで、閾値selectorから4設定を選べる。JSONはPython実行原票、`evidence/data.js`は同じ原票から生成したUI用の複製、図とレイアウトは説明モデルである。画面内では新しい推論や学習を実行しない。

確認済みの表示経路:

```bash
python3 -m http.server 8767 --bind 127.0.0.1
```

別のBrowserで `http://127.0.0.1:8767/index.html` を開く。終了時はserverをCtrl-Cで止める。`open index.html`によるfile direct-openは、実QAで確認した場合だけQA記録に追記する。

## 正常・異常比較と答え合わせ

| 閾値 | TP | FN | FP | TN | Accuracy | Precision | Recall | FPR |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 0.30 | 2 | 0 | 2 | 16 | 90% | 50% | 100% | 11.11% |
| 0.50 | 1 | 1 | 1 | 17 | 90% | 50% | 50% | 5.56% |
| 0.80 | 1 | 1 | 0 | 18 | 95% | 100% | 50% | 0% |
| 0.90 | 0 | 2 | 0 | 18 | 90% | 未定義 | 0% | 0% |

このfixtureでは0.30・0.50・0.90のAccuracyが同じでも、実陽性の検出数は2・1・0件。多数派の陰性18件だけを正解にする設定も90%になる。閾値0.80ではscore 0.80の`p01`がTPに残り、比較演算が `>=` であることも確認できる。

## 資料・実装・原票の対応

- [Google公式の分類metric解説](https://developers.google.com/machine-learning/crash-course/classification/accuracy-precision-recall)のAccuracy、Recall、False positive rate、Precision、NaN節を数式と限界へ接続する。
- [Google公式の閾値と混同行列](https://developers.google.com/machine-learning/crash-course/classification/thresholding)をbinary predictionと4分類の読解へ接続する。
- [sources.json](sources.json)はURL・metadata・locatorのみを保持する。第三者本文は保存していない。
- [predictions.json](predictions.json)は固定入力。[hand-count.json](hand-count.json)はsample IDを独立して列挙した手集計Oracle。
- [evaluate.py](evaluate.py)は分類・集計・分数計算。[verify.py](verify.py)は手集計照合とboundary/invalid input検査。
- [原票](evidence/observation.json)、[環境・日時・digest](evidence/verification.json)、[UI](index.html)、[Skill](skills/atlas-ai-evaluation-safety/SKILL.md)を使う。

数式は `Accuracy=(TP+TN)/N`、`Precision=TP/(TP+FP)`、`Recall=TP/(TP+FN)`、`FPR=FP/(FP+TN)`。分母ゼロはJSON `null`と`undefined-zero-denominator`を保存し、画面では「未定義」と表示する。空データ、非binary label、NaN/infinity、範囲外score/threshold、重複IDは成功扱いせず拒否する。

## Coverageと制限

教材化した範囲は、固定binary predictionの4分類、4metric、閾値の包含境界、class imbalanceの反例、ゼロ分母と不正入力である。scoreの較正、統計的信頼性、母集団の代表性、未知データへの汎化は証明していない。

未教材: モデル学習、train/test分割とleakage、cross validation、ROC/PR curve、AUC、calibration、confidence interval、multi-class、ranking/generation、LLM evaluation、adversarial robustness、prompt injection、privacy、fairness、safety governance、現実属性ごとの評価、運用monitoring、distribution shift。この1教材はAI Evaluation/Safety分野全体の完成を意味しない。

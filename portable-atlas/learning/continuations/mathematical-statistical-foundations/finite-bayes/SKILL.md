---
name: atlas-statistics-finite-bayes
description: Atlasの二つの未知p仮説を使い、事前重み・尤度・事後重みと観測事象の違いを有限資料へ案内する。
---

# Atlas｜有限Bayesの資料を使う

[前提の条件付き確率](related.html?topic=base)→[契約](CONTRACT.md)→[固定入力](cases.json)→[実装前期待](expected.json)→[保存計算](observations/run-01/results.json)→[原典](SOURCES.md)→[範囲](COVERAGE.md)へ辿る。入口は[学習画面](index.html)。[状態](qa/reader-acceptance.json)を読み、計算と独立照合、保存結果readerのGUI確認、現物coinや現実のpriorの妥当性という未対応範囲を分ける。画面の前提・原典対応・Skillへの実リンクと表示本文も確認済み。

1. 「元のBayes教材と同じ？」：元は既知populationの構成割合、今回は未知p仮説への重み。式は共通だが、現実のpriorを正当化した実験ではないと説明する。
2. 「HTTの尤度が9/64なら、低pの事後確率も9/64？」：sequence-equal / sequence-shifted / count-equal を保存値で比較し、priorとの積と正規化、列と個数の係数を辿る。事後だけ一致してもevidenceは3倍違う。等priorでprior無視の故障が正答と一致しても一般化しない。
3. 「priorが0でも観測で復活する？ 実際のpは1/2かも？」：zero-priorでは低pの重みは0のまま。1/2は仮説集合に含まれず、今回のモデルでは答えられない。[範囲](COVERAGE.md)へ戻し、二仮説の重みを現実の真偽保証にしない。

この3例を資料で辿る限定Skillです。未知質問への一般Agent評価・利用者理解度・安全認証は行いません。global installや他の教材への書込みは不要です。

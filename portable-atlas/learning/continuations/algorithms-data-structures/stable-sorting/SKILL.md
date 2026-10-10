---
name: atlas-stable-sorting
description: Atlasの有限な安定整列・検索準備費用の資料を案内する。実性能や任意比較関数の保証には使わない。
---

# Atlas｜安定整列の資料を使う

最初に[契約](CONTRACT.md)と[範囲](COVERAGE.md)を読み、質問が固定6入力・3方式に収まるか判断する。保存値は[計算結果](observations/run-01/results.json)、実装前の予想は[手期待](expected.json)、原典は[SOURCES](SOURCES.md)、入口は[学習画面](index.html)。保存結果は今回の18整列・8拒否の実計算です。保存結果を読むGUIは18選択と代表3画像を確認済み。最終の受入状況は[状態](qa/reader-acceptance.json)へ戻る。関連資料は同じページへの移動と本文を照合済みだが、リンクの実クリックは未確認と分ける。

- 「key順なら十分？」にはmixed-duplicatesを使い、merge_rightのkey順/要素保存がtrueでもstabilityはfalseである理由を元ID列で示す。
- 「二分検索なら今回も得？」にはmixed-duplicatesの6query末尾で、挿入比較6＋検索17＝23と線形23が同じという手期待と今回の保存結果を辿る。配置7は別欄で、実時間が同じとは答えない。
- 「どれが実機で最速？」には[COVERAGE](COVERAGE.md)の実性能未確認へ戻る。比較数からCPU速度や任意入力の最適性を作らない。

予想→保存結果→正常/故障対照→原典/実装→答え→限界の順で案内する。状態やhashが不一致なら古い結果を使わない。これは3つの有限な資料利用例の案内で、一般Agent評価や未知質問への成功保証ではない。global Skillへのinstallや共有repoの書換えは行わない。

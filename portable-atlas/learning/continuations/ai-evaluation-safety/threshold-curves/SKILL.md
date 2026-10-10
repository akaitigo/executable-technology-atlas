---
name: atlas-threshold-id-curves
description: Atlas の合成 score と陽性 ID 集合から、固定境界の ROC/PR と未定義を限定的に案内する。
---

# Atlas：保存した閾値計算の意味を案内する

## Atlas の範囲確認

[契約](CONTRACT.md)、[入力](inputs/predictions.json)、[同点対照](inputs/tie.json)、[手書き期待表](expected.json) を読む。元21状態＋同点3状態だけを対象にし、全分類器・現実の性能・確率較正・AUC・安全認定を保証しない。質問がそれらを含むときは、保存事実で答えられる部分と別に必要な証拠を分ける。

## Atlas の通常手順

1. [status.json](status.json) の `observation` と `browser_start_hold` を読む。observation が null なら、契約・手計算・原典・コードまでで止まり、期待表を実測として扱わない。新規ブラウザー起動が保留なら、新しいブラウザー・前面化・サーバー起動に進まない。既に利用できる画面ではREADMEの読む順を案内できる。画面の実施範囲と別担当の受入は状態記録へ分ける。
2. [元20件](inputs/predictions.json) の label と score を読み、陽性 ID を予想してもらう。同点の話は別の3件であると先に伝える。
3. 保存結果があれば、状態が指す実行記録の SHA と完成状態を確認し、選んだ `fixture` と `ordinal` の `state` を読む。資料不在・照合不一致と、計算上の未定義を分ける。
4. `positive_ids` / `added_ids` →4分類の ID/件数→各割合の分子/分母→`roc` / `pr` の順に辿る。ID の辞書順は score の順ではなく、集合の表示順であることを説明する。
5. [公式規則](SOURCES.md) と [計算コード](threshold_sweep.py) へ戻り、[手計算](HAND_TRACE.md) と比較する。自由記述の予想は自動正誤判定したことにしない。
6. [COVERAGE](COVERAGE.md) の未対応と、実務で必要な用途・損失・標本の条件を明示する。

## Atlas の有限な案内例

- 最大より上：数値thresholdや Infinity を旧runnerへ渡す操作ではない。陽性集合は空、Precisionは0/0、PR座標なし。
- 0.40→0.35：p02追加で Recall は1/2→1、FPRは1/9のまま、Precisionは1/3→1/2。集合の単調拡大からPrecisionの単調減少を推論しない。
- 同点0.50：t-positiveとt-negativeは同時に加わる。好きな片方だけを途中の閾値として表示しない。
- ROCとPR：横軸/縦軸の分母を読み直す。未定義点を0や1へ補う描画慣行を、この教材へ黙って持ち込まない。
- 「このモデルは安全か」：モデル自体を学習/評価しておらず、計算の一致からは答えられない。

## Atlas の保存検査と新規計算を分ける

保存結果がある場合だけ、その実在パスを `python3 -B verify.py --run <保存したrun.json> --mutations` に渡して再照合できる。これは新しい対象計算やブラウザーを起動しない。欠落時に自動で再実行しない。

再計算が必要な作業では契約の資源・排他・優先度実値・時間制限・自己所有子回収を満たし、新しい保存先へ完全出力と失敗を残す。期待表や旧結果を結果に合わせて変更しない。SDK/外部AI/API/OS設定変更は不要。Skill文書の配置、有限な資料読取り、一般Agentの案内評価を別々に記録する。

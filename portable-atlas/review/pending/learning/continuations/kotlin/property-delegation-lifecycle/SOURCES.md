# Atlas：KR-02の固定原典を再利用する

この教材は原典調査を作り直さず、Epoch 2026-08-28で保存されたKR-02本文の必要箇所を読む。固定commit・元ファイルhash・行範囲・抜粋hashは[sources.json](sources.json)に保存した。取得や共有元の更新はしていない。

|読む規則|今回同梱した必要範囲|
|---|---|
|getValue/setValueの展開とthisRef|[Spec 1444–1506](inputs/source-sections/property-access.txt)|
|operatorの引数/型条件|[Docs 244–298](inputs/source-sections/property-operators.txt)|
|provideDelegateと結び付け|[Spec 1512–1550](inputs/source-sections/provide-delegate.txt)|
|説明上の補助fieldと最適化の境界|[Docs 314–400](inputs/source-sections/property-expansion-limits.txt)|

元の専用mode証拠10件のgapを、この3条件で閉じない。KR-02の概念と未実行例、KR-03のlazy mode、後続の例外・有限再入は既存成果として案内し、再実行・再加算しない。正式なAuthority意味分類、原典全体の読了、他platformでの確認とは別である。

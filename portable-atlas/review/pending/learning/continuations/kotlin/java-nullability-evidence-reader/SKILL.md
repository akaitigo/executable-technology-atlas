---
name: kotlin-java-nullability-evidence-reading
description: 既存Java nullability pilotの記録を読み、@NotNull宣言・実装・compile拒否・runtime失敗と証拠の限界を区別する。
---

# Java境界の保存証拠を読む

1. observations/status.jsonで制作・データ検査・GUI・独立受入を区別する。新規native実験ではないことを先に伝える。
2. READMEの手順でindex.htmlを使い、通常文字列／空文字列／契約違反／null引数の結果を予想する。
3. A欄の元原票、B欄の固定期待との対応を読み、runtimeとcompile拒否を別に比較する。取得失敗はJava/Kotlinの失敗結果ではない。
4. 固定公式原典とJava/Kotlin source、最小annotation定義へ進む。cache内JetBrains jarの読取確認を、pilotがそのjarを使った証拠へ変えない。
5. C欄の説明で答え合わせし、空文字列とnull、型の宣言と実装の保証を区別する。
6. ログ全文・実行日時・生成物が未保存という限界を守る。期待文字列を保存stdout全文と呼ばず、NPE stack traceや実traceを作らない。
7. 必要な整合確認はverify.pyとcheck-model.mjsだけで行う。元収集コードの写しは参照用で、実行しない。原repoや旧教材、台帳は変更しない。
8. 実GUI20検査・63操作と7実画像の目視は完了した。browser-qaの原票・visual-review.jsonを確認し、作者QAと独立受入を分離する。撮影後は状態案内1行だけを変え、差分を保持した。この1単元の成果と残項目を返し、次々の単元へ自動で進まない。

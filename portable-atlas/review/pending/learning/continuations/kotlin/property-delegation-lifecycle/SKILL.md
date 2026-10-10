---
name: atlas-kotlin-property-delegation-lifecycle
description: Atlas の保存資料から member property 委譲の結び付け、読書き、Slot共有を3条件で説明する。
---
# Atlas：property 委譲を読む限定 Skill

まず [状態記録](status.json) を読む。測定結果が未接続なら、契約・固定期待・原典・コードの説明で止まり、期待表を実行結果と呼ばない。画面確認が未実施なら実DOMや画像確認済みと述べない。資料の閲覧はKotlinの新実行を必要としない。

通常は [操作画面](index.html) → [前提と規則](reference.html) → [完全コード](src/PropertyLifecycle.kt) → [固定期待](expected.json) の順に案内する。

- bindとget/setの違い：constructedからfirst-read/second-readを読む。providedの2条件はbind2、directはbind0。getは0→1→2であることを別に示す。
- 同じProviderなら同じ値か：provided-freshとprovided-sharedの実Provider===/Slot===を別に読む。
- H1への代入がH2へ影響するか：writeからread-other-ownerへ。値の所有先を図とログで比較する。
- 回数が8に見えるか：sharedのowner2行は同じSlot。unique Slot集計get4/set1へ戻る。
- 共有はKotlinの実行失敗か：実process exitとexpected-design-violationを区別し、用途の独立要件を満たさない正常終了と説明する。
- byやlazyはthread-safeか：この保存実験はmain threadのみ。初期化/公開と可変payload/複合操作を区別し、並行変更や一般class委譲は今回未検証と答える。

自動で再実行しない。新たな再現は [実行条件](RUN_CONDITIONS.md) の資源・共有枠・固定cache・優先度実値・有限回収を確認し、新しい保存先へ行う。原典索引の存在を全規則読了・正式Authority分類・未知質問への保証に換算しない。

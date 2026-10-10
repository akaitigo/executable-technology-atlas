---
name: atlas-software-quality-engineering
description: このローカル教材で、区間判定の行coverage、境界test、固定変異のkill/surviveと同値例を説明・再現する。汎用品質監査やCI、fuzzing等は未対応。
---

[UIと図](../../index.html)、[元関数](../../core.js)、[変異・test・独立oracle](../../experiment.js)、[手順と制限](../../README.md)から質問に必要な箇所だけ読む。

弱い3testは全行を通ってもM1/M2/M4がsurviveする。下端・上端・空区間を追加すると4つの非同値変異をkillする。元関数のpassedと、意図した変異のkilledを混同しない。

再現にはmodule directoryで既存runnerを使う：`node verify.mjs observations/<新しいrun名>`。新しい出力先にmatrix・Node coverageの生出力・環境・時刻・Source hashを保存する。既存[原票](../../observations/node-20261005-attempt-01/runtime.json)を引用するときは、入力・実装version・現在Source hashとの一致を確認する。画面QAは既存[serve.mjs](../../serve.mjs)のlocalhostプレビューで行える。

E1は有限整数・lo≤hiの領域で同値と理由付きで別扱いし、5件の生分母と4件の非同値分母を残す。NaNや別契約へ同値性を一般化しない。coverageや固定mutation scoreを品質全体の保証としない。Browserの表示操作は実JSを再実行し、Node coverage自体は保存済み原票を照合して表示する。

性能・回帰選定・型検査・fuzzing・大規模CI等の依頼は[未教材scope](../../scope.json)を案内し、このmoduleで対応済みとは返さない。追加実装、公開、global installをこのSkillの機能に含めない。

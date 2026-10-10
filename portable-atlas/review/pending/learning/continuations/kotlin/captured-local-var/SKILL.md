---
name: kotlin-captured-local-var-learning
description: 書換ラムダに捕捉されたlocal varを、変更のないlocal varとlocal val snapshotに比較し、compile拒否と正常なnull分岐を区別する。
---

# captured local varの境界を学ぶ

1. observations/status.jsonで設計・実測・GUI QA・受入を分けて確認する。固定期待値を実測として紹介しない。
2. 前教材のpropertyとlocal valの比較を振り返り、今回はlocal varを誰が変更するかを予想する。
3. index.htmlで条件と予想を選び、保存原票を読む。non-captured control／書換closureの拒否例／書換前snapshotを比較し、原典・実装の後で答えを開く。条件・予想の変更やresetでは前の結果が消える。資料取得の失敗をcompile拒否やNPEへ読み替えない。
4. 実行は親担当が調整した専有枠で、既存固定cacheのみを使用する。全体CPU/load/メモリ・既知重処理を正規readし、unknownを0件にしない。sandboxで無害なreadが阻害されたら同じreadを正規reviewへ回し、拒否なら迂回しない。
5. 収集はnice実値10以上・1 active processor・小heap・短timeout・逐次1batch・再試行なし。代表1条件の成功と資源再確認後、同じattemptで残りへ進む。他process/OS/Dockerの設定を変更しない。
6. 保存したrun.jsonをverify.pyで独立照合する。今回の実測はcompile2（受理1/期待拒否1）・runtime正常4、独立46項目pass、runtime NPEは0。拒否をruntime異常へ数え直さず、不要なnative再実行をしない。
7. この単元のGUIは21検査・78実ポインター操作・7実captureの目視が完了した。原票はbrowser-qa/run-2026-10-06T064513392Z/report.json、目視はbrowser-qa/visual-review.json。必要な変更時だけ別の許可された枠で再確認し、模型と保存実測、作者QAと独立受入を分離する。以前の教材・原票・共有台帳は変更しない。
8. 一度読んだ値と最新値のどちらが必要か判断し、全capture・inline/contract・並行安全性へ一般化しない。この1単元の成果と残項目を返し、さらに次の単元へ自動で連鎖しない。

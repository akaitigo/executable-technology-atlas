---
name: atlas-api-retry-idempotency
description: この継続教材で、POST commit後の無応答と1回の再送を実HTTP・SQLite原票から調べる。本番注文、決済、無限retry、TTLや分散exactly-onceの実装には使わない。
---

教材rootはこのskill directoryから `../..`。READMEを読んで、clientのunknownと観察用DBのcommit済みを分ける。

保存証拠を調べる要求には `python3 -B check.py` と `python3 -B runner.py --case same-key --inspect-evidence` をrootで実行する。生のSQL ledgerと保存responseを参照して答える。

合成実験の再現要求には `runner.py --case no-key|same-key|key-conflict`、UIには `server.py` を使う。loopback権限は既存実行環境の制約に従う。新しい証拠保存は明示 `--record` のみ。各runは最初のPOST＋明示再送1回で終了する。

本番再送やTTL/分散保証の要求なら本教材の対象外と伝え、README末尾の未実施の問いへrouteする。URL、実注文、credentialをrunnerへ足さない。同一keyでもbody変更は409で止まる。POSTというmethodだけを再送許可としない。

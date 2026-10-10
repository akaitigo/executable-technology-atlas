---
name: atomic-replay
description: 認証済IDのcheckとrememberを分離した場合の競合を、この有限教材の全順序と実thread代表観測で学ぶ。
---

# 認証後の受入を追う

このskillの2階層上にあるCONTRACT.mdを先に読む。手表の6split順序を予測してから、README.mdのserve.pyで教材を開く。同じIDのsplit-2とatomic-ABをstepごとに比べる。seenが1要素でも受入2件になる理由をcached_absentから説明する。

既登録・異なるID・invalid MAC・mixed・payload違い・bytes境界を比較する。保存thread witnessは実観測だが全6順序の列挙ではない。Barrierはsplitではcheck後、atomicではLock前。Lock内でBarrierを待たない。sleepで再現しない。

検証はpython3 -B verify.pyとroute.py。証拠を書き換える--record/--seal-recordは通常学習では使わない。有限集合の教材からDB、永続化、TTL、再起動、分散、ESP、exactly-onceを断言しない。公開fixture鍵を実運用へ使わない。既存moduleや全体indexを変更しない。

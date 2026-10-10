---
name: atlas-information-theory-coding
description: Hamming(7,4)の偶数parity、syndrome、単一bit訂正と2bit誤訂正を、この教材のPython実装・独立oracle・操作UIで確かめる。SECDEDや他の符号方式は未実装として区別する。
---

# Hamming(7,4)を確かめる

このSkillのrootは[教材](../../README.md)。module内だけを使い、依存導入・他Repository・公開へ広げない。

- 再現・保存観測の検査：rootで`/usr/bin/python3 -B verify.py`。既定はread-only。
- 単一bitの質問：`/usr/bin/python3 -B lesson.py --case single-data`。送信符号語、受信語、syndrome、反転位置、復号を回答へ接続する。
- 2bitの境界：`/usr/bin/python3 -B lesson.py --case double-counterexample`。`post_syndrome=0`を回復成功と扱わず、原messageとの不一致を説明する。decoderは原messageを受け取らない。
- 操作したい場合：`/usr/bin/python3 -B lesson.py --port 18748`をloopbackで起動し、UIで予測→反転→実行→比較する。自分が起動したserver/tabだけを終了する。
- 記録の再生成は利用者が求めたときだけ`lesson.py --record`、`verify.py --record-checks/--record-http/--record-media/--record-readonly`。HTTPと画面は実serverで採取し、未実行画像を作らない。

位置は左から1〜7、parityは1/2/4、dataは3/5/6/7。syndrome表示はs4s2s1。MIT資料の列順をそのまま貼らない。

SECDED、Reed–Solomon、LDPC、物理通信、圧縮、容量定理などはこのrunnerにない。[範囲表](../../README.md#対象範囲)を示して未実装と答え、別方式をこの教材の結果で検証済みにしない。保存digestは再現のbindingであり、数学的保証は独立oracleと試験範囲から説明する。

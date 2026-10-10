---
name: reduction-order
description: 固定float列の逐次・隣接tree・math.fsumとID欠落を限定教材で検証する。MPIや性能保証には使わない。
---

このmoduleだけを対象にREADME→hand-oracle→producer→oracleを読む。通常 python3 -B verify.py と route.py は保存しない。未使用attempt recordとQA sealだけが観測を書き込む。固定CPython3.9.6と4要素以外は拡大しない。UIで予想→実行→比較→原典→答え、開いた答えの予想変更clearと位置拒否保持を確認する。MPIや全入力安定性要求は未対応と明記し、関連数値計算Subjectへ案内する。global installしない。

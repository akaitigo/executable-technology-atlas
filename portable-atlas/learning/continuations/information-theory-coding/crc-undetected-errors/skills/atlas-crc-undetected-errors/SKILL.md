---
name: atlas-crc-undetected-errors
description: 独自4+3bit CRC教材でXOR長除算、単一bit/burst/未検出反例を実操作から比較する。製品profile適合、実通信性能、訂正、暗号認証は対象外。
---

module rootのREADME.md、contract.json、crc.mjs、oracle.mjsを読む。元Hamming教材と他continuationはread-only。

- 正常routeはundetectedを選び予想→新しい実行→次のXOR位置→最後→答え。remainder000でもpayload0001は元0000と違う。受信器へ元message/maskを渡さず、比較はharnessだけで行う。
- no-error、single-data、single-crc、short-burstと比較。spanは1の個数ではなく端の1間の幅、内部0あり、span1も含む。非零127maskの未検出15/検出112を全2048条件で照合し、channel確率へ転用しない。
- node verify.mjs / node check.mjsは通常read-only。明示--record observations/NEW-IDだけ原票保存、既存directory拒否。所有tab/serverだけ終了し、既存利用用server/他moduleは操作しない。
- 製品CRC/実通信/訂正/認証を求められたら未対応と説明し、scope.jsonのE1–E4へ案内。CRC passを原文一致/送信者認証と呼ばない。追加SDK、Cloud、鍵/OS設定へ今回の許可を拡張しない。
- 通常routeと未対応routeは同一agent確認であり独立Forward Evalではない。旧Evidenceを上書きしない。全Subject/Atlas完成を主張しない。

# write policyとdirty eviction

前提: byte address、4B block/offset、valid/tag、cache fill。[前単元のread-only競合](../../../subjects/computer-architecture-digital-systems/README.md)から、storeで更新したdataの保存へ進む有限続編です。容量4B/line4B/1行、metadata除外、memory256Bの初期値(17*a+3)%256。両方式write-allocate。実CPUではなくPython標準ライブラリの状態遷移modelです。

1. load0 → store1=99 → load1の後、cacheとmemoryは両方式同じか予想する。
2. `python3 verify.py`で記録と独立期待値を照合し、`python3 serve.py`のURLで[UI](index.html)を開く。
3. ケースとselected stepを操作し、返却byte、before/after cache、memory、dirty、victim block先頭address、書込transaction/byte数を3方式で比較する。
4. 原典locator、実装、rawを読み、答え・実務判断・未教材へ進む。

主要概念: WTはstoreごとにcacheとmemoryの1byteを更新。WBはcacheだけを更新してdirty=trueとし、dirty victimを置換前に4B書戻す。故障版はdirty evictionの書戻しだけを省略する。flushはresident dirty lineをmemoryへ一度書戻しdirty=falseへ戻す独自操作。

| 予想の答え | WT | WB | 故障版 |
|---|---|---|---|
| load0/store1=99/load1 | cache99、memory[1]=99 | cache99、memory[1]=20、dirty | WBと同じ |
| 続けてload4/load1 | 99 | victim先頭0を保存して99 | 20に戻り値不一致 |
| clean eviction | 書戻し0 | 書戻し0 | 書戻し0 |
| dirty flush / 再flush | storeの1byte書込後、flush増分0 | 4B書戻し1回 / 増分0、dirtyfalse | flush自体は正常 |

実務判断: 新blockではなくvictim blockのaddressへ保存する。hitやcacheの値だけでなく、eviction後の再読とbacking memoryも確認する。書込transaction数とbyte数は別で、WBが1transactionでも4B、WTはstoreごと1B。このmodelからcycleや速度を推定しない。[Cornell Handling Stores](https://www.cs.cornell.edu/courses/cs3410/2025fa/notes/caches.html#handling-stores)のwrite-through/write-back/dirtyを概念入口にする。

独立期待値: [手書き状態表](hand-oracle.json)はproducer実行前に固定。別の[逐次memory仕様とchecker](source.html?file=verify.py)は、256byteを17刻みのrecurrenceで用意しstoreを即時に論理memoryへ反映する。load返値をその仕様と比較し、正常のbacking memory＋resident dirty lineから論理memoryを復元できることを全stepで確認する。replacement実装を期待値として複製しない。[producer](source.html?file=cache.py)と[raw](observations/attempt-01/raw.json)を読む。

入力契約: trace0..64、loadはaddress、storeはaddress/value、flushはopのみ。address/valueはboolを除く整数0..255、未知op/余分なfield/不正値を実行前に拒否。store missはfillしてから更新。3と255はblock末尾、0/4は不同block。正常な空traceと入力拒否を分ける。

限界: flushはこのmodelのdirty反映だけで、fsync・耐久性・メモリ順序保証ではない。power loss、coherence、ordering、任意cache設計、実CPU、cycle/性能は未実証。原典は[source locator](sources.json)、未教材と次3実験は[coverage](coverage.json)、[検証記録](VERIFICATION.md)、[有限Skill](skills/atlas-write-policy-dirty-eviction/SKILL.md)。全Subject/Atlas完成ではない。

記録は`python3 verify.py --record attempt-01`（未使用名限定）。通常checker/route/UIは固定attempt-01を読む。`--seal-record`はrawを保全し現在QA/source receiptを記録する。旧教材の原票は更新しない。

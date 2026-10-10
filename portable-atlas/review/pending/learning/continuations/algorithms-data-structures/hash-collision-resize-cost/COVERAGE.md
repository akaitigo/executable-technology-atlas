# 今回の対応と未教材

対応: 固定mod整数key、listで表現するchaining、put/find/delete、同key更新、負key・空・閾値等値、初期容量2からload>1で倍増、比較数とrehash entry移動数、同じ列の固定/倍増比較、正常とbucket全削除の反例、hashなしlist oracle、有限24条件。

未対応: shrink/hysteresis、open addressing、tombstone、乱択・universal hashingの実装と確率検証、文字列/prehash、mutable key、一般入力列、並行性、allocator/cache/実時間/メモリ計測、最悪/期待/償却計算量の一般証明、Karp-Rabin、他の木・heap・graph・DP。Python dict内部の再現ではありません。MIT講義全体と分野全体を今回の成功で埋めません。Core atlas audit/npm gateは今回の割当外・未実行です。

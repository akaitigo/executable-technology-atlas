# 有限契約と先に固定した手表

整数keyは -32..48、valueは1..2文字の大文字、操作列は下記6列のみです。Pythonのbool、float、文字列keyを拒否します。初期容量2、h(k)=k % m。負key -1 の余りは m-1。chain末尾に新keyを追加し、既存key更新はnを増やしません。一致keyのみdelete、find/deleteの不在はfound=false/value=nullです。

新key挿入後 n>m なら倍増し、n==m では拡張しません。更新・削除で拡張しません。縮小なし。rehashは旧bucket昇順、chain順で全entryを新bucketへ直接追加します。新挿入entryも移動数へ含め、rehash内でkey一致比較をしません。

| 列 | 比較 固定/倍増 | 移動 固定/倍増 | 最終容量 固定/倍増 |
|---|---|---|---|
| collision: 0,2,4→find2→更新2→delete2→find0/2/4 |14/9|0/3|2/4|
| distributed: 0..5→find5→delete1→find1 |12/4|0/8|2/8|
| persistent: 0,8,16,24,32,40→find40/48 |27/27|0/8|2/8|
| threshold: 0,2→更新2→find2 |5/5|0/0|2/2|
| negative: -1,1→find-1→delete1→find-1/1 |6/6|0/0|2/2|
| empty: find0/delete0 |0/0|0/0|2/2|

正常と意図異常delete-whole-bucketを各方針で実行します。異常は一致keyを見つけた時に同bucket全体を消す誤りです。衝突しない対象では異常と正常が一致するため、常にFAILになるとは限りません。

比較数は訪問したchain entryごとのkey一致判定数、移動数はrehashで新bucketへ配置したentry数です。hash計算、bucket走査、allocation、list削除後のshift、oracle、図描画を含みません。単位の異なる費用を実時間や期待O(1)保証に変換しません。modと2の累乗容量は意図的な教材選択で、分布改善を保証しません。

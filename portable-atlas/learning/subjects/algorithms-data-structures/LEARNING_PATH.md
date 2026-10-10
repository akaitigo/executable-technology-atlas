# アルゴリズムとデータ構造を、不変条件から広げる

この文書は既存の [README](README.md) を置き換えない補足ガイドです。既存実装・原票・QA・source束縛を変更していません。次案は実行証拠ではありません。有限教材の補足であり、分野全体の学習完了を示すものではありません。

## 1. 前提を確認する

配列、0始まりのindex、整数比較、反復、半開区間を確認します。配列[1,3,5]の長さは3、要素indexは0/1/2ですが、末尾の挿入境界は3です。[lo,hi)の要素と、挿入位置pの候補lo≤p≤hiを紙に書き分けてください。実装を追う時はJSの変数・if・whileが前提です。

次に、入力の前提、返す結果の契約、ループ中に保つ不変条件、減少する量、費用の数え方を分けます。速さを議論する前に、何を返すべきか、どの入力に使えるかを決めます。

## 2. 主要概念の見取り図

データの表現 → 操作と契約 → 正当性・停止 → 計算量 → 実測・メモリ、の順で学びます。探索には線形・二分・hash・treeという選択があり、整列・更新・所有の費用も関わります。graphでは隣接関係と訪問状態、DPでは部分問題と再利用、greedyでは局所選択が最適性を保つ根拠が必要になります。

今回のlower boundは最初のa[i]≥xの位置、なければnを返します。値の存在は終了後に別検査します。不変条件を保つことと、毎回hi−loが減ることは別の責務です。

## 3. 正常・意図異常から実装と原票へ

[画面](index.html) → [README](README.md) → [search.js](search.js) → [検証記録](VERIFICATION.md) → [Node原票 attempt-03](observations/node-20261005-attempt-03/runtime.json) と読みます。記録の世代はVERIFICATIONで確認してください。起動・再現方法はREADMEにあり、この補足作業では実行していません。

正常はhi=midで候補を保ちます。意図異常Aのhi=mid−1は[1,3,5]から3を見落とします。異常Bのlo=midは長さ1で進まず、診断器が停止します。異常Cは未整列[3,1,2]へ強行し、3を見落とします。正常は前提違反を拒否します。重複は最初の位置、空列は挿入位置0・一致なしです。

16件・目標なしの比較数と、先頭一致で線形探索が1回で済む例を並べ、前提確認の比較数を別に読みます。保存traceの図は実時間の測定ではありません。

## 4. 実務判断と限界

整列済み・反復検索なら二分探索を検討できます。小さい列、先頭付近、未整列、単発検索では準備費用も含めて線形探索を比較します。境界契約を混ぜない、停止の根拠を別に持つ、空・重複・前提違反を試す、というreviewにも使えます。

最大32要素、有限整数、固定比較関数です。整列確認や診断走査を含む教材全体をO(log n)とは呼べません。実時間・メモリ・大量入力・並行性・学習者理解度は未測定です。[scope.json](scope.json)の未教材を今回の成功で埋めません。

## 5. 主要未教材を問いへつなぐ

| 概念 | 学ぶ問い | 接続 |
|---|---|---|
| 整列・安定性・比較モデル | 同値keyの順序を保つ必要がある？ 前処理費用をいつ回収できる？ | 次案1、MIT Lecture 3 |
| hash・衝突・load factor・償却 | 同じhash値でも別keyを保持できる？ 再配置費用を誰が負担する？ | 次案2、Lecture 8/9 |
| list/stack/queue・tree/heap | 探索だけでなく更新・所有・優先度の費用は？ | MIT lecture一覧 Unit 2。専用実験は未整備 |
| graph・BFS/DFS・最短路 | 初めて見つけた経路が最短になる条件は？ cycleをどう止める？ | 次案3、Lecture 13/14。重み付きは別教材 |
| DP・greedy・backtracking | 同じ部分問題を何回解く？ 局所選択で全体最適を失わない？ | 次案4、Lecture 19。greedy証明は別課題 |
| 近似・乱択・並行構造 | 誤差確率や競合を、何の仮定で制限する？ | 専用原典・実験は未選定 |
| 実測・メモリ・計算量 | 比較数が少なければ速い？ cacheやallocationも含めたか？ | 実機実験は未実施。比較数から速度を推定しない |

## 6. 次の4実験（すべて未実装・未実行）

1. **安定整列と検索の準備費用**：同じkeyと元IDを持つ小配列をinsertion sortとmerge sortへ与える。昇順・降順・重複を比較し、key順、同値key内のID順、比較数・移動数を記録する。独立oracleはkey順と同値順保持を別に検査する。整列後の反復検索費用も整列費用と別計上する。原典はMIT公式 [Lecture 03: Insertion sort, merge sort](https://ocw.mit.edu/courses/6-006-introduction-to-algorithms-fall-2011/resources/mit6_006f11_lec03/)。
2. **hash衝突と拡張**：有限整数keyと固定hashでchainingを実装し、同じbucketへ衝突するkey列と分散する列を比較する。find/deleteの一致key、chain長、比較数を記録し、単純list oracleと照合する。さらに容量拡張あり/なしで同じ挿入列の再配置数を比較する。平均計算量を保証する乱択仮定は別に整理する。原典はMIT公式 [Lecture 08: Hashing with chaining](https://ocw.mit.edu/courses/6-006-introduction-to-algorithms-fall-2011/resources/mit6_006f11_lec08/) と [講義一覧 Lecture 9: Table doubling](https://ocw.mit.edu/courses/6-006-introduction-to-algorithms-fall-2011/pages/lecture-notes/)。
3. **BFSとDFSの経路**：同じ有限・無重み・有向graphにcycleと到達不能頂点を入れる。固定隣接順でBFS/DFSの発見順、parent、経路長を比較し、独立な距離層oracleと照合する。DFSの最初の経路を最短と呼ぶ反例を残し、visitedで停止できるか観測する。原典はMIT公式 [Lecture 13: Breadth-first search](https://ocw.mit.edu/courses/6-006-introduction-to-algorithms-fall-2011/resources/mit6_006f11_lec13/) と講義一覧Lecture 14: DFS/topological sorting。
4. **部分問題の再利用**：Fibonacciを小さいn=0..20で素朴再帰、memoization、bottom-up計算する。同じ値を独立の反復表で照合し、呼出し数、異なる部分問題数、保存entry数を比較する。実時間とは別の数値として扱う。cacheへ誤った値を置いた場合の不一致も診断する。原典はMIT公式 [Lecture 19: Memoization, subproblems, guessing, bottom-up](https://ocw.mit.edu/courses/6-006-introduction-to-algorithms-fall-2011/resources/mit6_006f11_lec19/)。

既存lower-bound実装にこれらの機能があるわけではありません。新実装・独立oracle・観測が必要です。4本でも分野全体は閉じません。

## 7. 原典の確認状況

既存教材の一次資料は画面のPython bisect_left仕様、固定版CPython実装、Cornell loop invariant講義です。新規MIT locatorは2026-10-05にread-only webで講義一覧のLecture 3/8/9/13/14/19と、3/8/13/19の公式resourceページの題名・説明・配布入口を確認しました。配布PDF全文の追加精読は未実施で、本文確認済みと扱いません。新規MIT URLに取得失敗はありません。第三者本文・図・コードは転載していません。

この追加で実験・runtime・実UI再QAを実施したとは主張しません。既存証拠のhashやsource束縛は再封印していません。

# rootからの到達性をmark/sweepで追う

object間に参照があるだけでは生存しない。A→B→C→Bへroot AがあればABCは残るが、rootから届かないD↔Eは回収される。最初のrootを見落とす故障では、live ABCまで誤回収される。合成heapの各stepと独立graph oracleで違いを観察する教材。

```sh
python3 -B serve.py
```

表示された動的`http://127.0.0.1:<port>`を開く。Python標準libraryだけを使い、依存追加・外部通信・ログインは不要。停止はCtrl-C。隔離環境のbind/connect拒否は別の失敗として保存する。今回の実表示はOS承認された同じ一時serverで確認する。

fixtureとroot探索を選び、「live objectを誤回収する？」を予測して実行する。結果は独立oracle到達集合・pre-sweep mark集合・回収集合・残った辺・失われたrootを示す。stepは初期状態から最終状態まで選べる。「前/次のstep」でqueueとgraphの色を追う。表示は1始まり、rawのstep番号は0始まり。

## 学習順序

1. rooted-cycle/全rootで実行し、step 1へ戻す。A seed→scan A→scan B→scan Cのqueueを手表と比べる。
2. D/Eに相互参照があるのに回収される理由をrootからのpathで説明する。keep時のmark解除も確認する。
3. root見落としと比較し、ABCが誤回収されること、宣言root Aが失われることを確認する。
4. masked-rootではCからBへ届くため故障が露呈しない。root空・全root・自己cycle・空heapも比較する。
5. root移動前後を比較する。未回収の同じgraphでroot A,D→F,Dを設定した独立snapshotで、回収集合はFG→AGへ変わる。先にGCしてFを回収してから復活させたとは扱わない。

画面のgraphは元の全辺を示す。sweep途中のgarbageが既に除いたgarbageへ向くこともある。完了後の残る辺は別に照合し、不正な辺を削って隠さない。色の意味は画面のlegendにあり、金枠は宣言root（見落としたrootも含む）。条件変更は旧結果を消し、resetはrooted-cycle/全root/未回答へ戻す。

## 実装と再現証拠

```sh
python3 -B verify.py
python3 -B route.py
```

[CONTRACT.md](CONTRACT.md)は実装前の型・上限・手表。[collector.py](collector.py)はenqueue時markとFIFO、元のobject順sweep。[oracle.py](oracle.py)はproducer helperを呼ばない反射的transitive closure。9fixture×2探索=18比較、19入力拒否、6実際の故障変種を検証する。normalの到達node保存・残った辺の宛先・root保持・GC後mark解除、故障の誤回収も照合する。入力を変更しないことも確認する。

初回rawは`observations/attempt-01.json`、core先行証拠・実IAB転記・HTTP・失敗・cleanup・receipt・最後のread-only proofは同directoryへ保存する。[COVERAGE.md](COVERAGE.md)で経路と限界を分ける。source viewerはallowlistの実ファイル全文を表示する。raw JSONは実応答、graphはそのsnapshotの再描画であり、実heapの撮影ではない。

## 原典と限界

[Crafting Interpreters 著者repository](https://github.com/munificent/craftinginterpreters/blob/master/book/garbage-collection.md)のMark-Sweep Garbage Collection、Marking the Roots、Tracing Object References、Sweeping Unused Objectsを参照した。著者のC VMを転載・実行したものではない。既存の著者サイト取得不能記録から本文不存在とは断定せず、今回取得できたrepository本文を使う。

数学的な有限object graph simulationで、実memoryをfreeしない。実アドレス、allocator、停止時間、GC速度、moving/generational/concurrent、weak参照、finalizerは未検証。FIFOやstep数を実GCの速度へ拡張しない。既存名前解決教材への別の増分。全Atlas audit/npm gate、commit、push、公開は未実行。

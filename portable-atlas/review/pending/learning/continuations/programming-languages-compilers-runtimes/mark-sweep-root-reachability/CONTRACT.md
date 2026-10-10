# 先に固定する合成heap契約

objectは`{id, refs}`のlist、rootはIDのlist。IDはASCII大文字から始まる1..4文字の大文字/数字。objectは0..16個、辺は合計48本以下、各refs/rootは16個以下。未知field、重複ID/辺/root、unknown root、dangling input edge、型違い、bool/numeric IDを拒否。全参照は強い有向辺。weak reference、finalizer、実アドレス、allocator、実memory、停止時間、GC性能、moving/generational/concurrent GCは対象外。

各実行は入力heapの新しいsnapshotから始める。root移動前後は同じ**未回収**graphへ別のroot集合を設定した独立比較であり、先に回収したobjectを復活させる操作ではない。

## producerの順序

normalは宣言順の全rootをmarkしてFIFO worklistへ入れる。missing-first-rootは最初のroot1個だけをseedから省く故障対照（root空なら省くものなし）。元の宣言rootは正しさの基準として保持する。

markはenqueue時に行い、既にmarkされたobjectを再enqueueしない。FIFOから1個popし、refsを入力順にscan、未mark参照先をmark/enqueue、popしたobjectをblackにする。各root seed/omit、各scan、mark完了をsnapshotする。white=未発見、gray=mark済未scan、black=scan済。mark完了後にpre-sweep marked集合を保存する。

sweepは元のobject順に1個ずつkeep/reclaimする。keepはmarkを解除して次回GCへ備える。reclaimは合成集合から除くのみ。traceにはgray/black/current mark、kept/reclaimed、残っているobjectと辺を保存する。sweep途中の未回収garbageが既に除いたgarbageへ向くことはあり、残る辺の宛先保証は**完了後**について照合する。残る辺を後から削って不具合を隠さない。完了後mark bitは空、結果のmarkedはpre-sweep集合。

独立oracleはID間の反射的transitive closureをWarshall行列で求め、元rootから到達できる集合を出す。producerのqueue/scan helperを呼ばない。normalではmarked=reachable、reclaimed=全object−reachable、live objectを回収しない、残る辺の宛先がsurvivor内にある、declared rootが残ることを照合する。故障結果はpremature_reclaimed=reachable∩reclaimed、dangling_roots/edgesで診断する。

## 実装前の手表

基本graph: A→B、B→C、C→B、D→E、E→D、F→C、G→∅。

|fixture/root|normal reachable / reclaimed|最初rootを省くと|
|---|---|---|
|rooted-cycle / A|ABC / DEFG|到達empty、live ABCを誤回収|
|unrooted-cycles / G|G / ABCDEF|live Gを誤回収。cycle内の参照だけでは生存しない|
|move-before / A,D|ABCDE / FG|DEだけ残り、live ABCを誤回収|
|move-after / F,D|BCDEF / AG|DEだけ残り、live BCFを誤回収|
|empty-roots / empty|empty / ABCDEFG|同じ。faultの効果なし|
|all-roots / A..G|ABCDEFG / empty|BCDEFG / A。Aを誤回収|
|masked-root / B,C|BC / ADEFG|CからBへ届き同じ集合。faultがこの条件で露呈しない|
|self-cycle / H→H,I→∅、root H|H / I|live Hを誤回収|
|empty-heap / objectなし/rootなし|empty / empty|同じ。初期/mark完了/完了の3step|

rooted-cycle normalのmark手順: seed Aでqueue[A]、scan Aでqueue[B]/black[A]、scan Bでqueue[C]/black[AB]、scan CはBを再enqueueせずqueueempty/black[ABC]。その後A/B/Cをkeep、D/E/F/Gをreclaim。normal14step、故障11step。root移動前後のnormalは各17step、回収集合はFG→AGへ変わる。step数は可視化イベントの数で、CPU時間ではない。

## 原典

[Crafting Interpreters 著者repository](https://github.com/munificent/craftinginterpreters/blob/master/book/garbage-collection.md)のMark-Sweep Garbage Collection、Marking the Roots、Tracing Object References、Sweeping Unused Objectsを2026-10-05 UTCに確認した。著者はCのVMを扱うが、この教材は独自の有限graph simulation。既存資料の著者サイト取得不能記録は本文不存在の証拠とせず、今回確認できたrepository本文を参照する。

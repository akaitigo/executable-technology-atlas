# 観測範囲

|経路|実測|限界|
|---|---|---|
|事前契約/手表|9graph-root snapshot、rooted queue/black、回収集合|有限fixtureのみ|
|producerと独立oracle|18比較。FIFOとWarshall closureを別実装|同じsynthetic inputを使う|
|正常invariant|到達nodeを回収しない、残る辺の宛先、宣言root、GC後mark解除|残る辺の宛先保証は完了後|
|故障対照|root1個見落としでpremature回収、別rootで隠れる条件|実VMのroot探索ではない|
|拒否|unknownroot/danglingedge/duplicateID/型/上限など19件|CLI入力契約の有限拒否|
|故障変種|refs省略/辺逆転/incoming seed/keep逆転/sweep前mark解除/keep後mark未解除の6件|witnessをrawに残す。一般mutation scoreではない|
|実IAB|18条件、rootedの全14step SVG/queue、root移動/故障/予測/reset/source|CUA実操作とDOM。graphはsnapshotの再描画|
|HTTP|18正常応答と13不正JSON等の拒否|自分の一時localhostだけ|
|画像|実UIのtool capture|inlineのみ。保存画像/path/hashを捏造しない|
|封印|receiptとread-only hash/mtime proof|module有限検証のみ、全Atlas gate未実行|

browserの集合は別に入力した手表literalと比較し、SVG状態は実DOMから読む。その後だけCLI値を手動転記templateに使い、CLI成功を実表示に置き換えない。具体範囲はbrowser.jsonに記録する。Python 3.9.6、標準library、Codex IABを利用。

実memory/allocator/停止時間/GC性能/moving/generational/concurrent/weak/finalizer、保存download、公開は未確認。保護port53478/60285/50835とtab6/7/17へ操作せず、所有server/tabのみcleanupする。sandbox bind/connect拒否も保存する。

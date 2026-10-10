# 2lockのdeadlockとretry cycle

前提: 集合、状態tuple、有向graph、guard、atomic step。[既存mutexのsafety教材](../../../subjects/formal-methods-verification/README.md)と[学習経路§6実験2](../../../subjects/formal-methods-verification/LEARNING_PATH.md)から、資源待ち・進行へ進む有限単元です。Python標準ライブラリだけを使います。

1. 逆順なら両者が1lockずつ保持したまま動けなくなるか予想する。解放retryを加えると必ず完了するだろうか。
2. `python3 verify.py`で保存実行と独立期待値を照合。`python3 serve.py`のURLで[UI](index.html)を開く。
3. 条件を選び予想を入れ、比較する。traceのstepを操作してowner、要求lock、enabled actionを追う。retryはprefixと閉じたcycleを一周以上動かす。
4. 原典・実装・rawに戻り、答えと実務判断を説明する。条件変更は予想・比較結果・答えをリセット。不正stepでも既存の予想対照を維持する。

主要概念・状態契約: tuple=(pc0,pc1,ownerL0,ownerL1)。owner=-1/0/1は空き/P0/P1。pc0=取得前、1=最初のlock保持、2=両lock保持、3=一度完了し所有なし、4=retry専用の失敗観測済み。pc2からの完了は両lockを一つのatomic stepで解放し、完了後は再開しない。stutteringを辺に数えない。未完了で非stuttering辺0がdeadlock、両pc3で辺0は正常な終了。

| 条件 | 手で固定した期待 | 意味 |
|---|---|---|
| 逆順 P0:L0→L1 / P1:L1→L0 | P0 first、P1 firstの2遷移で(1,1,0,1)、deadlock | 相互待ち |
| 同順 両者L0→L1 | P0完了解放→P1完了解放、到達deadlock0 | 最後の遷移0は完了 |
| 逆順＋失敗観測・解放retry | prefix2の後、両者失敗観測→両者解放→両者firstの6辺cycle | 動いても完了しない許容schedule |

retryはpc1でsecondが占有されているとpc4へ失敗を観測し、別stepでfirstを解放してpc0へ戻る。観測後にsecondが空いてもpc4は解放を続けるという独自契約。単一atomic try/release版と同じgraphとは主張しない。探索器は最短のnoncompletion cycleも別に記録する。手書き6辺cycleは両processが動く具体例で、最短とは呼ばない。

Safetyは両者が同時に両lockを保持しないこと。Liveness/terminationは求める進行がいつか起きるかを問う。同順の非stuttering graphはcycleなし・未完了sinkなしだが、無限stutteringや実schedulerを許した一般的終了保証ではない。retry cycle存在は公平性付き必然のstarvationではない。[Lamport Session9 §1/§3](https://lamport.azurewebsites.net/tla/tutorial/session9.html)の進行条件と各process進行の違いを原典で読む。本模型は一度完了、原典の反復mutex algorithmと同一ではない。

独立期待値: [事前手書きtraceと契約](hand-oracle.json)、[lock所有/要求表とsource-target対のedge判定](source.html?file=oracle.py)。oracleはproducerをimportせず、pcから所有集合を構成して全候補の辺を別判定し、集合の層ごとの閉包で到達・距離を求める。[producer BFS/cycle探索](source.html?file=model.py)、[checker](source.html?file=verify.py)、[全実行raw](observations/attempt-01/raw.json)をつなぐ。

実務判断: 無効な所有状態、失敗の観測、解放、再取得の操作境界を固定する。deadlock freedom・safety・各process進行を別の条件として検査する。cycleを見たらenabled履歴とfairnessの対象を確認する。

入力契約: 固定3mode、pc/ownerはboolを除く列挙整数、所有集合とpcが一致する状態だけを探索。UI stepは現在path内の整数、負数/範囲外/空欄は拒否。正常な完了sinkと拒否を混ぜない。

限界: 原典algorithm再実装・PlusCal/TLC・形式証明・実thread/OS lock・実CPU/weak memory・公平性付き定理は未実施。原典は[source locator](sources.json)、未教材と次3実験は[coverage](coverage.json)、[検証記録](VERIFICATION.md)、[有限Skill](skills/atlas-two-lock-deadlock-livelock/SKILL.md)。全Subject/Atlas完成ではない。

明示記録は`python3 verify.py --record attempt-01`（未使用名限定）。通常checker/route/UIは固定attempt-01を読む。`--seal-record`は既存rawを保持してQA/source receiptを更新する。旧単元は変更しない。

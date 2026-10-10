# 分散システムを学ぶ道筋

この文書は[2 replicaの既存教材](README.md)から、収束、因果順序、一貫性、業務条件を分けて学ぶための補足です。有限教材の補足であり、分野全体の学習完了を示すものではありません。以下の次実験はすべて未実行です。

## 1. 前提と仕組み

状態遷移、graphの到達可能性、部分順序と全順序、集合、最大値の交換・結合・冪等性を理解します。replicaが同じ値を持つことと、その値が利用者の要求を満たすことを分けます。

学ぶ順序は **local状態とmessage → partitionと配送 → 因果順序と論理時計 → mergeと収束 → 操作historyの一貫性 → 業務invariant → consensus・永続化・運用** です。

- 同processの順序とsend→receiveの関係からhappened-beforeを作ります。再生画面のglobal stepを因果関係に加えません。
- 論理clockは因果順序に沿うlabelです。clockの大小だけでは因果関係の逆向き推論はできません。
- tie-breakによる全順序は並行書込みから勝者を選べますが、物理時間の最後を測ったことにはなりません。
- max mergeの収束には必要な書込み情報が届く条件があります。収束と、値の保存・linearizability・在庫等の条件は別です。

## 2. 予想から既存実測へ

[UI](index.html)、[model.py](model.py)、[CLI原票](observations/comparison.json)、[QA](QA.md)を往復します。この文書作成ではsimulator、server、UIを実行していません。

| 場面 | 保存済み結果 | 予想との比較 |
|---|---|---|
| partition中のlocal書込み後 | A=alpha-2、B=beta | local書込みはできても値は違う |
| link復旧直後 | まだ同じ不一致 | 復旧とmessage配送は別 |
| A2,A1,B1を配送、arrival | A=beta、B=alpha | 全部届ければ一致、という予想への反例 |
| 同じ配送、version-max | 両方alpha-2 (2,A) | 固定書込み集合のmaxと一致 |
| 最後に古いA1を再配送 | arrivalのBはalpha、maxはalpha-2 | staleなmessageの採否が異なる |

正常なmax経路は、immutableな書込みlabelを比較して大きいものだけ採用します。arrival経路の不一致は到着順上書きの反例です。固定3 messageの全6順でmaxは6/6 Oracle一致、arrivalのreplica一致は0/6と記録されています。duplicate入り24 positional permutationsは12 unique schedulesです。これらはPython内部の有限計算で、実networkの障害・lossを発生させた結果ではありません。

受信clockはmaxに1を足して進みますが、書込みversionを受信clockへ付け替えません。A2とB1は並行でも(2,A)が勝ちます。最終registerからalphaとbetaは失われるため、一致を「全書込みを保存」と読みません。独立Oracleは配送関数を呼ばず全書込み集合をsortしますが、任意の分散実行の証明ではありません。

## 3. 実務で何を判断するか

まず守る契約を、最終収束、因果順序、完了した操作の観測順、業務invariantのどれかとして明示します。複数の要件があればそれぞれ検査します。勝者を一つ選ぶmergeを採用する前に、捨ててよい更新か、競合を利用者へ見せる必要があるかを決めます。

partition中の書込みを継続するときは、永久loss、再送、重複、再起動、membership変更を別の状態遷移として扱います。clockやmessage IDの保存も必要です。既存max-registerからconsensus、CAP一般、残高安全性、実transport耐障害性を結論しません。

## 4. 一次資料への道筋

| 原典とlocator | 読む目的・確認範囲 |
|---|---|
| [Lamport, Time, Clocks, and the Ordering of Events (1978)](https://lamport.azurewebsites.net/pubs/time-clocks.pdf)、刊行pp.559–561、The Partial Ordering / Logical Clocks / Ordering the Events Totally | 因果順序、clock条件、全順序。既存registerは論文の相互排他algorithmではない |
| [Herlihy & Wing, Linearizability (1990)](https://cs.brown.edu/people/mph/HerlihyW90/p463-herlihy.pdf)、§2.1 Histories / §2.2 Definition of Linearizability、刊行pp.467–469 | invocation/responseと実時間の先行関係を満たす逐次history |
| [Shapiroほか, A comprehensive study of CRDTs, RR-7687候補](https://inria.hal.science/inria-00555588/document) | CRDT群を広げるための取得候補。今回はbot検査画面で本文未確認。アルゴリズム根拠に使用していない |

既存資料と未教材の記録は[coverage.json](coverage.json)にもあります。収束を学んだ後は、別の一貫性の定義を原典へ戻って確認します。

## 5. 未教材の問いと次実験

| 未教材 | 問い | 次の入口 |
|---|---|---|
| causal consistency・vector clocks | clock大小と因果関係をどう区別するか | 実験1。vector clocksの算法自体は別教材 |
| linearizability | 完了した書込み後の読取りはどの値を返せるか | 実験2 |
| 業務invariant・multi-key transaction | 収束しても予約数等の条件を破らないか | 実験3 |
| CRDT群・anti-entropy | 並行更新をどこまで保存し、未配送情報をどう交換するか | 未取得CRDT原典の本文確認と別教材が必要 |
| consensus・leader・membership・Byzantine | 合意の安全性と進行条件は何か | 別の原典・model・検査が必要 |
| transport・retry/ack・durability/restart | lost ack、永久loss、crashで何が失われるか | 実runtimeの有限障害計画が必要 |
| CAP形式化・運用性能 | failure modelと利用者契約をどう定義・測定するか | この2 replica計算では未検証 |

## 6. 次の実験案（3本、すべて未実行）

1. **event graphと論理labelを照合する。** 独立した小さなevent fixtureにprocess内edgeと同一messageのsend→receive edgeを置き、推移閉包を求めます。並行な2書込みにも異なるclock値を与え、予想は「因果があればclockは増えるが、clockが小さいだけでは因果を示さない」です。全event対を先に分類した手書き表と到達関係を照合し、画面stepをedgeに混ぜた故障版も比較します。原典はLamportのPartial OrderingとClock Conditionです。vector clock実装や実時計測定にはしません。

2. **完了した単一register historyのlinearizabilityを調べる。** 初期0、write(1)、readのinvocation/responseを合成し、write完了後に始まるreadが0を返す反例と1を返す正常例、両操作が重なる例を作ります。予想は完了後のstale readが拒否され、重なる場合は合法な順序が複数あり得ることです。完了操作の全permutationから実時間の先行関係を満たすものを選び、独立した逐次register仕様で返却値を照合します。原典はHerlihy & Wing §2.1〜2.2です。pending操作、multi-object、実DBhistoryは対象外とし、既存max原票をこの未実行checkerのpassに見せません。

3. **収束と予約数の条件を分ける。** 在庫1の合成modelでpartition中にA/Bが各1件の異なる予約IDを受理し、復旧後に予約集合をunionする場合を作ります。予想は両replicaが同じ2件へ収束しても「受理数≤1」に違反することです。受理応答・local状態・配送・最終集合を手書きtraceと照合し、partition中の新規受理を止める対照modelでは安全性と処理継続の違いを記録します。Lamportの並行eventの定義へ接続した独自説明modelで、特定CRDTやCAPの証明ではありません。取消・補償・合意protocolは別の問いとして残します。

## 7. 資料の取得・検証状況

2026-10-05にLamport著者サイトのPDF本文と、Herlihy著者の大学サイトのPDF本文を取得しました。既存のMicrosoft掲載Lamport PDFは取得時Internal Errorだったため、著者サイト版を参照しました。`https://cs.brown.edu/~mph/HerlihyW90/p463-herlihy.pdf`もInternal Errorで、上表の`/people/mph/`版は取得できました。

CRDT候補はHALの上記URLでbot検査画面となり、`https://pages.lip6.fr/Marc.Shapiro/papers/RR-7687.pdf`もInternal Errorでした。本文を確認できず、CRDTの実装・該当節検証は行っていません。取得失敗を資料不存在とは扱いません。第三者本文・図は教材へ保存していません。

追加したのはこの文書だけです。model、checker、server、UI、global gateは実行せず、既存原票・QA・digestを更新していません。次実験の予想は新たな実測証拠ではありません。

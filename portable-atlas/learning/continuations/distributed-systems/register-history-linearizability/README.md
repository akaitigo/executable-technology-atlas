# 単一registerの完了historyをlinearizabilityで検査する

[元の学習経路 §6 実験2](../../../subjects/distributed-systems/LEARNING_PATH.md)を独立continuationとして制作した。初期0の単一registerに対し、合成write/readのinvocation/responseから合法な逐次順序を探す。元の2replica収束原票をこの検査のpassとして流用せず、元教材・入口を変更しない。

これはPython内部で合成historyを検査した実行であり、実分散通信、実DB、障害注入、物理時計計測ではない。画面barのtickは固定の合成event順。1historyの合法性を、全実装や将来の全historyの保証へ広げない。

## 前提と入力契約

単一registerは初期0。write(v)はstateをvへ置き換え、応答は文字列`ok`。readはその逐次順で直前に書かれた値、writeがなければ0を返す。固定domainは整数0..2でbool不可。操作ID/client、inv/resと返却値を持つ完了操作1..4個だけを受け取る。

inv/resは整数0..100、全eventで異なる合成tick、inv<res。同clientは重複区間を持たず、逐次processとして扱う。readにargはなく、writeはargを必須とする。未知op、不正response、同client重複、時刻逆転、pendingは **INPUT_REJECTED**。入力拒否では候補探索を実行しない。pendingの一般的linearizabilityを「違反」と判定したのではなく、この教材の対象外として拒否する。

完了AのresponseがBのinvocationより先ならA→Bの実時間precedence edgeを置く。この関係を全て保存した逐次候補だけを許し、register仕様を満たすかを調べる。重なるinterval同士には、その重なりだけからedgeを追加しない。

## 予想→操作→比較→答え

画面でLINEARIZABLE / NOT_LINEARIZABLE / INPUT_REJECTEDを予想し、historyを選んで実検査する。timeline→precedence→候補順→read mismatch→原典/実装→答えを追う。候補prefixの生traceは開閉できる。画面実行は保存rawを更新しない。

| 完了history | 手書き期待 | 合法順序・判断 |
|---|---|---|
| write1完了後read1 | LINEARIZABLE | w1→r1 |
| write1完了後read0 | NOT_LINEARIZABLE | w1→r1が必須だがreadは1を返すべき |
| write1と重なるread0 | LINEARIZABLE | r1→w1で初期0を読む |
| write1と重なるread1 | LINEARIZABLE | w1→r1で1を読む。response順r1→w1は失敗する |
| 2write/2readの重なり | LINEARIZABLE | w1→r1→w2→r2。r1完了後r2開始のedgeを守り1→2を読む |
| 逐次2write後read2/read2 | LINEARIZABLE | w1→w2→r1→r2 |
| 逐次2write後read2/read1 | NOT_LINEARIZABLE | w2の後、writeなしで1へ戻るreadは仕様に合わない |
| 初期read0/read0 | LINEARIZABLE | r1→r2 |

schema-valid 8historyは合法6・合法候補なし2。入力契約外の6fixtureは期待入力拒否として別計上し、合法historyの成功件数に足さない。preview bindのOS拒否等の実行失敗も別記録する。

「response順にsortして仕様を調べれば十分」は誤り。`overlap-read-one` はresponseがr1→w1でも、区間が重なるためw1→r1を選べる。response-sortの失敗から、このhistory全体が非linearizableとは結論しない。重なるread0/read1は別historyでどちらも許容され得るので、readの実戻り値を含めて検査する。

## 仕組みと独立oracle

`model.py` は入力検査→実時間precedence DAG→available nodeのbacktracking。prefixでread値が現在stateと違えばその枝を切り、合法な全candidateを保存する。traceにavailable choices、apply前後state、readの期待値/返却値、合法候補を記録する。

`check.py` はproducerをimportしない。全operation permutation（最大4!=24）を列挙し、直接の時刻不等式で先行関係を検査する。別のliteral sequential specでは各readのprefix内の最後のwriteを調べる。手書き `oracle.json` のstatus/witness/response-sort期待値と、独立全permutation集合、producer集合を照合する。5破損（stale偽witness、edge欠落、sort誤判定、入力理由差替え、mismatch期待値改竄）を拒否する。

独立oracleもこの有限register仕様・complete historyの範囲であり、任意の並行実装証明やscale評価ではない。

## 原典・実務の採取境界

[Herlihy & Wing, Linearizability (1990)](https://cs.brown.edu/people/mph/HerlihyW90/p463-herlihy.pdf) §2.1 Histories（刊行pp.467–468）でinvocation/response、well-formed process、pendingを確認。§2.2（pp.468–469）でresponse-before-invocationの部分順と合法逐次historyを確認した。原論文はpendingの拡張も定義するが、この教材はcomplete操作だけに制限する。

実務でhistoryを採取するなら操作ID/client/object、要求引数、invocationとresponseの対応、返却値、timeout/pendingを記録する。別hostのclock数値を無条件に1本の正確な実時間順として使わず、observer・時刻uncertainty・欠損を明示する。今回のtickは曖昧さのない合成event列なので、実clock同期の問題を解決したとは言えない。合法性と可用性・性能・durability・収束は別の要件。

## 再現と証拠

このdirectoryを作業位置にする。Mac既存Python標準libraryのみ。

```sh
python3 -B check.py
python3 -B runner.py --inspect-evidence
python3 -B runner.py --case overlap-read-one
python3 -B server.py
python3 -B runner.py --record
python3 -B skills/atlas-register-history/route.py register-history
```

checker/inspect/routeは保存証拠をread-onlyで見る。`--case` はfixed historyを実検査。previewは空きdynamic 127.0.0.1 portを起動時に表示、終了はCtrl-C。原票保存は明示 `--record` のみ、新しいUTC directoryへ保存し旧rawを上書きしない。

採用rawは `observations/20261005T112523779101Z/raw.json`。各historyのUTC/runtime、input、status/reason、edges、合法候補、bad sortの順/理由、探索trace、model/runner/history/oracle source bindingを記録。`observations/qa.json` と `observations/verification.json` に実IAB操作、capture保存可否、限定Skill、source/raw/QA hash、通常検査のhash/mtime不変、所有resource cleanupを記録する。通常sandboxのpreview bind失敗は `sandbox-preview-failure.txt` に保全。

## 未教材と次の3有限実験案（未実行）

| 問い | 次の具体入力・操作 | 比較観測 | 原典locator |
|---|---|---|---|
| pending操作の効果をどう扱うか | 初期0、pending write1と完了read1/read0。応答追加候補とpending除去候補を明示列挙 | complete(H')と合法順を比較。pendingを一律失敗/成功へ丸めない | 同論文§2.1 pending/complete、§2.2 extension |
| 曖昧な時刻をどう扱うか | 合成inv/resに±1tick uncertainty、responseと別invocationの区間が接触/重複する2例 | 確定edgeと不確定edgeの候補を分け、同じ観測から判定不能な場合を表示 | 同論文§2.2 real-time precedence。uncertainty modelは別途固定する教材設計 |
| 2objectの履歴をどう分けるか | register X/Yへ各2操作、object別合法例とXだけstale例を投入 | object projection、個別witness、全体順序の適合を比較。multi-key transactionと混同しない | 同論文§3.1 Locality/Theorem 1（この単元では未実装） |

未網羅はpending、event同時刻/uncertainty、multi-object/transaction、CASや他type、liveness/可用性、実transport/DB、crash/durability、長大history探索・性能。全Subject/Atlas完了、Core/fullGate、公開/commit/pushは主張しない。

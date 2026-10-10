# 有限検証

3modeの到達graphを最後まで探索し、独立所有/要求表・全source-target候補・集合閉包/層距離と全状態/全辺を照合。逆順最短deadlock trace2、同順の完了trace、retryの探索cycleと手書きprefix2+cycle6を別検査する。終端をdeadlockと誤判定しない。10contract拒否と6改変原票の拒否は正常graph照合と分離する。

初回rawにはUTC・command・input/source hash・環境・exitを保存。現在QA/receiptは別時刻でsource/artifactを束縛。通常checker/routeのhash/mtime不変は外側recorderで確認し、そのproofは循環hashを避けreceipt対象外。

Core/fullGate、Subject全体完成、TLC/実OS/fairness theoremは未実施。Skillは作者routing smokeで独立AgentEvalではない。

実観測: opposite13状態14辺/deadlock1/最短2、same-order12状態12辺/deadlock0、retry18状態26辺/deadlock0/最短cycle3。全mode safety違反0、各mode完了sink1。独立source-target候補713組。実IAB9状態と拒否3件、条件/経路の予想・結果・答えreset、拒否時対照保持、cycle一周追加を確認。実capture7回、ファイル未保存。専用tab15/session52986/port49337終了、残存listener0。利用60285は開始PID53504、終了確認PID64319でLISTEN（本taskから操作なし）、53478/PID3901も保持。default bind EPERM保全、一時承認実行でUI検証。Skill quick_validateと作者route正常/unsupported成功。初回receipt/pending QAを保持し、rawの初回command/UTC/sourcehashを変更せず現在QA/receiptを別日時で束縛。

post-UI seal時に入力メタデータtuple/listのJSON再照合が失敗。seal-failure-stderr.txtとiteration-failure.txtを保全し、未知modeテストの入力literalをJSON listへ修正した。producer探索・既存rawは変更せず再照合成功。独立edge集合には1/2辺cycleがなく、retry witness3辺が最短であることを照合。同順/逆順はpc和が各辺で1増える独立rankから非stuttering cycleなしを確認。

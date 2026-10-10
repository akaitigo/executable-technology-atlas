# OS・kernel engineeringを学ぶ入口 — pipe EOFは誰が決める？

有限1教材。Python標準libraryでtask-owned childを起動し、実OSのpipe・dup・close・read・SIGTERM・waitを観測する。kernel内部の改造・VM・host設定は行わない。[UI](index.html)は保存された実行原票を表示する。全Subject完成ではない。

**前提 → 主要概念・仕組み:** processは別PIDを持つ。FDはprocess内の番号で、open file descriptionへの参照。pipeにはread-end/write-endがあり、duplicate FDもwriterを保持する。bufferを読み尽くしただけではEOFにならない。全writerが閉じて初めてempty pipeのreadが0bytesを返す。childはread-endだけをpass_fdsで受け取り、親のwrite-endは継承しない。

**予想 → 操作 → 比較:** [UI](index.html)で「元のwrite FDを閉じ、dupだけ残すとreaderは終了する？」を予想し、caseを選んでeventを進める。FD図・parent/child別PID・timestamp/event表と独立期待lifecycleを比較する。正常close、empty EOF、最大512bytes、意図異常leak→close回復、leak→SIGTERM cleanup、拒否入力を扱う。原典/実装を辿ってから答えを開く。UIの操作は保存観測のreplayで、browserからprocessを新規起動しない。

| 契約case | checkpointのwriter参照 | bounded timeout期待 | EOF期待 | exit期待 |
|---|---|---|---|---|
| close | 0 | なし | あり（drain後） | 0 |
| leak-release | parent dup 1 | あり | dup close後あり | 0 |
| leak-signal | parent dup 1 | あり | なし | SIGTERM / Python -15 |

**今回の実装・正常異常:** [experiment](experiment.py)は実os.pipe→dup→Popen→ready handshake→write→close→bounded wait→回復/termination→cleanup。[child](child.py)が実readを記録する。[oracle](oracle.py)は実行codeをimportせず上の固定table・受信byte連結・所有child identity・因果順・FD/stream回収を確認する。readのchunk数は決め打ちしない。空payloadの0bytesは「0byte書込の効果」ではなく、writer全close後のEOF。SIGTERMは通常EOF完了に見せない。

入力は`{"mode":"leak-release","payload":"atlas\n","timeout_ms":200}`のみ。modeはclose/leak-release/leak-signal、payloadは0..512ASCII文字、timeout_msはinteger100..500（bool/float不可）、extra key/PID拒否。leak-signalは空payloadのみ。child ready最大3s、回復/終了wait最大3s。正常系が短いtimeoutに収まらなければ検証失敗を残し、cleanup fallbackを成功扱いしない。外部PID/process groupをsignalしない。

このdirectoryで:

```sh
python3 -B runner.py
python3 -B runner.py --input-json '{"mode":"leak-release","payload":"atlas\n","timeout_ms":200}'
python3 -B checker.py
python3 -B route.py pipe
python3 -B route.py kernel-patch # 未対応 exit2
python3 -B preview.py # 表示されたdynamic 127.0.0.1 URLを開き、終了はCtrl-C
```

runnerは一時pipe/childだけを操作し、原票を書かない。checkerは通常read-onlyで保存観測を検査。明示的な再観測依頼のときだけ`python3 -B observe.py --write-evidence`、artifact binding更新は`python3 -B checker.py --seal-evidence`。拒否はchildを起動せずexit2、実行失敗/検査失敗はexit1。[raw](evidence/raw.json)が実input・PID/FD・各process timestamp・child stdout/stderr。[run](evidence/run.json)が実行時刻/環境/input/source/raw digest。[FD図](evidence/fd-lifecycle.svg)は生成図でcaptureではない。[実IAB QA](evidence/ui-qa.json)にcapture保存・ownedserver終了を残す。

**実務判断 → 限界:** 終わらないreaderを調べる時、書込を止めた事実とFDを閉じた事実を分け、duplicate/継承されたwriterを数える。ready handshakeは起動との同期、waitはchild回収、signal終了はprotocol完了とは別。user-space実測からkernel実装・scheduler latency・throughput・全OS互換を断定しない。特にこのMacのPython3.9のmono値はprocess間で比較できず、[初回発見](evidence/clock-discovery.json)を保存。各process内elapsedのみmonoを使い、timeline表示はwall timestampによる参考順で因果証明には使わない。

**次に学ぶもの → 原典:** [全Subjectのcoverageと次の4実験](COVERAGE.md)でFD継承/IPC→同期/scheduler→VM→filesystem/driver/kernelへ進む。[一次資料索引](SOURCES.md)は公式規格、Python API、Apple/Linux guideと実装を結びつける。[専用skill](skills/atlas-operating-system-kernel-engineering/SKILL.md)は既存runner/checker/UIだけへrouteする。Portal/Core/Graph、OS/GitHub設定、依存追加、global install、commit/push/公開はこのunitの対象外。

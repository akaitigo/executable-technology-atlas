# HTTP requestが500になった後、接続は残る？

[第1単元](../../../subjects/backend-application-engineering/README.md)のservice/transaction実測から、既存N1のHTTP adapterとrequest resource ownershipへ進む有限追加単元。Mac stdlibの実wsgiref server、http.client、SQLiteを使う。同transaction outboxの再実証を新coverageとして数えず、CLI応答モデルから実HTTP transportへの増分を扱う。

読む順番は第1単元のservice境界→この単元のHTTP contract/trace→独立SQL→答えと実務判断。関連する[process context教材](../../observability-engineering/process-context-propagation/README.md)ではprocess間の親bindingを検査する。この単元のrequest内event履歴はその跨process接続の証明ではない。

前提はHTTP method/route/header/body、JSON、SQL transaction、try/finally。[事前契約](EXPECTATIONS.md)でPOST /orders、strict Content-Type、必須Content-Length、最大128byte、units integer1..3を固定。normal専用、refusal専用、fault→recovery共用の3 DB groupはそれぞれ空から始まる。setup接続、request接続、独立read-only observer接続は別の役割で、取得/close件数はrequest分だけ。

| 実HTTP条件 | status/body | orders/outbox | request取得/close |
|---|---|---|---|
| 正常JSON | 201、order_id1 amount200 | 1 / 1 | 1 / 1 |
| 不正JSON | 400、invalid JSON | 0 / 0 | 0 / 0 |
| 第二SQLに明示故障 | 500、storage failure | 0 / 0 | 1 / 1 |
| 故障後の次正常要求（同じDB） | 201、order_id1 amount200 | 1 / 1 | 新接続1 / 1 |

bool units、body宣言129、length欠損/不正、Content-Type/route/method不正も実HTTPで拒否。固定literal status/body/全SQL行を[手書き表](oracle.json)へ実行前に固定した。全11caseは正常HTTP2、入力/transport拒否8、意図SQL fault1。expected 500は正常業務成功へ数えない。unexpected server/client failureとも別。

[UI](index.html)で条件→予想→保存実測比較→HTTP/DB/所有resource→trace/source/raw→答えを辿る。条件または予想の変更で以前の比較・答えをresetする。入力拒否でも予想と実理由を読める。UIは保存実HTTPログの再生で、browserからDBを書き換えない。

[adapter](adapter.py)はenvironとwsgi.inputからbodyを読み、validation後だけsqlite3.connectを取得。BEGIN IMMEDIATE→orders INSERT→第二SQLを実行。faultは第二SQLだけをmissing_outbox INSERTへ置換し、実OperationalErrorを起こす。rollback→close→closed SELECTの実ProgrammingError→start_responseという順を記録する。準備に失敗したSQLはSQLite trace callbackに現れない場合があるので、fault eventのattempt SQLと実exceptionを別に保存する。wsgi.errorsへ固定合成errorを書きflushし、rawへdeltaを保存。appはserver所有input/errorsをcloseしない。

[runner](runner.py)は動的127.0.0.1 serverと標準HTTPclientで逐次送信。実status、response headers、正確なbody hex、WSGI environ、event seq、SQL trace、取得close tokenを記録。各requestの後にSQLite snapshotを保存し、[oracle](oracle.py)はadapter/runnerをimportせずread-only URIの直接SELECTで全行とintegrityを照合する。traceにROLLBACKがあるだけで0行を仮定しない。故障と次正常は同じlive DB、新しいconnection token1→2とclose probeで寿命を比較する。

```sh
python3 -B runner.py                   # current原票読むのみ
python3 -B checker.py                  # 保存raw + read-only SQL + artifact照合
python3 -B route.py http
python3 -B route.py framework          # unsupported exit2
python3 -B preview.py                  # 所有dynamic127.0.0.1 preview
python3 -B runner.py --record          # 明示unique run dir、新raw/snapshotsのみ
python3 -B checker.py --record-binding # 明示digest更新のみ
```

通常checker/routeは新要求を送らず原票を更新しない。recordの失敗もrawにtype/message/cleanupを保全し、成功時だけcurrent pointerを更新。live temp DBは所有serverをshutdown/join/socket closeした後で除去。証拠snapshotは保存対象として残す。最初のsandbox bind EPERM原票も保全する。条件変更・実行失敗を隠さない。

答え: 不正JSONはDB取得前に400。第二SQL500でもrollbackで両表0、connectionはresponse開始前にclose。次requestは別接続で201になる。入力streamとDB接続の所有者は異なり、全資源を一括closeする設計ではない。

実務判断: HTTP入力契約をtransportで確定し、service exceptionのHTTP変換責務とrequest connectionのclose責務を分ける。正常statusだけでcleanupを判断せず、故障位置・SQL残存・closeと次要求を照合する。

coverage増分は実HTTP contract、WSGI input/errors/start_response、request所有DB cleanup。次の3実験（未実施）:

1. framework DIのrequest scopeで同じfault/cleanupを比較。[PEP3333](https://peps.python.org/pep-3333/)
2. commit後・応答前停止と再送のidempotencyを実HTTPで比較。[HTTP client](https://docs.python.org/3.9/library/http.client.html)
3. 別process write競合/timeoutとjournal/WAL可視性を調べる。[SQLite transaction](https://www.sqlite.org/lang_transaction.html)

限界: 固定route/逐次request/stdlib/合成入力、独自status mapping・fault header。auth/TLS、実framework DI、concurrency負荷、chunked、宣言より短いbody、送信後failure、電源断、outbox実配信は未実証。Subject/Atlas全完成、Core/fullGate、commit/push/公開は主張しない。既存教材/Portal/2既存serversは触らない。

[原典](SOURCES.md) · [fixture](fixture.json) · [事前期待](EXPECTATIONS.md) · [current](evidence/current.json) · [binding](evidence/binding.json) · [実IAB QA](evidence/ui-qa.json) · [検証](evidence/verification.json) · [限定Skill](skills/atlas-wsgi-boundaries/SKILL.md)

# tool resultのfieldをtyped referenceで束縛する

[元のagentic systems教材](../../../subjects/agentic-systems/README.md)の次案typed-bindingを実固定executorで検証する継続単元。元教材では著者planのaddへ定数を渡した。今回はreadの戻り値 `r.value` を著者planのtyped referenceからaddへ渡し、dataと命令を分けたままfield・型・依存関係を検査する。既存入口・原票・coverageは変更しない。

実LLM、推論、自律agent、外部tool/API、認証、課金、eval、任意codeは実行しない。tool readは固定JSON fixtureのdeep copy、addはpureな整数和。どちらも外部writeや永続副作用を持たない。「呼出0」と「readだけ1」を同じ拒否結果へ丸めない。

## 契約を先に決める

planは著者が `fixtures.json` に固定した最大8nodeのDAG。toolはread/addのみ。referenceは `{"ref":"r","field":"value","type":"int"}`、literalは `{"literal":3}`。intはPythonの `type(value) is int`、-100..100で、bool trueを整数1として許さない。文字列"4"も自動変換しない。

全nodeのschema、tool名、reference先の存在、cycleを **全plan preflight** で確認してから最初のtoolをdispatchする。依存順はDFSで固定し、cycle/unknownはtool call 0。fieldの存在や値の実型はread resultを得ないと確認できないため **binding** で確認し、missing/string/boolはreadだけ1call、add dispatch前の拒否になる。readが済んだことを全tool未実行とは書かない。

tool resultの `proposed_plan` はdataとして保持するがstrict policyでは命令を選ぶために参照しない。著者planは実ユーザー承認やOS capabilityの証明ではない。

## 予想→操作→比較→原典/実装→答え

前提はJSON、整数/文字列/bool、field、reference、DAG、dispatch。画面でcall数を予想し、条件を選んで実行する。実executorを呼び、call/結果/拒否位置・traceを事前oracleと比較する。rawは記録再生ではなくその操作の実行結果。画面操作では保存原票を更新しない。

| 条件 | status / final | 実call | 拒否位置・判断 |
|---|---|---|---|
| normal: value=4、proposalあり | COMPLETED / 7 | read → add(4,3) | typed fieldだけを束縛。proposalはdataのまま |
| missing-field: other=4 | REJECTED / null | readのみ | binding / MISSING_FIELD |
| string-value: value="4" | REJECTED / null | readのみ | binding / TYPED_INT |
| bool-value: value=true | REJECTED / null | readのみ | binding / TYPED_INT |
| unknown-reference: ghost.value | REJECTED / null | 0 | preflight / UNKNOWN_REF |
| cycle: a→b→a、read rもplanにある | REJECTED / null | 0 | preflight / CYCLE。先にreadを呼ばない |
| bad-coercion（意図的誤り） | BAD_COMPLETED / 7 | read → add(4,3) | "4"をintへ無検証変換した型契約違反 |
| bad-promotion（意図的誤り） | BAD_COMPLETED / 103 | read → add(100,3) | tool dataの固定proposalを採用した出所境界違反 |

strictは正常1、期待拒否5。bad比較2をagentの成功件数へ足さない。7という最終数値だけでは正しいtyped dataflowか分からない。103もtool allowlistを通るが、計算の出所が変わっている。bad variantsはこの著者固定fixtureに限った比較で、任意の入力programを実行する機能ではない。

[OWASP AI Agent Security §5 Output Validation & Guardrails](https://cheatsheetseries.owasp.org/cheatsheets/AI_Agent_Security_Cheat_Sheet.html#5-output-validation-guardrails) からoutputの検査を学び、[Prompt Injection Prevention](https://cheatsheetseries.owasp.org/cheatsheets/LLM_Prompt_Injection_Prevention_Cheat_Sheet.html) からdata/instructionの境界へ戻る。このDAGと型規則は教材の契約で、OWASPがこの固定formatを規定したものではない。

答え：`executor.py` のpreflight→typed binding→dispatchを読み、`oracle.json` と `check.py` でcallと拒否位置まで照合する。値を取り出す型検査と、命令を採用する権限判断は別の条件。`results.r.proposed_plan` が残っていても、strictのadd引数は4,3のままである。

## 再現と原票

このdirectoryを作業位置にする。Python標準libraryのみ。

```sh
python3 -B check.py
python3 -B runner.py --inspect-evidence
python3 -B runner.py --case normal
python3 -B server.py
python3 -B runner.py --record
python3 -B skills/atlas-typed-tool-dataflow/route.py typed-reference
```

checker/inspect/routeは保存証拠をread-onlyで見る。`--case` は固定条件を実executorで実行してstdoutへ返す。previewは空きdynamic 127.0.0.1 portを起動時に表示、終了はCtrl-C。原票保存は明示 `--record` のみで新しいUTC directoryに保存し、旧rawを上書きしない。

採用原票は `observations/20261005T104512920684Z/raw.json`。各条件のUTC/runtime、入力plan/data、plan hash、実call、field binding、結果、拒否位置、全trace、executor/runner/fixture/oracle source hashを持つ。`check.py` はproducerをimportせず、手書き最終値・calls・拒否位置・段階列を照合し、5種の破損を拒否する。これはschemaの全入力探索や第三者AgentEvalではない。

通常sandboxでpreview bindはPermissionErrorになり、`observations/sandbox-preview-failure.txt` に保存。実行失敗を期待拒否の件数へ足さない。所属previewだけを既存ホストreviewで起動し、実IABの予想/操作/trace/答え/captureとcleanupを `observations/qa.json`、source/raw bindingとread-only検証を `observations/verification.json` に記録する。capture保存できなければその制約を明記する。

## 未教材と次の3実験案（未実行）

| 問い | 具体入力 | 比較観測 | 公式locator |
|---|---|---|---|
| 同じtoolでも引数変更の許可があるか | 著者plan hashと許可add(4,3) scopeを固定。tool dataでadd(100,3)へ差替え、期限切れscopeも投入 | 事前許可と実call hash、dispatch前拒否、call数。値の型が正しくても承認済みとはしない | [Agent Security / Tool Authorization Middleware](https://cheatsheetseries.owasp.org/cheatsheets/AI_Agent_Security_Cheat_Sheet.html#tool-authorization-middleware) |
| retryで副作用が重複しないか | 合成in-memory counterにoperation ID=op-1で1回加算。結果喪失を注入し同IDを再送、別IDも比較 | call回数と業務counter、checkpoint再開位置、同ID再生。外部writeは使わない | [W3C SCXML / Data Model](https://www.w3.org/TR/scxml/#datamodel)（状態設計の参考。idempotency仕様は次案で固定） |
| pause後のplan/referenceは有効か | read後pauseしapprove/cancel、旧plan hashへ失効入力、valueのsnapshot更新を比較 | 再開位置・binding元のversion・add未dispatch、停止後のcall数。実ユーザー承認を模倣したとはしない | [Agent Security / Human-in-the-Loop Controls](https://cheatsheetseries.owasp.org/cheatsheets/AI_Agent_Security_Cheat_Sheet.html#4-human-in-the-loop-controls) |

未網羅はmodel planner/plan repair、複雑schema/union/null/範囲外結果、任意planの入力防御、nested reference、memory/context poisoning、実capability、並行tool、timeouts/retry/cancel、durable state、multi-agent、実LLM injection試験・評価。有限typed bindingをLLM injection全防御やagent性能の成功と呼ばない。全Subject/Atlas完了、Core/fullGate、公開/commit/pushは主張しない。

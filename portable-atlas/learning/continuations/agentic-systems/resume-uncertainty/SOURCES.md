# Atlas｜再開判断の原典と前提



|前提資料|既に確認している範囲|今回との境界|
|---|---|---|
|[型付き参照](related.html?topic=typed) README:11/60–61・executor.py|事前の参照検査、実resultの型、dispatch位置|checkpointを再開判断へ使う処理は残課題|
|[call承認](related.html?topic=authorization) CONTRACT:17–20・model.py:110–131・COVERAGE:16|actor/plan/call/tool/args/期限/未使用の照合、消費→pure add|一続きの逐次処理。中断後の消費と効果を区別しない|
|[APIの再送](related.html?topic=api) README:5/31・runner.py:28–40|応答不明、業務rowとledgerの同一commit、同一key再送|今回この仕組みを再実装しない。承認消費の記録から効果を確定できるかを扱う|
|[serverless lease](related.html?topic=lease) README:16/34・runner.py:6–7|owner/generation/期限に合う完了UPDATE|旧workerのDB完了拒否は外部効果の停止・完了証明ではない|
|[crypto atomic admission](related.html?topic=atomic) COVERAGE:5–8・admission.py:37–44|check/rememberの一体化と受入数|認証済IDの受入と、別システムの効果完了は同じ記録ではない|

公式本文は2026-10-06に読取確認しました。[OWASP Tool Authorization Middleware](https://cheatsheetseries.owasp.org/cheatsheets/AI_Agent_Security_Cheat_Sheet.html#tool-authorization-middleware) は具体操作へ結び付いた承認と、実行直前の照合・消費を扱います。[High-Impact Action Integrity Controls](https://cheatsheetseries.owasp.org/cheatsheets/AI_Agent_Security_Cheat_Sheet.html#high-impact-action-integrity-controls) は冪等性や重複時の明示確認へつなぎます。これらが「消費済みなら効果も完了」と規定しているとは扱いません。

[RFC 9110 §9.2.2](https://www.rfc-editor.org/rfc/rfc9110.html#section-9.2.2) は非冪等要求を自動で再送できる条件を限定しています。今回の模型はHTTP実装ではなく、この境界を既存API教材へ戻るための前提として使います。checkpointの3状態、時刻9/10/11、HOLD_UNKNOWNという判断名は教材固有の契約です。

前提本文viewerは、元を編集せず固定pathとSHAを照合して読みます。sourceの存在確認と実ブラウザーで本文を読めた確認は別です。今回は前者のみです。

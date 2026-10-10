# 実行前の有限契約と予測

carrierはstdinの1 JSON object、独自field `context.trace_id` / `context.parent_span_id`。W3C traceparentでもOTel SDKでもない。固定IDはこのcase内識別用のみ。各caseは独立childで、新traceも教材固定dddd…、child spanはcccc…。

業務入力はobject、keyはunits/contextだけ、unitsはboolを除くinteger 1..3。context省略は許容し新trace+parentなし。指定contextはobject、許容keyはtrace_id/parent_span_idだけ、trace_id必須。IDはlowercase hex、trace32字/span16字、all-zero禁止。trace_idだけの故障版は診断比較のため意図的に許容し、親接続の欠落として扱う。null/空object/parentだけ/不正ID/余分keyは拒否。拒否では業務計算とchild spanを作らない。

| case | 業務結果 | child trace | child parent | 観測 |
|---|---|---|---|---|
| propagated | 200 | aaaa…（親と同じ） | bbbb…（親span） | connected |
| missing | 200 | dddd…（別） | null | orphan |
| trace-only | 200 | aaaa…（親と同じ） | null | orphan |
| upper-bound | 300 | dddd… | null | orphan |
| bool-units / missing-units / context-type / bad-id / parent-only / extra-key | 拒否exit2 | spanなし | spanなし | 対象なし |

完全IDと理由文字列を[手書きoracle](oracle.json)へ先に固定。正解は「業務成功200でもmissing/trace-onlyは親bindingを失う」。same traceだけを完全接続と誤認しない。

親のwrite開始/完了/receiveは親内順序。childのread/computeまたはreject/emit_readyはchild内順序。第1stdout行をflushした**後**のchildemit_completed ackを第2行へ出し、親はEOFまで読み実stdoutを保存する。stdin bytesとchild received、stdoutのline順とPID/PPIDでprotocolを照合する。異processのUTCをsortして因果を証明しない。UTCは記録用途、performance測定なし。

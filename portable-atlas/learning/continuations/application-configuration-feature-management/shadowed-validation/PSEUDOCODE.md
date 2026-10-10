# 固定手順

`emit`は全状態のdeepcopyを保存する。raw値そのものが不正でも、既知fieldだけをdiagnosticへ保存する。未知fieldのrawは参照/出力しない。input文字列のJSON解析はこの模型の前段であり、重複keyなどは今回の問いではない。

```text
state = attempts=[], candidate=null, config=null, provenance=null, error=null
emit START
structure_check(all layers, before either policy)
if error: emit STRUCTURE_REJECT; emit REFUSE; return refused
emit STRUCTURE_OK
if policy == all-layer:
  for layer in [default, env-input, task-json]:
    for known field in [timeout_ms, retries, flag_enabled, rollout_percent]:
      if layer has field: parse_and_validate(value, layer)
      append attempt(layer, source_field, field, raw, typed or null, reason)
      if rejected: set error; emit PARSE_REJECT; emit REFUSE; return refused
      emit PARSE_OK
  candidate = last parsed attempt for each field (layer/source_field/raw/typed)
  emit MERGE_TYPED
else:
  candidate = last raw binding for each field (layer/source_field/raw; no typed key)
  emit MERGE_RAW
  for field in fixed field order:
    parse_and_validate(candidate[field])
    append attempt; on reject emit PARSE_REJECT, REFUSE and return
    emit PARSE_OK
config/provenance = last typed attempt for each field
emit COMMIT; return accepted
```

PARSE_OK/REJECTのattemptは `layer,source_field,field,raw,typed,reason`。成功reason='ok'、失敗reasonは既存規約名（integer-string-required、strict-boolean-required、integer-required等）。errorはlayer/source_field/field/reasonだけ、構造不正のfieldはnull。イベントの注目metadataはPARSE/構造拒否だけ非null。他のSTART/STRUCTURE_OK/MERGE/COMMIT/REFUSEでは全てnull。

最終結果はcase_id, policy, decision（accepted/refused）, reason（resolvedまたはerror理由）, config, provenance, diagnostic={parse_attempts,candidate,error}, events。winning-only候補のraw文字列はtyped変換後も元のまま保存する。部分検査済み値はCOMMIT前にconfigへ出さない。

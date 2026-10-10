---
name: atlas-browser-engine-web-runtime
description: このBrowser event loop教材で同期log、Promise/追加microtask、timer内microtask、reaction例外/catchの順序を比較する。engine内部・worker・全Browser・timer精度の保証には使わない。
---

# Browser event loop教材

教材rootは二階層上。[README](../../README.md)の操作と学習案、[VERIFICATION](../../VERIFICATION.md)の実測、[scope](../../scope.json)の未教材範囲へ案内する。

- `node serve.mjs` のown動的loopback URLとtitleを確認。予想→basic/nested/caught-errorを新iframeで実行→期待順/誤モデル比較→原典/runner→回答という既存UIを使う。別loader/frameworkへ置換しない。
- 通常 `node check.mjs` は保存Browser原票のread-only検査。`--self-test`は合成oracle fixtureで、Runtime証拠ではない。明示的な新原票要求だけ `--record 未使用名`、旧成功/失敗は上書きしない。
- traceはこのcallbackのinstrumentation。新Documentは別thread/processやsandboxの証明ではない。delay0も精度/締切を保証しない。
- worker、全engine、paint/Network、process isolation、starvation/負荷等はscopeの未教材とREADMEの計画へ案内。この結果で保証せず、依存/OS設定/権限/公開/global installをSkill利用だけで始めない。

同一Agentの通常/対象外routing確認を独立Forward Evalと呼ばない。

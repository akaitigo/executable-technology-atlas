---
name: memory-growth
description: この固定72byte Wasm教材のpage増設、bounds trap、旧新view、JS/core grow失敗を実Browserと保存原票で比較する。
---

README→UI→hand-oracle→oracle→原典の順。通常verify/routeは保存Browser証拠を読むだけ。実行はUIのBrowserで実行を押す。grow後はviewを再取得。TypedArray添字undefinedとDataView TypeErrorを分離。RuntimeError trap、host拒否、注入基盤失敗も区別。各予想変更で開いた答えを空にし閉じる。明示record以外で原票を書かない。WASI、shared memory、性能、全engine互換を主張しない。

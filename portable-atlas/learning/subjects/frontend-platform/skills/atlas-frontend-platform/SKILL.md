---
name: atlas-frontend-platform
description: このnative ES modules教材で2importerのlive bindingとsnapshot、同URLの1回評価、read-only import、隔離された読込/構文失敗を試す。framework/build tool/循環依存/他runtimeの実装保証には使わない。
---

# native modules教材

二階層上が教材root。[README](../../README.md) の操作、[VERIFICATION](../../VERIFICATION.md) の実測、[scope.json](../../scope.json) の未教材範囲へ案内する。

- 起動は `node serve.mjs` のown dynamic loopback URL。予想→A/B更新→live/snapshot比較→同URL再import/代入拒否→別iframe失敗→原典→回答を試す。既存module/UIを使い、frameworkや別loaderへ置き換えない。
- 通常checker `node verify.mjs` はNode file loaderの検査。Browser保存原票は `node audit.mjs`。Node成功をBrowser HTTP/MIME/評価の実証と呼ばない。
- checkerはread-only。新規原票を求められたときだけ `--record 未使用名`。既存成功/失敗は上書きしない。
- 「1回評価」は同じDocument・同じresolved URLのこのfixtureに限定する。snapshotは初回評価時の数値コピー。read-only importはexport object内部のdeep freezeを意味しない。
- cycle、framework、build tool、worker/他realm/他runtime等は未教材。scopeを説明し、この教材の結果から保証しない。依存/権限/OS設定/global install/公開はSkill利用だけで開始しない。

通常/対象外の同一Agentルーティング確認は、独立Forward Evalとは別に記録する。

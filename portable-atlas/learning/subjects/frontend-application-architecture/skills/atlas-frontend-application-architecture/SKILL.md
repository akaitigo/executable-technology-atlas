---
name: atlas-frontend-application-architecture
description: このlist/detail教材で値copyの重複保存stateとID共有normalized state、選択/削除/unknownID/不正編集を比較する。framework/network/persistence/SSR/routing全般の保証には使わない。
---

# State ownership教材

rootは二階層上。[README](../../README.md)の操作/図/学習案、[VERIFICATION](../../VERIFICATION.md)の実測、[scope](../../scope.json)の未教材領域へ案内する。

- `node serve.mjs` のown動的loopback URL/titleを確認し、予想→同じ編集→copy不整合/normalized一致→選択/削除/拒否→図/model/原典→回答の既存UIへroute。別framework/loaderへ置き換えない。
- `node verify.mjs`はNode pure model、`node check.mjs`は保存Browser DOM原票のread-only検査。明示の新原票要求だけ `--record 未使用名`。成功/失敗を上書きしない。
- copy版のdetail-only保存は意図した不十分更新。draft/undoのcopy一般を否定しない。ID正規化だけでnetwork競合/全品質を保証せず、全stateのglobal化とも区別。
- framework、実network、persistence、SSR/routing、production権限等はscope/未実装学習案へ。保証や新実装/依存/OS設定/global install/公開をSkill利用だけで追加しない。

同一Agentの正常/対象外routingを独立Forward Evalとは呼ばない。

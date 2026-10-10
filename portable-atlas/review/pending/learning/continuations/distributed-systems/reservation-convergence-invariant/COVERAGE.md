# 検証範囲

| 問い | 対象 | 境界 |
|---|---|---|
| 収束と業務上限 | 即時受理/保留のtraceと独立集合oracle | 固定2 replica合成計算 |
| pendingの扱い | 初回pending→復旧後accepted/rejectedの履歴 | 実予約の確定通知ではない |
| 未配送/重複 | 空/片方向/順序逆/同一message再配送 | loss/retry/ackの実装ではない |
| 有限冪等性 | 26 positional、8 unique schedules | 任意実行証明ではない |
| UI | 編集、ケース、reset、旧結果、503、不正入力 | native静止画は特定時点 |
| 未教材 | transport,CRDT,CAP,consensus,取消補償,永続化 | 別model/原典/検証が必要 |

成功/失敗の実測はevidenceの原票とQAを参照。Subject全体、Atlas全体の完了は主張しない。

---
name: atlas-performance-capacity-engineering
description: このmoduleの有限FIFO workloadと観測窓のqueue面積を既存runner/checker/UIで比較する。実benchmarkや本番capacity算定には使わない。
---
module rootはこのfileから../../。README.mdでmodel tick、L/Lq、有限exposureと定常理論の違いを読む。
- `python3 -B runner.py --case censored`。fixture.jsonの9caseのみ。未完了j4,j5、完了積とLの不一致をoracle.pyと比較。
- `python3 -B checker.py`はread-only。明示的な原票更新依頼のときだけ`--record`。
- `python3 -B server.py`の一時127.0.0.1動的portで予想→操作→timeline/segment/intersection→原典→答え。自分のserver/tabを終了。
実production負荷、server sizing、forecast、外部data入力、他moduleは未対応。cohortRateはarrivalRateではなく、完了jobだけの平均を窓内Lへ混ぜない。

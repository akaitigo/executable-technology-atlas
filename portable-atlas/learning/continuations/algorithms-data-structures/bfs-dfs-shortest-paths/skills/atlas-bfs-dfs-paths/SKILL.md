---
name: atlas-bfs-dfs-paths
description: 有限無重み有向graphのBFS/DFSを既存学習fixtureで追い、queue/層/parentとstack/first pathを比較する。重み付き最短路や実速度の測定には使わない。
---

module rootのREADME.md、cases.json、search.mjs、oracle.mjsを読む。元lower bound教材はread-only。

- 正常routeはcounterexampleを選び予想→実行→次の一手→終点→答え。rawのBFS/DFSを独立単純path列挙oracleと照合する。DFS first pathを最短と呼ばないが、DFS自体を誤算法とも呼ばない。
- cycle-unreachable、equal-paths、self-loopで再訪停止/到達不能/同距離選択を分ける。重複辺は拒否し、黙ってdedupeしない。UI図は実JS状態traceの説明で実時間測定ではない。
- node verify.mjs / node check.mjsは通常read-only。明示--record observations/NEW-IDだけ新原票を追加、既存directoryを上書きしない。所有tab/serverだけ終了する。既存利用用serverや他moduleは触れない。
- 重み付き最短路/Dijkstraや実速度保証は未対応と説明し、scope.jsonのE1/E4と原典へ案内。依存追加/Cloud/課金/実機設定へ許可を拡張しない。
- Source/input/runtime/UTC/attemptを原票へ保存し、旧Evidenceを消さない。同一agentのrouting確認であり独立Forward Evalではない。全分野網羅/Subject完了は0のまま。

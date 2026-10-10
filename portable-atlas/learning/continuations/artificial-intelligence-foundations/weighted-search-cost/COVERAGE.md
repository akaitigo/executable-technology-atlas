# 有限coverage

既存 artificial-intelligence-foundations READMEのweighted未実験とcoverage.next_experiments.weightedの問い「異なるcostでもBFSはcost最小か」に対する小グラフ継続。重み付格子/Manhattan縮尺は未実装。

実施：≤5nodes、BFS/Dijkstra/A*、weightedと全辺1、零cost、同cost経路、到達不能cycle、負cost事前拒否、BFS mincost故障判断、独立simple path/手計算oracle、UIの予想/比較/失敗境界。

未実施：任意入力、負辺探索、負cycle、非整合h、汎用性能、ML、学習heuristic、格子の地形cost、CSP/MDP/実世界推論、Core/fullGate。次の未実施案はREADMEに3本。

# 重み付き探索：hopとcostの目的を分ける

[元Subject](../../../subjects/artificial-intelligence-foundations/README.md) READMEの未教材weighted実験、coverage.next_experimentsのweightedを小さな有向グラフで継続する有限1単位です。元案の地形格子・Manhattan縮尺・独立緩和はここでは実装せず、3〜5nodesの固定グラフと全simple path列挙を採用しました。元Subjectや全Atlasの完成ではありません。

前提は頂点/有向辺、経路、hop数、辺costの和、FIFO、priority。読む順番は[関連BFS/DFS教材](../../algorithms-data-structures/bfs-dfs-shortest-paths/README.md)で無重みのhop目的→元Subjectでunit-costとhの条件→本教材の重み付き例→独立列挙→cost/heuristic条件→実務判断。関連BFS/DFS教材は無重みの経路を扱い、本教材のcost最小化とscopeが異なります。UIは3つのcost予想→条件変更→実Python探索→hop/cost/条件比較→原典/コード/raw→答えの順です。

## 手計算を固定してから実行

全辺の向き・整数cost・入力辺順がfixtures.jsonの正本です。≤5nodes、平行辺なし、cost≥0、h≥0、goalのh=0、各辺でh(u)≤c(u,v)+h(v)。負costは探索前に拒否します。非整合/負heuristicの任意入力や巨大グラフを検証したとは主張しません。

| case | 手書きS→G経路とcost | BFS hop / cost | Dijkstra/A* cost | h(S),h(A),h(G) | 状態 |
|---|---|---|---|---|---|
| weighted | S→G:10、S→A→G:2 | 1 / 10 | 2 | 2,1,0 | 正常比較 |
| unit-cost | S→G:1、S→A→G:2 | 1 / 1 | 1 | 1,1,0 | 正常比較 |
| zero-cost | S→G:3、S→A→G:0 | 1 / 3 | 0 | 0,0,0 | 正常比較 |
| equal-paths | S→A→G:2、S→B→G:2 | 2 / 2 | 2 | 2,1,0（B=1） | 同cost2経路 |
| unreachable | なし。S→A→B→Aのcycle、X→Gは別component | none / none | none | 全0 | 期待到達不能 |
| bad-bfs-cost-claim | weightedと同じ | 1 / 10を最小と誤受入 | 2 | 2,1,0 | 故障判断 |
| negative-cost | A→G=-1 | 未実行 | 未実行 | 2,1,0 | 探索前契約拒否 |

hand-oracle.jsonの全経路・minhop/mincost・固定BFS pathはproducer採取前に手書きで固定。weightedの整合性はS→G:2≤10、S→A:2≤1+1、A→G:1≤1。unit-costではh(S)=2を流用すると直接辺の整合性/許容性を破るため1に変更しました。

BFSはenqueue時visitedのFIFO、入力辺順で1hopのS→Gを先に発見。Dijkstraはpriority=g、A*はpriority=g+h、最良g更新と古いentryの破棄。goalは取り出した時点で終了し、生成時に終了しません。同priorityは挿入順。weightedのpopはBFS S,G（g=0,10）、Dijkstra S,A,G（g=0,1,2）、A* S,A,G（f=2,2,2）。この例でA*がDijkstraより少なく探索したとは主張しません。

oracle.pyはproducerのneighbors/queue/heap/relaxationを呼ばず、edge listから再帰で全simple pathを列挙し、その辺costを足します。各頂点からgoalまでの列挙でhの許容性も独立確認。非負costの有限模型ではcycleを除いた最小経路を比較でき、zero-cost cycleがあっても全walkは列挙しません。今回のzero-cost fixture自体はcycleなしです。全simple pathは一般に高コストなので性能用oracleではありません。

## 再現と検査

このdirectoryで `python3 -B runner.py --case weighted`。fresh保存は明示的 `python3 -B runner.py --record` のみ。採用原票はobservations/20261005T133435011217Z/raw.json、record command exit0。UTC/Python/OS/machine、全入力、search/runner/fixture/事前表SHA、全pop/enqueue/relax traceを保存しました。

`python3 -B check.py` はproducerをimportせず全simple path/固定表、返却pathの辺cost/hop、Dijkstra/A*の最小cost、BFS最小hop、辺ごとのh整合性/許容性を確認します。6改変を拒否。通常checker/Skill routeは全ファイルSHA/mtime不変を検査し、原票を作成しません。

`python3 -B server.py` は127.0.0.1:0の専有preview。case変更は全予想unknown、各予想単独変更は新値を維持して比較/表/trace/raw/答えを消します。全run-startも同clear、generationで旧応答を破棄。INPUT_REJECTED、UNREACHABLE、EXECUTION_FAILUREを区別し、実行失敗はphase/errorとpath/hop/cost未確認で旧正常答えを表示しません。

observations/ui-qa/preview.pyは有限QA専用：2回目返却EXECUTION_FAILURE、4回目HTTP503、別modeで旧応答を保留/明示解放。synthetic注入を実環境の探索障害と混同しません。実IAB画面captureを表示してもローカル画像未保存ならその制限をQAに残し、画像を再構成しません。sandbox bind拒否はそのまま保存し同じserverをhost許可で実行。所有tab/portだけ終了します。

## 原典と実務判断

一次資料[Poole & Mackworth: Artificial Intelligence, Foundations of Computational Agents, 3e §3.6.1](https://artint.info/3e/html/ArtInt3e.Ch3.S6.html)を2026-10-05確認。g+hのpriority、許容heuristic、十分条件、同点順序による探索量の変化を読むlocatorです。著者の文章・図・コードは転載していません。本graph/コードは独自の有限例です。原典の一般条件と、今回の固定模型の観測を同一視しません。

実務ではhopを最小化したいのか費用/時間を最小化したいのか、辺cost/hの単位、負辺、goal終了条件、同点規則を先に確認します。既知グラフを探索しただけで、学習・汎化・学習heuristic・ML/LLM・外部APIを実証していません。負辺を許す最短路、負cycle、任意h、浮動小数cost、巨大グラフ/汎用性能も未検証。Core/fullGate、設定/依存install、公開、commit/pushは実施していません。

## 次の未実施案

1. 地形costを持つ有限格子で最小辺cost×Manhattanを検証する。現在は固定hの小グラフのみ。原典§3.6.3の簡略化問題へ接続。
2. 非整合hと再開を、全simple pathの最小costに照らす。現在は整合h契約のみ。元Subjectの再開教材との接続を深める。
3. 4変数彩色CSPで全割当/forward checkingを比較する。coverageのcspへ進み、経路探索から制約へ広げる。現在未実装。

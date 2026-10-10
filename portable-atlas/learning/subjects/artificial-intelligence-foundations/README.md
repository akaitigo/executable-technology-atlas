# AI基礎 — 状態空間を探索して計画を選ぶ

対象分野を学ぶための入口。現在は探索・計画基礎の有限1教材であり、Subject全体の完成ではない。実ML・LLM学習は未実装。Python標準ライブラリのみでMac上で実行する。

## 学習の道筋

1. **前提**：座標、集合、キュー、優先度キュー、グラフの辺、整数の大小を知る。状態は位置、行動は東南西北、遷移は決定的、各辺は1、目標は指定位置。このモデル化自体がAIの問題設定である。
2. **主要概念・仕組み**：BFSは距離順、A*は `f=g+h` 順。gは既知経路長、hは残りの推定。許容性は `h≤真の残距離`、整合性は全有向辺で `h(u)≤1+h(v)`。Manhattanは障害物を取り除いた緩和問題の距離であり、この4近傍単位costモデルで両条件を満たす。
3. **今回実装・正常異常**：[視覚入口](index.html)で予想→操作→比較を行う。[実装](search.py)と[独立checker](verify.py)を読み、原典へ戻る。
4. **実務判断**：単位costならBFSで十分な場合がある。良い下界と同点順序は探索量を変える。closedを永久固定するには整合性等の根拠が必要。到達不能と入力不正は別結果で扱う。
5. **限界→次の学び**：重み、部分観測、確率、行動前提、学習された推定器を追加するには保証を見直す。下の未教材coverageと次の4実験を使う。
6. **原典**：[source binding](sources.json)には節と実装との対応、[coverage](coverage.json)には主要概念・問い・公式locatorがある。

## 予想→操作→比較→原典/実装→答え

予想：8×2格子で、上側を避ける推定は短い道を見つけるか。許容的な推定ならclosedを永久固定できるか。5×5で同点順序を変えても探索量は同じか。

操作：module directoryで以下を実行する。UIは実行済み原票の状態列を再生する。スライダーは実時間やライブ探索ではない。

```sh
python3 verify.py
python3 serve.py --port 0
# 表示された127.0.0.1 URLをブラウザで開く。終了はCtrl-C。
```

比較：caseを選び、一段ずつ選択位置、closed、frontierのg/h/fと挿入順、経路、再開／抑止を見る。終点を取り出した時に停止し、goalもexpanded数に含める。古いheap項目は捨て、frontier表示から除く。挿入順による同点FIFO/LIFOを明示する。BFSはhを使わない。

|入力/方式|期待cost|説明|
|---|---:|---|
|corridor BFS / Manhattan A*|7|独立distance-layer oracleと一致|
|corridor 過大推定100|9|短い道のhが真値を超え、goalが早く取り出される|
|corridor 許容的・非整合、再開あり|7|closed (3,0) のg=5を3へ改善する|
|同じ推定、再開なし|9|短い経路への改善を抑止する意図的な誤り|
|5×5 同点FIFO / LIFO|8 / 8|costは同じでもexpanded・経路が異なる|
|遮断 / start=goal|到達不能 / 0|探索尽きと即時成功|
|範囲外、blocked start、bool寸法等|拒否|不正を到達不能へ変換しない|

原典/実装：[Poole & Mackworth §3.6](https://artint.info/3e/html/ArtInt3e.Ch3.S6.html)のf、許容性、緩和問題、同点順序と、[§3.7.2](https://artint.info/3e/html/ArtInt3e.Ch3.S7.html)の枝刈り条件を[search.py](search.py)のbest/closed/reopenへ対応させる。

答え：この格子の過大推定では9>7。許容性だけではclosed永久固定の根拠にならない。本例の非整合推定では再開で7に回復する。再開は過大推定を許容的へ変えず、最初のgoalで終了する保証も回復しない。同点順序は最適性の条件と探索量を別々に判断する必要がある。

## 未教材coverageと次の実験

[著者公式AIMA目次](https://aima.cs.berkeley.edu/)を分野の見取り図とし、[coverage.json](coverage.json)の問いと[原典一覧](sources.json)を対応させる。

|領域|ここから学ぶ概念・問い|状態|
|---|---|---|
|エージェント/問題設定|観測可能性・効用・合理性。現実の何を状態に含めるか|位置の状態空間のみ|
|探索/制約/ゲーム|重み、局所/記憶制限探索、CSP、minimax。制約や敵の選択をどう扱うか|BFS/A*以外未教材|
|知識表現/推論|命題/一階論理、含意、充足性。列挙せず何を証明できるか|未教材|
|計画|前提/効果、時間、資源。見つけた道を本当に実行できるか|位置routeのみ|
|不確実性/意思決定|Bayes推論、期待効用、MDP/POMDP。確率的遷移で何を最適化するか|未教材|
|機械学習|損失、最適化、汎化、NN、RL。既知グラフと経験からの学習の違い|実ML/LLM未実装|
|言語/知覚/ロボティクス|言語モデル、画像理解、状態推定、制御。入力から状態をどう作るか|未教材|
|評価/責任ある運用|分布変化、頑健性、公平性、安全、人の介入。何を測り復旧するか|未教材|

次の実験は4本（まだ実装されていない）：①地形costを導入しDijkstra/A*と独立緩和を比較（[§3.6](https://artint.info/3e/html/ArtInt3e.Ch3.S6.html)）、②4変数彩色CSPで全割当とforward checkingを比較（[著者教科書目次](https://artint.info/3e/html/ArtInt3e.html) Constraints）、③鍵/扉の前提を状態へ追加し位置のみの誤りを比較（[AIMA](https://aima.cs.berkeley.edu/) Automated Planning）、④滑る格子のMDPで最短routeと期待効用を比較（[著者教科書目次](https://artint.info/3e/html/ArtInt3e.html) Decisions）。この順で、cost→制約→表現→不確実性へ広げる。

## 再現証拠・検査

[原票](observations/raw.json)は入力、全探索trace、oracle cost、推定条件の違反辺、不正入力の実際の拒否を保存する。[receipt](observations/receipt.json)は実行時刻UTC、Python/OS/architecture、input/source/artifact SHA-256を持つ。hashは結びつける証拠であり正しさ自体の証明ではない。通常checkerはread-onlyで現在sourceとの一致、原票再実行一致、local links、roadmap/source binding、120個のseed固定ランダム格子を確認する。独立oracleは本体のneighbors/solveを呼ばず集合の距離層で計算する。

明示的な原票更新だけ `python3 verify.py --record` を使う。過去の観測を現在sourceの観測と偽らない。[UI実確認記録](observations/ui-qa.json)と[検証記録](VERIFICATION.md)を参照。[Skill](skills/atlas-artificial-intelligence-foundations/SKILL.md)は既存runner/checker/UIへ限定routeする。作者routing smokeは独立AgentEvalではない。

最大12×12、有限4近傍、全辺cost1、非負h、固定隣接順。対角移動、重み、巨大グラフ性能、実ML、LLM訓練、外部API、Dockerは今回未検証。全SubjectやAtlas全97入口の完成を主張しない。

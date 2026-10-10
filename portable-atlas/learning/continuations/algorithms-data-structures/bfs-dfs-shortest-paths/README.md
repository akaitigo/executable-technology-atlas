# BFSとDFS：最初の道は最短？

元の[lower bound教材](../../../subjects/algorithms-data-structures/README.md)と[学習経路・実験3](../../../subjects/algorithms-data-structures/LEARNING_PATH.md)を深掘りする有限unit。入力契約、不変条件、停止、結果の意味を分ける前提を引き継ぎます。元教材・原票・Portal/Core/Gateは変更しません。入口分野数の追加0、全分野網羅0、Subjectはincompleteです。

## 予想 → 実操作 → 比較

HTML/JS配列・向き付き辺・FIFO/stackが前提。既存Nodeのstdlibだけで起動します。

```sh
node serve.mjs
```

表示された動的127.0.0.1 URLを開き、予想を選びます。所有serverだけCtrl+Cで終了。既存利用用serverはそのままです。

1. 「DFS first path ≠ 最短」で新しい実行。次の一手を2回押し、BFS queueとDFS framesを比較する。
2. 終点まで見る。BFS S→B→T（2辺）、DFS first S→A→C→T（3辺）。「first pathを最短と扱う」誤判断であり、DFS自体の誤りではない。
3. cycle-unreachableはUへの経路なし。visitedでcycle A↔Cを再訪せず停止する。
4. equal-pathsは最短2経路。固定S隣接順[A,B]でBFS parent[T]=Aを選ぶ。唯一の最短とは言わない。
5. self-loop、起点＝終点、孤立終点を比較。重複辺・不正頂点・重み付き入力は拒否表示し、探索結果を返さない。
6. 図とqueue/stack/visited/parent/depth、原票、原典、実装を見て答え合わせする。

UIは[実JS探索](search.mjs)を操作時に実行し、記録済み状態列をステップ表示します。BFS/DFSは全reachableを探索し、最初のparentを上書きしません。目標到達時の早期停止版ではありません。図のstepやUTCはCPU速度の比較ではなく、操作履歴です。

## 契約と独立oracle

8頂点/32辺まで、uppercase ASCIIラベル1–3文字。有限・無重み・有向graph、隣接配列順固定。自己loopは受入れ、重複辺は拒否（黙ってdedupeしない）。未定義頂点/存在しない端点/重み付き要求は対象外です。入力の重複辺が拒否されても、同じ頂点へ異なる親から向かうdiamondは受入れます。

BFSはenqueueと同時にvisited/parent/depthを固定。未処理の同じ頂点を別親から重複投入しないこと、queueの距離層順序、first parentの最短性を分けて確認します。dequeue時まで印を遅らせる方式は同じ一回投入契約ではありません。

DFSは再帰と同じ隣接順のframes stackで深く進み、戻って次の辺を調べます。first discovery親は有効な経路ですが最小辺数の保証ではありません。今回visited skipをcycle分類やtopological sortingの完成とは呼びません。

[独立oracle](oracle.mjs)は探索実装をimportせず、pathごとの再訪を禁止した全単純path列挙から最小辺数と到達集合を計算します。自己loop/cycleでも最短経路は単純pathで十分な、この無重み有限契約を使います。全列挙oracleは実務の大graph用アルゴリズムではありません。固定反例のDFS経路は別の手で固定した期待値でも照合します。

```sh
node verify.mjs
node check.mjs
```

Nodeは9入力＋有効6入力の全端点105組を実JS実行、独立oracleとsnapshot不変条件を照合。通常は読取りのみ。明示`--record observations/NEW-ID`だけ新原票を書き、既存directoryを拒否。checkerの別原票は`--node observations/NEW-NODE/raw.json --browser observations/NEW-BROWSER/raw.json`。実Browserの表示・図・原票・Screenshotを照合し、生成図をcaptureと呼びません。

[検証記録](VERIFICATION.md)と[module-local Skill](skills/atlas-bfs-dfs-paths/SKILL.md)へ接続。Skillは同一agentの正常/未対応route確認であり、独立Forward Evalではありません。

## 原典と、次の未教材

- MIT [Lecture13 PDF pp.4–6](https://ocw.mit.edu/courses/6-006-introduction-to-algorithms-fall-2011/1208e162775f6f5cedfbb9f2b694ede0_MIT6_006F11_lec13.pdf#page=4)：層、初回parent、最小辺数。講義のfrontier版と今回FIFO queue版を同じコードとは扱わない。
- MIT [Lecture14 PDF pp.2–3](https://ocw.mit.edu/courses/6-006-introduction-to-algorithms-fall-2011/e59f8a55929028498953691891229a17_MIT6_006F11_lec14.pdf#page=2)：深く進み戻る探索、再訪の回避、到達成分/全graphの違い。

2026-10-05に公式PDF本文を上記locatorで確認。説明・code・graphは独自制作、既存repositoryのApache-2.0方針に従う。第三者code/図/本文を転載していません。

[scope.json](scope.json)に増分と未教材を保持します。

- E1：同じgraphの最小hopと最小costを比較。重み付き最短路/Dijkstra/負辺は未制作。[MIT Lecture16](https://ocw.mit.edu/courses/6-006-introduction-to-algorithms-fall-2011/resources/mit6_006f11_lec16/)
- E2：on-stack/finishedでcycleとcross edgeを分け、DAGのtopological orderを検証。未制作。[Lecture14 pp.3–6](https://ocw.mit.edu/courses/6-006-introduction-to-algorithms-fall-2011/e59f8a55929028498953691891229a17_MIT6_006F11_lec14.pdf#page=3)
- E3：複数成分のforestと多源BFS。根と距離層を別fixtureで比較。未制作。[Lecture14 p.2 outer loop](https://ocw.mit.edu/courses/6-006-introduction-to-algorithms-fall-2011/e59f8a55929028498953691891229a17_MIT6_006F11_lec14.pdf#page=2)
- E4：trace無/有、queue実装を分けてmemoryと実速度を測る。未制作。[MIT Python cost model](https://ocw.mit.edu/courses/6-006-introduction-to-algorithms-fall-2011/pages/readings/python-cost-model/)とJS実測モデルは別。

任意graph全証明、大入力benchmark、多Browser/AT、学習者理解度は未評価。Docker、Cloud、依存追加、OS設定変更、公開、Git操作は行いません。

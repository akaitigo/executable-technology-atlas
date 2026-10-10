# 検証記録

2026-10-05に有限unitを実行しました。全分野網羅0、入口加算0、Subject/全体Goalはincompleteです。独立単純path列挙は数学的モデルであり、実時間/実速度の測定ではありません。

## 現在Sourceの原票

- [Node attempt03](observations/node-attempt-03/raw.json)：Node v25.2.1 / V8 14.1.146.11-node.14、darwin arm64。9入力＋有効6入力の全端点105組＋不正入力5例を実JSで実行。**30,038 assertion**（6種類の負例拒否を含む）。保存済みUI結果の読取りではなくsearch.mjsの実行です。
- [Browser attempt02](observations/browser-attempt-02/raw.json)：実IAB Chrome/154.0.0.0、ja、1280×720、DPR2。全9入力＋Skill正常経路の別run、**10 run / 15 checkpoint / 15 full-page実Screenshot**。新しい実行、次の一手、終点まで見るを実UIで操作。UTC、attempt1/retries0、12 Source digest、input digest、full trace、DOM/AX、表示状態を保存。
- [read-only照合](observations/check-attempt-01/raw.json)：**38,298 positive assertion / 10 negative fixture拒否 / 297,048 negative traversal check**。これは原票の照合件数であり、Browserをその回数実行した意味ではありません。保存したBrowser結果はNode結果と独立列挙oracle、図の頂点/有向辺/parent/frontier/visited、実JPEG hashに結び付けています。
- Skill正常は`skill-counterexample`の別実行で予想→一手→終点を操作。未対応は重み付き最短路と実速度保証をE1/E4へ案内、測定済みとしない。quick_validate exit0 / `Skill is valid!`。同一agentであり独立Forward Evalではありません。

## 正常・拒否・解釈の比較

| 入力 | BFS / DFS first / 独立最小辺数 | 判断 |
|---|---|---|
| counterexample | 2 / 3 / 2 | S→B→TとS→A→C→T。DFS firstを最短と呼ぶ誤判断を検出 |
| cycle-unreachable | 到達不能 / 到達不能 / 到達不能 | A↔Cでも停止。Uは訪問されない |
| equal-paths | 2 / 2 / 2 | oracle最短経路2本。固定隣接順でAを親として選ぶ |
| self-loop | 2 / 2 / 2 | S→SとA→Aをskip、頂点を重複投入しない |
| start-goal | 0 / 0 / 0 | path[S]、頂点数1でも辺数0 |
| isolated-target | 到達不能 / 到達不能 / 到達不能 | 空の隣接列で停止 |
| duplicate-edge | 拒否duplicate-edge | 黙ってdedupeしない |
| unknown-vertex | 拒否unknown-vertex | 未定義Xを探索しない |
| weighted-input | 拒否unweighted-only | 重みを捨てて成功扱いしない |

BFSのenqueue-markはparent/depth/visitedを同時に固定。visitedが一度だけ増え、queueの層順序が保たれ、各reachable辺が一度だけ調べられることを全snapshotで検査。DFSはframesの親鎖とcursor範囲を検査し、depthはparent木の深さで、最短距離とは区別します。固定反例のDFS経路は手で固定した期待列も使用。

![実IABのBFS/DFS探索図（Skill正常経路）](observations/browser-attempt-02/skill-counterexample-diagram.jpg)

上は実viewport Screenshot。追加のviewport2枚は原票15枚とは別で、再描画/生成画像ではありません。最初のviewportはinput欄内をスクロールしてしまい図が写らず保持。背景余白でページ本体をスクロールした次のcaptureを図の表示確認として採用しました。whole-pageの前提/入力/結果/答えは[counterexample full-page](observations/browser-attempt-02/counterexample-3.jpg)で確認できます。

## 失敗・修正・旧原票の保持

- [record失敗](observations/node-record-failure/raw.json)：初回はobservations parentが存在せずmkdir ENOENT。保存成功とせず失敗を記録し、Nodeを実再実行。
- [locator失敗と修正](observations/source-url-correction/raw.json)：Python cost modelのURL取得が失敗。公式講義一覧のnavigationから正しいreadings下へ解決。Scope Sourceが変わったので[Node01](observations/node-attempt-01/raw.json)を保持し[Node02](observations/node-attempt-02/raw.json)を実再実行。
- [Browser01](observations/browser-attempt-01/raw.json)：counterexample4地点の実captureで、S→Bの辺が無関係なAを横切り、逆向き辺が重なることを人手の画像確認で発見。partial原票として保持。円周配置・逆向きcurve・DOM edge/vertex bindingへ修正。期待path、入力、探索algorithmは変更しない。Source変更後Node03と全Browser02を実再実行し、digestだけの更新にはしない。
- [通常権限preview失敗](observations/preview-default-denied/raw.json)：listen EPERM/exit1を保持。127.0.0.1同一commandのhost review後に一時表示。外部公開・恒久的権限変更なし。

## 再確認とcleanup

```sh
node verify.mjs
node check.mjs
```

default原票はNode03/Browser02。通常checkerはread-only。新規保存は明示`--record observations/NEW-ID`、既存directoryはEEXIST拒否。過去原票のSourceが現在と違う場合は正しく拒否し、再封印しません。

作成tab18を閉じ、所有server session86406/87417をSIGINTで終了（各exit130）。所有port55498/57270のLISTEN確認はexit1/空出力。既存利用用PID3901/port53478は引き続きLISTENを確認し、停止/変更していません。Docker/Cloud/依存追加/OS設定/公開/commit/pushなし。旧Goal/Core/Gateの再試行はこの単元の委任範囲外です。

最終hash/mtimeのinventory、通常検査と既存directory拒否の無変更確認、元lower bound17ファイルの不変確認は `observations/read-only-audit/raw.json` に記録します。監査自身は循環hashを避けてinventoryから除外。局所的なcredential/path marker scanは包括的な秘密情報監査の保証ではありません。

## 未測定・次の実験

全列挙oracle/trace複製/SVGの費用を含む教材全体をO(V+E)や実速度比較として売りません。weighted/Dijkstra/負辺、cycle分類/topological sort、全graph forest/多源、実時間/memory・任意graph証明、多Browser/AT、理解度は未教材。[E1–E4の問い・具体実験・primary locator](scope.json)を維持します。MIT Lecture13 pp.4–6、Lecture14 pp.2–3本文を確認し、将来E1は公式resourceの入口のみ確認しました。第三者PDF本文/図/codeは複製していません。

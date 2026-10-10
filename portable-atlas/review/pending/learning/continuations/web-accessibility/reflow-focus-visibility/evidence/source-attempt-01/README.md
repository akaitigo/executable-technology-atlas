# Reflowとfocus表示の有限実験

固定幅の故障フォームと流動layoutを、1000/320 CSS px幅で比べる。同じ5controlへTabで到達しても、枠が抑制されたり送信が覆われたりする。[学習経路の実験4](../../../subjects/web-accessibility/LEARNING_PATH.md)と[modal scope E3](../modal-focus-lifecycle/scope.json)の一部を独立fixtureで進める。

このディレクトリで `python3 -B server.py` を起動し、表示URLの `/index.html` を開く。予想→条件選択→Tab開始点クリック→Tab5回→DOM原票→保存観測との比較→source/原票→答え。条件選択だけではviewportを変更しない。保存比較は採取時の実測であり、現在の端末の新しいAX実測ではない。

`python3 -B checker.py` は保存証拠を読み取り監査、`python3 -B test_negative.py` は誤った証拠の検出、`python3 -B route.py reflow` は読む入口。新採取は[REPRODUCE.md](REPRODUCE.md)。正常な流動版と故障版を比べ、幅とfocus可視性を別に判断する。故障をWCAG全体の判定へ拡張しない。

読む順は[事前期待表](EXPECTATIONS.md)→[原典](SOURCES.md)→[実装](ui.js)→[原票](evidence/observations.json)→[QE品質特性](../../../quality-engineering-atlas/README.md)。操作できても意味や操作位置が伝わるとは限らないという観点へ接続する。既存QE/global文書は変更しない。

DOM寸法、computed style、rect重なり、中心hit-test、trusted keyboard/focus eventと、native AX/captureを分ける。AXに送信があることは画面で見えることを保証しない。outline0だけで全indicator不在を断定しない。viewport外のcontrolをデータ削除と呼ばない。

実zoomは公開APIに手段がなく未測定。viewport overrideを使い終了時resetする。実AT、contrast、forced colors、touch、media、全遮蔽ケース、全WCAG適合は未評価。OS/アプリ設定や新権限は変更しない。Core/fullGate、公開/install/commit/push、Subject/Atlas完成、受入数の加算は対象外。

# 名前と説明の参照行列

見える文字から名前を推測せず、12個の小さなnative button fixtureで参照規則を比較する。[既存の学習経路・実験1](../../../subjects/web-accessibility/LEARNING_PATH.md)の独立した続き。[QE品質特性](../../../quality-engineering-atlas/README.md)へは、操作できても意味が伝わるとは限らないという問いで接続する。既存文書の受入・状態は変更しない。

## 使う

このディレクトリで `python3 -B server.py` を実行し、表示された動的loopback URLの `/index.html` を開く。名前と説明を予想→条件選択→白い領域の対象ボタンを操作→「保存観測と比較」→原典・実装・原票→「答えと実務判断」。正常な名前と、クリックできる名前空の故障条件を比較する。説明は期待表と未観測表示を読む。

`python3 -B checker.py` は保存原票のread-only監査、`python3 -B test_negative.py` は誤った証拠が拒否されるかを監査する。`python3 -B route.py names` で入口を取得。新しいAX採取はREPRODUCE.mdのIAB手順を用いる。保存観測を取得した端末と、後からUIを開いた端末を同一視しない。

## 証拠と制限

期待表はAccName 1.2 2026-10-02 Working Draft §4.2/§4.3.2読解。fixture/oracle/期待表はproducer前に固定。Mac IABでnative AX snapshotと完全一致role/name queryを実行した名前観測、実click、DOM原票を分けて保存する。description getterはこの経路で公開されず全12条件UNOBSERVED。descriptionを空文字、照合pass、AT発話へ置き換えない。Browser版はAPIから未取得、Mac/IAB経路の観測であり版を固定した再現試験ではない。

実AT音声、全WCAG適合、name/description全規則、Browser間互換、focus/キーボード/タッチ/zoom/通知は対象外。Core/fullGate、公開/install/commit/pushは実行しない。Subject/Atlasの完成やaccepted数は主張しない。予想と取得失敗も原票に残す。

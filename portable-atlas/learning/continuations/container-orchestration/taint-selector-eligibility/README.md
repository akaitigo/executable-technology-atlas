# Atlas｜空きがあるのに、なぜ配置できない？

[元のslot配置](related.html?topic=slots)→[CPU・memoryの配置](related.html?topic=resources)→[今回の画面](index.html)の順に読みます。[目標47](related.html?topic=goal)の、容量があっても配置できない理由を扱います。

同じpodが収まる空き容量を持っていても、配置先のlabel条件やtaintの許容条件を満たすとは限りません。今回の問いは「容量を増やす前に、何が配置を妨げているか分かるか」です。tolerationはnodeの制限を許容する条件で、特定nodeへ誘導する指定ではありません。

1. 条件と予想を選び、保存した計算結果を読む。
2. 各nodeのCPU・memory・label・taintの判定を比べる。
3. 「全条件を満たす集合」と「教材のA→B順で選んだ1node」を分ける。
4. taintを無視する故障版を対照にし、選ばれたnodeが本当に条件内か確かめる。
5. [原典と既存実装](SOURCES.md)、[固定契約](CONTRACT.md)、[手期待](expected.json)へ戻り、答えと限界を読む。

2node・1pod・6条件の有限模型です。Kubernetes・Docker・実podは動かしません。A→Bの選択は教材固有で、実schedulerのscoreではありません。画面に出るBOUNDは模型の選択結果で、実podのRunning・Readyや通信成功を表しません。

2026-10-07 00:15:01 UTC に有限模型を初回実行しました。6条件×2方式と4入力拒否を保存し、作者検査252関係・9改変拒否が通過しています。保存結果readerの実画面も確認しました。独立最終判定と保存した根拠は確認状態から辿れます。[確認状態](qa/reader-acceptance.json)、[再現手順](REPRODUCE.md)、[Skill](SKILL.md)、[残る不足](COVERAGE.md)から実施範囲を確認してください。

画面は、このディレクトリで `python3 serve.py --port 18783` を実行し、`http://127.0.0.1:18783/` を開きます。使用中のポートなら別番号を指定し、既存サービスを止めません。1280×900と390×844の実画面で、固定6条件と4拒否、予想変更・reset・取得失敗後の古い表示消去を確認しています。

[保存した計算結果](observations/run-01/results.json)と[実行ログ](verification/execution.json)を分けて読むと、模型の判定と実行条件を確認できます。正常版は3条件がBOUND、3条件がPENDING。故障版は5条件でBOUNDを返しますが、2条件は配置可能な集合の外です。入力拒否4例はpayloadなしで、PENDINGとは別です。

既存ブラウザーの1ページで確認した操作は保存値の選択・比較です。元slotとCPU・memoryの本文、目標47、Skillへ実リンクから移動できました。公式原典へのクリックは外部通信を遮断したテスト応答までで、GUIで公式本文を取得したとは扱いません。狭い画面の図と表は横スクロールで読み、全列が同時に見えるとは主張しません。

# 性能・容量工学：この単元の範囲と次の課題

既存の `learning/continuations/performance-capacity-engineering/two-server-bounded-queue/COVERAGE.md` 第1行「job cost が異なるとどうなるか」から、順序に関する最小の有限実験を切り出しました。既存repo・元のcoverage・統合manifestは変更していません。

|問い|今回の状態と根拠|次に必要なこと|
|---|---|---|
|仕事の長さが違うとFIFOと短い順はどう変わるか|単一サーバー、到着0、A5/B1/C1の6順序をPython/JavaScriptで照合。実ブラウザではABC/BCAとリセット・時刻進行・幅1280px/390pxの6件成功、実画像の目視確認済み。|既存の検索・閲覧・実行案内への統合を判断する。統合は未完了。|
|平均が改善すると全員が改善するか|反例を確認。平均6→10/3、A5→7。|期限や仕事ごとの重みを別の固定入力で比較する。|
|最後の完了時刻と処理量は変わるか|6順序とも終了7、3件完了。|実測の負荷・資源制約とは切り分けて扱う。|
|元の2サーバー・待ち行列上限でも同じか|未実施。今回は単一サーバーへ限定した。|既存の有限2サーバー教材で、長さと選択順序だけを変える。|
|処理時間を事前に知れないとどうなるか|未実施。実行前に正確な長さが分かる仮定。|固定された予測値と実際値が逆転する入力を用意する。|
|到着が続くと長い仕事が待ち続けるか|未実施。3件の全完了から一般的なstarvationは主張しない。|有限の観測窓、未完了仕事、連続到着の仮定を明示した別実験。|
|retry/deadlineでattemptと要求はどう変わるか|既存coverageの第2行。今回未対応。|有限retry/deadlineを作り、attemptとlogical requestを分ける。|
|producer待ちを実測から失っていないか|既存coverageの第3行。今回未対応。|専用のローカルbenchmarkでoffered/accepted時刻と未完了を保存する。今日の重い計算には追加しない。|

学習経路は、要求（平均と個人の両方を見る）→仕組み（単一サーバーの累積処理）→実験（6順序）→判断（平均とAの遅延を比較）→限界（有限モデルと実運用を分ける）です。[ブラウザ操作記録](../browser-qa/run-2026-10-06T022404940Z/report.json)の11件中6件、保存画像8枚中4枚が本教材です。[実画像の目視確認](../browser-qa/visual-review.json)も完了しています。分野全体の網羅、Portal統合、受入加算は未完了です。実サーバーのベンチマークは行っていません。

原典： [Google SRE: Handling Overload](https://sre.google/sre-book/handling-overload/)、[Cascading Failures](https://sre.google/sre-book/addressing-cascading-failures/)、[Monitoring Distributed Systems](https://sre.google/sre-book/monitoring-distributed-systems/)。後者2件は既存coverageの次課題locatorを引き継いだもので、今回の実験根拠や再検証済み資料として数えていません。

再受入では既存readerの旧答え文字列消去を修正し、6順序・32時点の実DOM、1280/390px、実画像6枚を確認しました。数式と手計算は不変。順序変更のselectOption9回は実pointer54回/keyboard33操作群とは別です。[追加QA](GUI-QA.md)・[元教材との差](ACCEPTANCE-NOTES.md)を参照。独立受入は引継ぎ中、統合は別工程です。

# Atlas — 固定計算と保存結果の読み方

対象は [cases.json](cases.json) の5列×4分位点です。実装前の [expected.json](expected.json) と別担当の独立表を先に固定します。合成入力の有限計算で、実collectorやネットワーク実験はありません。

予定する実行コマンドは `python3 -B run.py --output observations/run-01` です。外側の実行器が資源余力・単独枠を確認し、nice>=10、1子、約5秒の期限、終了後の回収を記録します。CLI自身も実優先度を確認し、未達なら模型の import より前に停止します。既存出力は上書きしません。自動再試行はありません。

対象は2026-10-07に1回実行済みです。[結果](observations/run-01/results.json)、[実行時実装](observations/run-01/inputs/histogram.py)、[保存検査](observations/run-01/saved-result-check.json) を結びました。PID60903、実nice10、exit0、子回収済み。外側の実行器が記録した全工程は約0.085秒、結果内のelapsedSeconds約0.00104秒は保存/検査前の計算部分です。両者を同じ所要時間としません。検査の数は作者・独立担当で合算しません。

画面は `python3 -B serve.py --port 0` の表示ポートを開きます。既存資料の本文は固定allowlistとSHA照合で表示します。JSONや実装ファイルは保存版を読み、結果の欠落・改変・取得失敗を成功表示に置き換えません。

実画面確認は用意済みの1ページを再利用し、約5.779秒で完了しました。環境側の実行器が教材用loopbackサーバー1個（PID64749、127.0.0.1:50389）を起動し、確認後に正常終了（exit0）を記録しています。検査module自身のbrowser/context/page/server起動は0です。自身のroute/listenerを外しviewportを戻してpageを返却しました。共用ブラウザー全体の終了と、今回のサーバー終了は区別しています。

原典2リンクは実pointerでURLへの遷移を確認しましたが、外部通信を遮断したテスト応答を表示しただけです。公式本文をGUIで取得した確認ではありません。5前提の本文と6文書は実リンクから読み、保存内容へ照合しました。9実画像を保存し、作者は重要な5枚を1枚ずつ目視しました。画像の取得と目視した範囲、独立担当の目視は [確認状態と記録への参照](qa/reader-acceptance.json) と最終受入へ分けて残します。

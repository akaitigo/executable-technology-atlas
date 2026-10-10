# Atlas：保存資料を読む手順と再現の条件

[README](README.md)のコマンドでloopbackの資料viewerを開く。[index](index.html)で条件と予想を選び、表示・比較・原典/実装・答えの順に読む。予想や条件の変更、resetでは古い結果・比較・答え・表示済み実装を消す。読込失敗では入力と選択肢も消す。回復後は予想してから再表示する。

今回の計算は実HTTP通信ではなく、固定status・media・本文bytesを渡したconsumer関数。[保存結果](observations/run-01/results.json)は対象子1回、actual nice=10、wall約0.103秒、retry0で得た。[実行ログ](verification/execution.json)と[保存検査](verification/saved-result-check.json)を分けて読む。作者手表と独立手表を先に固定し、資源観測から約1.947秒で今回の実行条件を照合した。子と専用process groupの終了も確認した。実行前のsandbox読取拒否、期限外となった観測、補助scriptの文字コード読込失敗は履歴に残し、対象consumerの再実行に数えない。

GUIは2026-10-07 01:09:50–01:09:54 UTCに、既存の1ブラウザー/1ページを再利用して確認した。検査環境が教材用loopbackサーバー1個を起動し、確認時は `http://127.0.0.1:51237/` で配信した。継続利用のためブラウザーとサーバーを維持した。検査module自身のbrowser/context/page/server起動・終了は0で、自分のrouteとlistenerを解除し、viewportを復旧して同じページを返した。READMEの18784は起動例で、今回使ったportとは別である。

全12応答の可視値、開いた詳細、条件・予想・resetによる消去、取得失敗・欠落・内容改変・遅れた旧応答の5対照を保存した。操作は実pointer99件・実wheel6件と、選択API32件・同じページへの移動API17件を分けた。前提7資料と文書6件は実リンク操作と本文表示を確認した。公式原典2リンクは正確なURLへの要求をローカルの遮断案内へ置き換え、外部へ転送せず、GUIで公式本文を取得したとはしない。

1280×900と390×844の実viewport画像10枚を確認した。狭幅では図・member表・比較表を左右端へ動かしてから左端へ戻した。反対側の列は画面外になるため、全列を同時に表示した確認ではない。図は保存した計算結果の説明で、通信を撮影したものではない。遅れた応答の確認はAbortを含む実際の読込経路であり、世代番号の判定だけを単独で強制した試験ではない。文書の更新前後と画面確認の記録は[確認状態](qa/reader-acceptance.json)から辿れる。

6応答×2方針、member/type/判断の全値と入力前後を保存した。実行時の[consumer](observations/run-01/inputs/consumer.py)と17入力のsnapshotは保存結果内のSHAに対応する。入力schemaの拒否は今回0例で、保存値の8改変とは別。全schema境界、任意URI/媒体文法、認証、一般HTTP相互運用、実proxy、業務副作用、再送は対象外。

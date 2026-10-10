# Atlas｜所有bytesだけで再現する

既存MacのPython標準ライブラリを使用します。hostへのextract、container、registry、Docker、SDK/install、OS設定変更は行いません。

- [CONTRACT](CONTRACT.md)、[fixture](fixture.json)、[11条件](cases.json)、[手期待](expected.json)を先に読む。
- 保存した実行は2026-10-06 18:17:41 UTC、load3.145/12CPU・idle82.4%・memory query49%・既知の計算処理の競合なしを確認して開始した。execute_once.pyは実nice10を読戻してから、run/verifyを各15秒・子1個ずつで実行し、両子はexit0で回収した。新たな再実行では直前の負荷・メモリ・競合の確認が必要。既存runへの上書きは拒否するため、保存済み教材は読み直すだけでよい。
- 保存結果だけを照合する手順は `python3 -B verify.py`。producerをimportせず、保存したbyte列と手期待を確認する。
- 2026-10-06 19:01 UTCに既存の公式Playwright/Chromium headless・sandbox有効の共有1ページでGUIを確認した。11条件・83回の実ポインター操作、取得失敗/旧応答と3画像を保存。今後の起動には、`python3 -B serve.py --port 18764` で専用loopbackを使い、表示されたportの `http://127.0.0.1:18764/` を開く。競合したら既存serviceを停止せず、`--port 0` で空きportを選ぶ。自分の経路設定とviewportは確認後に元へ戻す。共有browser/serverを他担当から終了せず、所有する実行担当が回収する。
- 操作順は条件と予想→保存結果を表示→正常2blobと選択条件を対照→計算時の実装→答え。予想・条件・reset・再読込時は古い結果と答えを消す実装で、欠落/改変時も停止する。古い成功/失敗の応答を無視する通常経路も実DOMで確認した。これはAbortを含む試験であり、世代番号だけの強制検査とは呼ばない。

gzipやtarのbinary保存は自分の教材ディレクトリだけ。tar memberをホストのfileへ展開する操作とは異なります。元の3資料は固定したpathと内容hashを使って読むだけで変更しません。実計算、保存照合、静的reader、実画面の確認を混同しません。実行結果は[計算結果](observations/run-01/results.json)、[照合](verification/saved-result-check.json)、[実行ログ](verification/execution.json)へ。

Atlasの関連3資料はhref取得後に同じページへ移動し、固定本文へ照合しました。実リンククリックは未確認です。計算再実行は不要で、状態文だけの追補確認は初回の全条件確認と分けます。

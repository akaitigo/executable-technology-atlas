# Atlas：保存記録と実通信の再現を分ける

[README](README.md)の起動方法は資料viewer用である。画面の再読で実験のHTTP要求を送り直さない。画面は初回4応答の[保存結果](observations/run-01/results.json)を内容hash付きで読む。手期待は実装前に固定した予測として残す。

対象実験は標準ライブラリのHTTPServerを自己所有の127.0.0.1:0へ一時的に起動し、4GETを逐次実行した。各HTTPResponse.read(8193)は1回のみ、追加readや無制限readは使わない。socket timeout2秒は停止のための境界で、遅延やtimeoutを実測する条件は含めない。

既存作業と競合しない単独枠、最新資源・プロセスidentityの確認、今回だけの実行判断が必要。execute_once.pyは実nice>=10を確認してから1子を開始し、wall15秒を超えた場合は自分の子だけを終了・回収する。run.pyも優先度確認前に実験をimportしない。古いallowed値や既存の実行記録は再利用・上書きしない。今回の初回実行はnice10・exit0・0.1872秒、timeoutなし、子の回収済み。保存検査は418関係と10改変拒否を通過し、追加通信はしていない。

実行時に4応答のstatus/header/body、Content-Length、read例外、HTTPResponse.length/isclosed、検査段階、返却JSON、所有資源の終了を保存した。実Python版とhttp.client/http.serverの実import元SHAも記録する。実装前の予測と一致しなくても記録を消さず、版と呼出し条件を調べる。保存検査はサーバーをimport・再起動しない。

GUI確認は管理側が用意した同じheadlessページ1個を再利用した。検査module自身はbrowser/context/page/serverを作成・終了せず、専用のroute/listenerを解除しviewportを復旧する。管理側は資料サーバーを127.0.0.1:61237に1個起動し、検査後にPID 41541のexit0・回収を保存記録で確認した。検査module自身の起動は0で、管理側の起動と区別する。検査moduleはページを残し、全教材の検査後に管理側が共有context/browserも終了した。実ポインターと選択API、説明図と実画面、外部原典の遮断テスト応答と公式本文の読取を区別する。

[契約](CONTRACT.md)の4条件だけを扱い、[未対象](COVERAGE.md)まで成功扱いしない。現在の実施範囲は[確認状態](qa/reader-acceptance.json)へ。

[実行記録](verification/execution.json)、[保存検査](verification/saved-result-check.json)、[実行時の判定実装](observations/run-01/inputs/boundary.py)を辿れる。実通信4GETと保存readerのGUI確認は完了した。GUIは4.320秒、4応答・10切替・5取得失敗/旧応答を記録し、9実viewport画像を保存。資料本文8件とMarkdown6件は実リンクから読んだ。外部原典2リンクはローカルの遮断案内への遷移で、公式本文の取得ではない。

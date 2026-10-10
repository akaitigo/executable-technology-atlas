# Atlas｜来歴policy比較の再現と確認状態

固定7条件14応答を1回計算しました。[実行ログ](verification/execution.json)にactual nice10、子1個、15秒上限、exit0、回収済み、retry0を保存しています。全経過0.161570秒、計算0.001416秒です。[作者検査](verification/saved-result-check.json)は189照合・8改変拒否。[保存結果](observations/run-01/results.json)と実行時18入力を保存しました。保存結果readerのGUI確認も1回実施しました。`policy.py` のcompareはartifact bytes、申告digest、claims、期待policyだけを受け取り、bundle全体を引数にしません。`produce.py` は正常版へ別保持policyを、故障版へ同梱policyを渡します。

[7条件](cases.json)・[別保持policy](consumer-policy.json)・[手期待](expected.json)を実行前に固定しています。実行時に18入力をsnapshot保存し、保存計算をproducer非importの検査で手表へ照合しました。手期待は計算結果ではありません。

閲覧の配信は `python3 -B serve.py --port 18780`、入口は `http://127.0.0.1:18780/`。使用中portや他サービスを止めず別番号を選べます。このserverは保存fileを読むだけで、比較処理や外部buildを実行しません。既存教材は固定hashの読取viewer、Markdownはtext/plainで表示します。

新しい有限計算には、直前の全ps/CPU/memory観測と今回の観測SHAへ結び付いた判断、実nice10、1子15秒、再試行0、自己所有子の回収を使います。実行入口は `run.py`、限定実行は `execute_once.py --decision <今回の判断JSON>` です。既存run-01を上書きしません。旧資源判断は実行許可に流用しません。

実画面確認は2026-10-06 23:19:22–26 UTCに3.827秒で完了しました。環境担当が教材用loopbackサーバー1個（PID3372、port64114、nice10）を起動し、既存ブラウザーの同じ1ページを再利用しました。検査module自身のbrowser/context/page/server起動は0です。終了時に自身のroute・listenerを除き、viewportを復元しました。ブラウザー・ページ・サーバーは継続閲覧のため維持しています。

7条件14応答の六つの比較項目・期待の出所・認証未検証表示を実DOMへ保存し、10の切替状態、取得拒否と遅い旧応答の5対照、9枚の1280×900／390×844実画面を確認しました。説明図と照合表は実mouse wheelで右端へ移動して左端0へ戻しています。既存3本文とMarkdown6文書は実クリック後に表示本文を保存版へ照合しました。原典2リンクは正確なURLへの実クリックをローカルの「外部通信を遮断したテスト応答」で確認し、外部転送0・公式本文のGUI取得0です。公式本文の内容確認は制作時の別のweb読取で行っています。条件選択のselectOption API、ページ復帰のgoto API、実pointer操作を実行ログで分けています。

狭幅の説明図は左右に分けて読む表示で、右端では左側の文字が見えません。全体の対応はdesktop表示と保存DOMでも照合しました。

署名・鍵・実builder・build・releaseは未実行です。構造不正のschema拒否コードはありますが、7条件は構造が正しいfixtureに限定し、全schema境界の実測とはしません。元CONTRACTの制作段階の記述を履歴として保ち、最新の工程は[確認状態](qa/reader-acceptance.json)へ保存します。

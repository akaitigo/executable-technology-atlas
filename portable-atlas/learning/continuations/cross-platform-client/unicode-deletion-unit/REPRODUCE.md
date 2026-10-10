# Atlas｜Unicode削除の保存結果を読む

2026-10-06 21:50:40 UTCに、既存Node25.2.1で7要求×3方式と拒否6例を初回実行しました。実ICUは78.1、Unicodeは17.0です。21:54:22〜25 UTCには、保存結果readerのGUIを既存の同じブラウザー・ページで確認しました。

画面を開く時はこのディレクトリで `python3 -B serve.py --port 18778` を実行し、`http://127.0.0.1:18778/` を開きます。portが使用中なら他サービスを止めず別番号を指定します。自分が起動したサーバーの終了はCtrl-Cです。保存資料だけを配信し、画面操作ではNodeを起動しません。

前提2本文は元教材を変更せず固定byte/hashで読みます。元pathが移動・変更された場合は旧内容で成功を装わず読込を止めます。Markdownはtext/plainで配信し、ファイルがあることと画面で本文を読めたことを区別します。

`cases.json` と `expected.json` は実装前の固定表です。[保存結果](observations/run-01/results.json)と必要な8入力の保存版には、実Node/ICU/Unicode版と入力前後・全結果を残しています。[実行ログ](verification/execution.json)は実nice10、子1個、全経過0.1153秒、exit0、回収済み、timeoutなし、再試行0です。正規化・分割部分の計算時間は約0.00075秒で、性能比較の根拠にはしません。

保存値を読み直す場合はこのディレクトリで `node verify.cjs` を使います。これは実APIを再実行せず、手表と整数による符号化へ保存値を照合します。初回実行の入力8ファイルは `observations/run-01/inputs/` にあります。`run.cjs` と `execute_once.py` は既存結果への上書きを拒否します。保存結果を消して再実行する手順にはしません。

初回wrapperは全プロセスを含む直前の資源観測と、その内容に限定した実行判断、実nice10以上、子1個、15秒の上限、既存結果の上書き拒否を確認しました。今回の受入に追加install・OS設定・重いbuildは必要ありません。GUI検査は既存の一つのブラウザー/ページを受け取り、検査module自身のbrowser/context/page/server起動は0です。

今回のGUI環境を準備した担当は、教材用loopbackサーバー1個を起動し、既存ブラウザー・ページを再利用しました。約3.32秒の検査後、専用route/listenerを解除しviewportを復元しています。ブラウザー・ページ・サーバーは継続利用のため維持し、検査module自身は起動・終了していません。

保存した画面記録は `../browser-qa/thread-safety-next-2026-10-06/runs/client-unicode-deletion-unit-20261006-215414-full-01/` です。`report.json` は7要求の全値・21カード・6拒否・15状態・5失敗例、前提2本文とMarkdown6本文、9枚の実viewport画像を束ねています。実pointerクリック102回・wheel1回と、selectOption API63回・同page移動API12回は区別して記録しています。390pxではページ全幅も390pxのまま、図だけを横に320px動かしました。

原典2リンクのクリックでは、追加した固定URL用routeが「外部通信を遮断したテスト応答」を返します。正確な遷移要求だけを記録し、公式本文のGUI取得は未実施です。そのrouteは確認後に解除し、既存の通信制限を変更していません。

# Atlas｜再開判断の再現と確認範囲

既存Pythonで固定5条件と2故障対照を1回計算しました。[実行ログ](verification/execution.json)は実nice10、子1個、15秒上限、exit0、回収済み、再試行0を記録しています。全経過0.108924秒、模型計算0.001196秒です。[保存結果](observations/run-01/results.json)と[作者の検査](verification/saved-result-check.json)は118照合・8改変拒否を分けて保存しています。

`model.py` の復旧関数へ渡すのはcheckpointとnowだけです。`produce.py` のdriverだけが合成効果counterを持ちます。中央2件は同じ `inputs/pending-shared.json` を参照します。実行時の14入力を `observations/run-01/inputs/` に保存し、[復旧実装](observations/run-01/inputs/model.py)を画面から読めます。[手期待](expected.json)は実行前の予想であり、計算結果とは別です。

読むだけなら `python3 -B serve.py --port 18779` でloopback配信し、`http://127.0.0.1:18779/` を開きます。使用中のportを止めず別番号を選べます。条件と予想→保存結果→中央2件の比較→原典・実装→答え合わせの順に操作します。この配信は模型を再実行しません。元教材は固定された読取viewerで表示し、Markdownはtext/plainで読みます。

計算の再実行は通常の閲覧に不要です。再現用の入口は `run.py`、限定実行は `execute_once.py --decision <今回の判断JSON>` です。直前の全プロセス・資源観測と観測SHAに結び付いた判断、実nice10、子1個の期限・回収を必要とし、既存run-01を上書きしません。旧PIDや旧資源許可を流用しません。

実画面は2026-10-06 22:39:56–59 UTCに既存Chromium headlessの1ページで確認しました。全5条件＋2故障対照の表示、10の切替等状態、5つの取得失敗・古い応答、実画像9枚を保存しています。92回の実pointer操作、横wheel2回、selectOption API34回、同page移動API13回は別に記録しました。390×844のviewportで表を0→790→0へ動かし、本文が不変であることも確認しています。この左右操作は比較表の確認であり、説明図の狭幅右端スクロール自体は未確認です。

最初のGUI確認はDISPATCH選択肢の開始タグ欠落で失敗しました。最初の実行記録と旧HTMLを保持し、`revisions/prediction-option-fix/` に1箇所の差分を残しました。修正後は実DOMの5選択値を先に照合してから全対照へ進めています。保存計算の再実行はありません。

配信環境側が教材用loopbackサーバー1個（PID1198、port63070）を起動し、既存ブラウザーと1ページを再利用しました。確認module自身のbrowser/context/page/serverの起動・終了は0です。固有route/listenerを除去しviewportを復元、継続利用のためブラウザー・配信サーバーは維持しています。初回／修正後のGUI記録は、同じindependent-learning内の `browser-qa/recovery-causality-2026-10-06/runs/agent-resume-uncertainty-20261006t223550z-full-01/` と `agent-resume-uncertainty-20261006t223947z-repair-02/` にあります。

前提3本文・Markdown6資料は実pointerで開いて表示本文を照合しました。OWASP/RFCの原典2リンクは、正確なURLへの実pointer遷移をローカル応答で遮断し、「外部通信を遮断したテスト応答」と表示しました。このGUI確認は公式本文の取得ではありません。公式本文の読取根拠は[SOURCES](SOURCES.md)です。Skill3例の有限利用と独立最終判定は[確認状態](qa/reader-acceptance.json)へ結びます。

実再起動・耐久性・外部効果・並行性を試す計画ではありません。`CONTRACT.md` の当初の静的制作という記述は履歴として保持し、継続した計算の条件は `EXECUTION-PLAN.md` と実行ログに分けています。

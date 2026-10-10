# Atlas｜配置条件の再現と確認状態

[固定契約](CONTRACT.md)、[2nodeとpodの定義](topology.json)、[6要求と4拒否](cases.json)、[実装前の手期待](expected.json)を先に固定しました。[計算結果](observations/run-01/results.json)、[実行時の模型](observations/run-01/inputs/placement.py)、[作者の保存値検査](verification/saved-result-check.json)、[実行ログ](verification/execution.json)を照合できます。

2026-10-07 00:15:01 UTC、既存Python 3.9.6で6条件×2応答と4拒否を1回実行しました。模型計算は0.00100秒、子の全経過は0.09780秒、実優先度nice10、子1個、15秒上限、再試行0、終了code0・回収済みです。実装前に固定した手表へ252関係を照合し、9種類のメモリ内改変を拒否しました。作者検査と別担当の確認数は合算しません。実Kubernetes・Docker・外部APIは動かしていません。

先の00:12:14 UTCの[停止理由](verification/runtime-gate.first-hold.json)は保持しています。その時点ではブラウザー群のCPU条件が不成立で、対象を開始しませんでした。別の明示された実行枠で[新しい資源確認](verification/runtime-gate.json)を1回行い、条件成立後だけ開始しています。自動で再試行した記録ではありません。

実行入口は `execute_once.py --decision <今回の確認に結び付いたJSON>`、その子が `python3 -B run.py` です。実行時の12入力は `observations/run-01/inputs/` に保存しています。既存runを上書きする再実行は拒否します。新しい計算を行う場合は保存先と確認範囲を別に定め、直前の全process・CPU・memory、実優先度、期限と自己所有子の回収を確認します。

閲覧はこのディレクトリで `python3 serve.py --port 18783` を実行し、`http://127.0.0.1:18783/` を開きます。使用中なら別の番号を指定します。画面操作は保存値の選択・比較で、模型の再計算ではありません。2026-10-07 00:20:31–00:20:36 UTCに、既存ブラウザーの同じ1ページで実画面を確認しました。環境担当が教材用loopbackサーバー1個（port49209）を起動し、継続利用のため保持しました。検査module自身のbrowser/context/page/server起動は0です。自分のroute/listenerを除去し、viewportと制御欄を復元してページを保持しました。

入力拒否4例はこの教材の狭いschemaに対する結果です。特にExists例はvalueを残した対象外入力で、正しいKubernetes Existsや全schema端点の実証ではありません。入力を受け付けたうえで候補がないPENDINGとも異なります。NoExecute、複数taint、affinity/topology、実schedulerの配置順、Readyは対象外です。

画面では6条件×2応答、4拒否、10切替等の状態、503・404・改変・遅れた旧success/errorの5対照を保存しました。131回の実ポインタークリックと6回のwheelを、selectOptionの48回・同じページへのgotoの13回というAPI操作と区別しています。元2教材と目標47の3本文、6つの文書を実リンク経由で読みました。原典2リンクは正確なURLへの遷移要求をローカル遮断案内で受け、外部送信・公式本文取得は0です。

実画像9枚は1280×900または390×844のviewportです。図はscrollLeft 0→390→0、node条件表は0→520→0、比較表は0→320→0を実wheelで移動し、本文不変を確認しました。旧応答の対照にはAbortによる中止も含むため、世代番号だけを強制検査したとは言いません。

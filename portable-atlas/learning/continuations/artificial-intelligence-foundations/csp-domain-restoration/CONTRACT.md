# Atlas：候補値の削減と、枝を戻るときの復元

## 学ぶ問いと前提

目標06の「小さな制約充足問題を解き、全列挙と別探索で解・探索量を確かめる」に対応します。問いは「一つの枝で除いた候補値を、次の枝にも残さず消したままにすると、正しい解を失わないか」です。前提は有限集合、変数への部分割当、隣接関係、深さ優先探索です。既存のweighted探索・register historyの後戻り探索は前提とし、探索一般を新しい成果へ数えません。[前提](PREREQUISITES.md)と[範囲](COVERAGE.md)へ戻れます。

これはPython標準ライブラリで実行する有限CSP模型です。現実の配置・学習済みAI・物理過程の測定ではありません。解の正しさと、試行や制約検査の回数を分けます。回数から実時間の優劣を主張しません。

## 固定入力

変数順は A,B,C,D、色順は 0,1。制約は無向の二項不等号だけです。辺を両端IDの昇順で正規化し、各変数のneighborをID昇順に走査します。全解を列挙し、最初の解では停止しません。解はABCD順の4文字で識別します。

| 問題 | 辺 | 初期domain | 手で固定した解 |
|---|---|---|---|
| no-edges | なし | 全変数[0,1] | 全16割当 |
| square | AB,AD,BC,CD | 全変数[0,1] | 0101,1010 |
| triangle-isolated | AB,AC,BC、Dは孤立 | 全変数[0,1] | なし |
| anchored-square | AB,AD,BC,CD | Aだけ[0]、他[0,1] | 0101 |

初期singletonのAも探索で1候補を試します。事前に割当済みとは扱いません。domainは未割当変数の残り候補、assignmentは今回選んだ値です。割当時に自身のdomainをsingletonへ書き換えません。割当済みのdomain表示は未割当候補の意味を持たず、assignment欄を参照します。

4問題をbaselineとforward-checking（FC）の2方式で比較し、squareのみFCのrestoreを省く故障版を追加します。合計9結果を対象process1回で保存します。故障版は合法なPython実行として正常終了し得ますが、全解保存という設計契約に違反します。UNSAT（解集合が空）、意図故障の解欠落、入力拒否、実行失敗を区別します。

## 探索と復元の固定手順

詳細は[PSEUDOCODE](PSEUDOCODE.md)。search入側で現在変数のdomainを色順の候補snapshotへ一度コピーします。各候補について、すでに割り当てたneighborを順に不等号検査し、最初の不一致で棄却します。成功ならassignmentへ加えます。

baselineはdomainを削減せず次変数へ進みます。FCは未割当neighbor順に、そのdomainの色順snapshotへ不等号検査を行い、違反値を削除してtrailへ保存します。一つのneighbor処理後、そのdomainが空なら即座にその枝を打ち切り、後続neighborは未走査、再帰呼出しもありません。このFCは新しい割当と隣接する未割当変数だけを調べ、AC-3や全辺のarc consistencyではありません。

正常FCは、成功葉・矛盾のどちらから戻る場合も、枝に入る直前のtrail markまで逆順に復元し、その後assignmentから今回変数を消します。次候補は最初に固定したsnapshotから選びます。全解列挙の最後に、assignmentは空、全domainは初期値へ戻ります。故障版は**すべての枝のrestore呼出しだけを省略**し、その他の手順を変えません。故障版のtrailは削除の記録として蓄積します。

空domainの検出はその部分割当に矛盾がある根拠です。未完の部分割当でdomainがすべて非空でも、全体に解があるとは限りません。三角は初期domainがすべて非空でも2色の解がありません。今回の全列挙結果を一般CSPや任意実装の完全性証明にはしません。

## 計数の定義

| counter | 増やす時点 |
|---|---|
| search_calls | searchに入るたび1。深さ4の成功葉も含む |
| candidate_attempts | 候補snapshotから1値を取り出すたび1。整合性拒否も含む |
| assigned_constraint_tests | 割当済みneighbor1件とのneqを実際に調べるたび1。最初のfalseで停止 |
| consistency_rejections | 上記neqがfalseで候補を棄却したとき1 |
| propagation_tests | FCで未割当neighborの候補値1件とのneqを実際に調べるたび1 |
| removed_values | FCが実際にdomainから値を一つ削除したとき1 |
| restored_values | 正常restoreで値を一つ戻したとき1。故障版は0 |
| domain_wipeouts | neighbor処理後の空domainによりFC枝を打ち切ったとき1 |
| solutions | 深さ4でassignmentのコピーを解へ保存したとき1 |

APIの呼出し回数、CPU時間、探索nodeの一般定義とは混ぜません。毎eventのassignment/domain/trailはコピーで保存し、後の変更で過去の列を書き換えません。規定した全順序はこの逐次模型の実行順であり、実分散処理の時系列ではありません。

## 期待と受入

作者と独立担当はproducerを読む前に全16割当から4問題の有効集合、9結果のcounter、square/triangle/faultの代表domain列を手で固定します。producerはexpectedを読みません。保存値checkerはproducerをimportせず、全割当の制約照合と手表へ照合します。解欠落、復元漏れ、削除理由の偽装、counter差し替え、stdout結合の改変を、対象の意味ラベルが失敗することまで確認します。

保存するものは入力・実装・手期待・Python/OS版・実コマンド・完全stdout/stderr・exit・資源判断・SHA・有限cleanupです。readerは予想→条件/時点操作→正常と故障の比較→原典/実装→答え→実務判断/限界の順にします。実DOM・1280/390の実viewport画像・資料導線・Skill6問を独立担当と照合し、最終receiptとstatus読戻しで閉じます。図は保存した模型結果の説明であり、実世界の配置図ではありません。

## 実行条件と現在位置

契約固定時点は対象実行0、GUI0。既存MacのPython標準ライブラリのみ。新SDK/install/設定/サービス/共有元編集はありません。独立期待とコードreview、新しい所有identity判断、rootの単独枠、60秒以内のfresh全ps・資源gateが成立した場合だけ1子を開始します。実nice>=10、wall3秒、CPU soft2/hard3秒、自動retry0、有限kill/waitと所有groupの回収を保持します。現行成功guardを最小差分で再利用し、未採用の「未分類CPU>10」追加停止は導入しません。具体的guardと今回は別のdecisionを実行前資料へ固定します。

作者によるbrowser/context/tab/server開始・終了は0。rootが提供する同じpageで後続GUIを確認します。原repo/旧教材/共有計画はread-only、元owner不明を不存在とは扱いません。全体加算はroot判断、作者加算0です。

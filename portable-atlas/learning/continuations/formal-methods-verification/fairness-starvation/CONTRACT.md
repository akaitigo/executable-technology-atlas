# Atlas：公平性の対象を変え、飢餓の循環を読む

この契約・モデルの読み方・手書き期待を、計算プログラムの実装前に固定します。専有先はこのディレクトリだけ。元分野 owner の現況は未確認です。元 repo、旧教材、共有計画、受入台帳は変更しません。

## Atlas の目標と既存成果との差



旧 mutex の正常部分は8到達状態・14非停滞遷移の相互排他検査です。[完全一致コピー](inputs/prerequisite-model.py) の `atomic` だけを前提に使います。旧2 lock教材は停止状態と解放/再試行循環、旧ループ教材は不変条件と終了で、公平性付きの飢餓判定は範囲外と記されています。[重複確認記録](records/input-and-dedup.json) の既知台帳では同じ受入を見つけていませんが、全PCの不存在を断定しません。これら旧成果は再加算しません。

## Atlas の有限モデル

状態は `(pc0, pc1, owner)`。各pcは idle / waiting / critical、ownerはfree / 0 / 1です。元の正常モデルと同じ原子的な3動作を使います。

- `P_i.request`：idle→waiting。ownerは変えない。
- `P_i.enter`：waiting かつ owner=free のとき、pcをcritical、ownerをiへ同時に変える。
- `P_i.release`：critical→idle、ownerをfreeへ同時に戻す。

二者が同時にcriticalにならない安全性は前提の対照で、今回の新しい問いは `P1 が waiting なら、その後いつか critical になるか` です。既存14辺に、各状態で同じ状態に留まる `stutter` を明示的に1本ずつ加えます。これで8状態・22辺の説明用graphです。stutterはprocess番号を持たず、どのprocess/actionを実行したことにも数えません。実thread、OS scheduler、実時間の観測ではありません。

## Atlas の公平性の定義と対象

Lamport著者本文 [Session 9 §5 Semaphore Liveness](https://lamport.azurewebsites.net/tla/tutorial/session9.html) を2026-10-06に実読しました。動作の弱公平性は、継続して実行可能なままなら永遠に見送らない条件です。強公平性は、実行可能になる状態が無限回ある動作を、永久に選ばない列を除きます。状態を変えない停滞は進行動作に数えません。livenessは待ち時間上限の保証とも別です（同§6）。

この教材の process 動作 `Next_i` は `request / enter / release` の和集合です。idleのrequestも含む独自の対象で、PlusCalの全ての `fair process` 宣言や非critical区間の例外と同一視しません。各状態でNext_iがenabledとは、そのprocessの非stutter辺が1本以上存在することです。Enter1は `P1.enter` だけを指します。

導入部分 prefix の後、長さ1以上の閉じた cycle を無限に繰り返す列だけを判定します。保存するのは有限の一周で、無限時間を実行・観測したものではありません。周期列では以下に簡約できます。

- `WF(A)`：cycleの全状態でAがenabledなら、cycle内にAの実行が1回以上必要。それ以外は満たす。
- `SF(A)`：cycleのどこかでAがenabledなら、cycle内にAの実行が1回以上必要。それ以外は満たす。

有限prefixだけで公平性を判定しません。enabledは辺の出発状態で評価し、executedは選んだ辺が対象の非stutter動作かで判定します。

公平性の仕様は4つを別々に比較します：条件なし、`WF(Next_0) ∧ WF(Next_1)`、`SF(Enter1)`だけ、`WF(Next_0) ∧ WF(Next_1) ∧ SF(Enter1)`。3つ目は意図的に解放の公平性を含めない対照です。Enter1へ強公平性を追加するだけで常に進めるとは言いません。

## Atlas の実装前の6列

初期Iは `(idle,idle,free)`。A=`(idle,waiting,free)`、B=`(waiting,waiting,free)`、C=`(critical,waiting,0)`。完全な状態/辺/真偽列は [expected.json](expected.json) に固定します。

|名前|prefixの終点と繰り返すcycle|P1の進行|公平：なし / WF両 / SF入室1のみ / WF両＋SF入室1|
|---|---|---|---|
|Aで停滞|P1.request→A。Aでstutter|要求後に進まない|true / false / false / false|
|Bで停滞|P1.request、P0.request→B。Bでstutter|要求後に進まない|true / false / false / false|
|P0保持中に停滞|同上＋P0.enter→C。Cでstutter|要求後に進まない|true / false / true / false|
|P0が取り続ける|P1.request→A。P0.request、enter、releaseでAへ戻る|P1は機会が断続的に来ても進まない|true / true / false / false|
|両者が進む対照|prefix空。IからP1のrequest/enter/release、P0の同3動作でIへ戻る|各要求を満たす|true / true / true / true|
|以前の入室で後の要求を満たさない|prefixでP1.request/enter/releaseの後、再度P1.request→A。その後P0の3動作を反復|最初の要求は満たすが、新しい要求は進まない|true / true / false / false|

CでP1.enterは全くenabledでないため、SF(Enter1)だけなら公平性条件を満たしてしまいます。一方でP0.releaseは選べるので、これは非stutter辺0のdeadlockではありません。P0が循環する列ではP1.enterのenabledは `[true,true,false]`、P1の実行は0です。継続enabledと断続enabledの差が表れます。

期待される飢餓反例は「列が有効」「P1の要求が満たされない」「選んだ公平性仕様を満たす」の3条件を分けて記録します。安全性違反や、不公平な列を公平な反例と混同しません。正対照も含め、P1の要求と入室をprefix/cycleの境界を越えて追います。

## Atlas の検証・表示・限界

実計算は固定6列の出発/到着状態・enabled/executed履歴・公平性・P1進行の照合です。任意の全閉路を列挙するcheckerやTLC実行、一般の時相論理の決定手続は実装しません。5本の反例が最後の公平性仕様で除かれたことだけから、全モデルの飢餓自由を証明したとは言いません。追加の一般的議論を載せる場合も、有限な保存計算と紙上の導出を分けます。

別担当はコードを読む前に独立期待を固定します。無効な辺、cycleが閉じない列、stutterをprocess実行と誤認する値、enabledのany/all混同などは、保存した値の改変検査で区別します。原子性・weak memory・任意process数・故障・実scheduler・待ち時間上限は保証しません。

実行は契約レビュー後、rootの単独実行枠を確認してからです。Python標準ライブラリーだけ、子1・worker0・対象再試行0。直前の正式読取でload<6、idle60%以上、メモリ空き照会40%以上/推定2GiB以上、読取時の全体busy CPU相当が400%以下（(100−idle%)×CPU数、12 CPU機の4コア相当以下）、既知重処理/headlessなし・他の担当対象計算0、読取不明を0にしないことを確認。起動前にnice10以上の実値を確認し、CPU2秒・経過3秒、自己所有groupのTERM後0.5秒/KILL後1秒回収を有限に行います。新しい保存先へ完全出力・入力hash・環境・失敗を残します。

予想→prefix/cycle操作・対照→原典/実装→答え→限界の説明と限定Skillを用意します。この契約を固定した時点では、実装/計算/実DOM/画像は未実施です。現在状態はstatus.jsonへ分けます。GUI/browser/image/installは行わず、全体受入false・作者加算0・元統合未実施を維持します。

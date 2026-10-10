# Atlas：未割当の候補へ伝えるAC-3

## 問いと前提

[範囲](COVERAGE.md)に結んだ目標06と前作FCを前提に、「隣への一巡で止める場合と、候補の変化をqueueで伝える場合の違い」を調べます。二項不等号だけの有限模型です。AC-3の固定点と全体の解を分け、削減なしの三角にも全解がない対照を置きます。前作の探索/復元を再実装した成果として数えません。

## 固定する4条件

変数はA,B,C,D、色は0,1。無向辺はIDの昇順で正規化し、重複なし、neighbor順はID昇順です。

| ID | 辺 | 初期domain | 既に固定した割当 | 全16割当からの有効集合 |
|---|---|---|---|---|
| chain-anchored | AB,BC,CD | A:[0]、他:[0,1] | A=0 | 0101 |
| triangle-anchored | AB,AC,BC、D孤立 | A:[0]、他:[0,1] | A=0 | なし |
| triangle-free | AB,AC,BC、D孤立 | 全[0,1] | なし | なし |
| square-free | AB,AD,BC,CD | 全[0,1] | なし | 0101,1010 |

A:[0]は入力側で指定した制約です。前作は探索中の割当と自身のdomainを分けましたが、今回はAC-3へ渡す入力で固定割当をsingletonに正規化します。旧教材の状態を書換えず、この変換を明示します。AC-3はassignmentを追加しません。singletonを見つけたことと探索による全解列挙は別です。

## FCの対照

固定割当がある2条件だけ、A=0と隣接する未割当neighborの候補を一巡して、不等号に違反する値を削除します。neighborと候補値は昇順、neighborの候補snapshotを使います。一つのneighbor処理後に空なら停止します。固定割当のない2条件は起点がなく、何も削除しません。これは前作のFC一段を取り出した比較であり、前作の探索全体を実行するものではありません。

FCのcounterはconstraint_tests（候補との実比較）、removed_values（実削除）、empty_domain_stops（空により停止）です。全割当の独立照合やAC-3の比較回数を加えません。

## AC-3の固定手順

[PSEUDOCODE](PSEUDOCODE.md)に従います。各辺の両方向を有向arcとし、(tail,head)の辞書順でFIFO queueへ一度入れます。queue内の集合を別に管理し、同じarcの同時重複を入れません。popで先頭を取り出したら集合からも除きます。

REVISE(tail,head)はtail値の昇順snapshotを走査し、各xに対してhead値の昇順snapshotから最初のx≠yをsupportとして探します。一つでもあればxを残してhead走査を止め、なければxを削除します。tailの全snapshot値を処理した後、tailが空ならその場で停止し、後続arcや追加queueを処理しません。

削減がありtailが非空なら、tailのneighbor kを昇順に調べ、k≠headのarc(k,tail)をqueueへ追加します。既にqueueにあれば追加せず、skipを記録します。head自身への逆arcは追加対象にしません。削減がなければ追加なし。queueが空ならarc-consistentの固定点として終了しますが、SAT判定とは呼びません。初期domainは全条件で非空です。

AC-3のcounterはinitial_arcs（初期queue長）、revise_calls（popしたarc数）、support_tests（実際のx≠y比較）、removed_values（実削除）、queue_added（初期分を除く実再追加）、queue_skipped（再追加候補が既にqueueにあった回数）、empty_domain_stops（空で停止）です。support取得後の比較や未処理の残queueは数えません。値のないheadへの比較は0回で、tail値にはsupportがなく削除されます。

## 期待と証拠

実装前に全16割当、FC後domain、AC-3のpop順/各revision後domain/queue、counterを手で固定します。期待をproducerから生成せず、producerはexpectedを読みません。手期待には三角の空停止後に残る未処理arc、free三角の全support存在と全解なし、free四角の同じdomainでも全解2個を残します。

eventは入力・pop・各候補のsupport比較・削除・revision完了・追加/skip・空停止・終端を保存します。domain/queueは各時点のcopyで保存し、後の変更で過去の記録を変えません。全割当による判定は探索の実行列ではなく独立oracleです。図も合成模型の説明であり、現実の配置や並行実行の観測ではありません。

受入予定は4条件の保存値と独立手表の一致、削除理由/queue/非空固定点とSATを分ける検査、前提→予想→FC/AC-3比較→原典/実装→答え/限界→Skillの導線です。実行・GUI・画像がない段階は未確認のままにします。

## 今の作業上限

今回はSRE/ISU優先で、文書・実装前期待・小実装・軽い構文/参照確認だけです。模型/producer実行、重いtest、browser/serverは開始しません。実行版の資源/単独枠は後でrootが判断し、既存許可を流用しません。新repo/install/SDK/設定変更/共有編集なし。作者加算0、一般CSPの完全性・GAC・速度・全体SATの保証なしです。

# Atlas — 観測した時刻と届いた時刻を分ける

## 問いと前提

目標90の timestamp/unknown を扱います。既存の点grid・観測後の次edge検査、footprintの幾何判定、観測遅延と制動距離は前提です。今回は新しいplanner、BFS、footprintや制動を実装しません。単一の合成観測源と共通の理想整数時計で、更新の順序と期限だけを比較します。

位置は固定(0,0)、検討する次edgeは(0,0)→(1,0)。対象cell C=(1,0)の知識だけを保存し、実worldの占有状態は入力しません。MOVE_ALLOWEDはこの模型で次edgeの許可条件が成立するというラベルで、実移動、非衝突、実robot安全の証明ではありません。

## 時刻・version・状態

各stepに判断時刻 `now` と到着 `arrival` を置きます。到着があるときは `arrivedAt=now` で、到着の処理直後に判断します。到着なしのstepもあります。観測の `observedAt` は見た時刻であり、届いた `arrivedAt` とは別です。すべて今回の整数単位で、wall clockや実通信遅延の測定ではありません。

観測は `version`、`observedAt`、`arrivedAt`、`state` の4キー。stateはfree/occupied/unknown。versionは単一観測源の正整数の番号です。保持状態は `state, observedAt, arrivedAt, adoptedVersion, mapRevision`。初期値はunknown/null/null/0/0、version0はまだ未採用の印です。mapRevisionは受け入れた更新の件数で、観測versionと同じ数とは限りません。

期限TTL=4。保持観測の `age=now-observedAt` とし、0≤age≤4ならfresh。ちょうど4を有効、5を期限超過にします。新しい到着があっても拒否した観測で保持時刻や期限を延長しません。期限超過で保持値そのものやversionを消さず、判断に使うeffectiveStateだけunknownにします。freshなunknownもfreeではありません。 保持観測がまだないときはage/freshともnullです。到着した観測のincomingAgeは保持観測のageとは別の診断欄に残します。

## 比較する2方式

保守版 `guarded` は入力の型/キーを検査した後、到着を次の順で判断します。

1. observedAt>nowならfuture-observationとして拒否。
2. version≤adoptedVersionならstale-versionとして拒否。
3. 既に保持していてobservedAt<保持observedAtならtime-regressionとして拒否。
4. now−observedAt>4ならexpired-at-arrivalとして拒否。
5. それ以外は受入。4つの観測欄を保持し、mapRevisionだけ1増やす。

同observedAtはversionが増えれば受入可能という独自規約です。同じnowで複数到着する列は今回含めません。拒否は保持状態全体を不変にします。到着なしも保持不変です。

故障対照 `arrival-only` は型/キーの検査を共用しますが、到着のたびに無条件で上書きしmapRevisionを増やします。version/観測時刻の順序と期限を判断に使いません。診断欄には両方式ともage/freshを計算しますが、この方式のeffectiveStateは古くても保持stateのままです。したがって故障は順序と期限の検査を省いた複合対照です。各固定列でどの差が効いたかを分けて読みます。

両方式とも effectiveState がfreeならMOVE_ALLOWED、occupiedならSTOP_OCCUPIED、unknownならSTOP_UNKNOWN。判断は更新後に行います。unknownをfreeへ補完しません。inputの型不正による拒否と、正しい形式の観測を更新方針で拒否することは別です。

## 固定5列・15時点

| ID | 到着と判断時刻 | 対照 |
|---|---|---|
| ordered | 0:free v1/観測0、2:occupied v2/観測2、4:free v3/観測4 | 正順の更新は両方式同じ |
| reversed-clear | 6:occupied v2/観測6、7:free v1/観測4、10/11:到着なし | 古いclearを拒否。拒否で期限を延長しない |
| expiry-boundary | 0:free v1/観測0、4/5:到着なし | age=4は有効、5はunknown |
| expired-arrival | 10:free v1/観測5、11:occupied v2/観測11 | 届いた時点で古い情報を拒否、次の新情報は受入 |
| explicit-unknown | 0:到着なし、1:unknown v1/観測1、2:free v2/観測2 | 未観測と明示unknownはいずれも停止、根拠は区別 |

入力は [cases.json](cases.json)。手追跡は [expected.json](expected.json) を実装前に固定します。各時点×2方式で保持前後、更新受入/理由、観測/到着時刻、採用version/更新回数、age/fresh/effectiveState、次edge判断を保存します。beforeとafterの入力も型込みで照合します。実装と別担当の手表を比較し、保存コピーの時刻・version・unknown・境界・拒否後変更・型の改変を有限に拒否します。

## 有限範囲と実行

固定5列だけを実行します。nowは非負整数かつ列内で厳密増加、観測時刻/到着時刻も非負整数（bool不可）、versionは正整数、キー/状態を限定します。future、同観測時刻、version増加だが観測時刻逆行、不正schemaの枝はコードの静的読取に限り、今回の実行例として網羅しません。

これは教材固有の方針で、Nav2標準のmap更新規約ではありません。ROS/実sensor/実通信、時計ずれ、複数観測源、認証、map fusion、認識誤差、実worldの変化、実移動、一般の安全停止は範囲外です。unknownや期限切れという知識の状態から実worldの占有を断定しません。

Python標準ライブラリの1子、実nice10以上、5秒以内の初回1回を共通実行器で行います。作者による独自target/browser/server起動はありません。契約と手表は実行前固定の記録で、現在の実施状態は [確認状態](qa/reader-acceptance.json) から辿ります。

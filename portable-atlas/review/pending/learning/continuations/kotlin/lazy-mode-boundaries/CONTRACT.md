# Atlas KR-03：lazy の計算回数と共有される値を分ける

専有先はこのディレクトリだけ。元 Kotlin repo、KR-01/02、旧教材、共有台帳は読取り専用です。[受入済み KR-02](../kotlin-delegation-concept-map/README.md)とその [実行前契約案](../kotlin-delegation-concept-map/KR-03-CONTRACT.md)を引き継ぎます。既存 owner の現況は未確認、共有元へ統合しません。

## Atlas の問い・前提・根拠

三 mode の初期化関数を呼ぶ回数、各読取りで返る Token の値と参照の同一性を区別する。前提は関数値、Lazy、同じインスタンス、thread、AtomicInteger、開始合図、Future の終了待機。Epoch 2026-08-28、Kotlin 2.4.10 / stdlib 固定 commit 5687445832cd835b4509b9fbc264cdf1a8201093。KR-02 の Lazy.kt 54–87 / LazyJVM.kt 15–46・63–149 の本文へ戻ります。

SYNCHRONIZED と PUBLICATION を同じ二読取り入力で比較し、PUBLICATION の初期化回数は 1 または 2 と先に固定します。NONE は同じ main thread の逐次対照だけです。結果を二回初期化へ寄せる retry はしません。例外・再入・NONE の並行・他 platform・性能は対象外。専用 proof 10件全体を閉じません。

## Atlas の固定五条件

各条件で新しい Lazy と AtomicInteger を用意します。initializer は count を一つ増やして Token(id=count, marker=7) を返すだけで、例外・再入・待機はしません。Token の値は構築後に変えません。

| ID | mode / 入力 | 固定した期待 |
|---|---|---|
| seq-synchronized | SYNCHRONIZED / main が2回読む | 初期 count0・未初期化、最終 count1・初期化済み、2結果の参照が同じ、id1・marker7 |
| seq-publication | PUBLICATION / 同じ入力 | 同上 |
| seq-none | NONE / 同じ入力 | 同上。並行安全性の根拠にしない |
| concurrent-synchronized | SYNCHRONIZED / 2 worker が各1回、終了後 main が1回読む | 初期 count0・未初期化、最終 count1・初期化済み、3結果は同じ参照、id1・marker7 |
| concurrent-publication | PUBLICATION / 同じ入力 | 最終 count1または2、初期0→初期化済み、3結果は同じ参照、共通 id は1..count、marker7 |

`expected.json` は手書き期待値。生成結果から作り直しません。参照同一性は Kotlin の `===` で比較し、値の一致や identityHashCode の一致で代用しません。PUBLICATION で count1 なら複数計算は今回未観測と記録します。

## Atlas の実行順序と終了

一つの JVM が五条件を逐次実行します。並行条件は固定2 thread の ExecutorService を使い、各 worker が ready を通知して読取り前の CountDownLatch(start) を待ちます。main は ready の有期限待機後に start を解放します。initializer 内には二者の合流待機を置きません。主な事象は連番付きで記録しますが、記録順が CPU 内部の全順序を表すとは主張しません。

各並行条件は開始から共通の絶対 deadline 2秒。ready.await と各 Future.get はその残り時間だけ待ちます。Future を番号順に受け取ることと実際の完了順を区別します。worker の読み終えた記録は別に残します。main の再読取りは両 Future が正常終了した後です。

finally で start を解放、全 Future を必要に応じ cancel(true)、ExecutorService を shutdownNow、最大1秒 awaitTermination。正常時も終了確認します。未回収や worker 失敗があれば次条件は開始しません。JVM は部分結果を先に各行 JSON として出し、失敗行と回収状態を保存して非0終了。外側の runner は deadline 時点までの stdout/stderr を保持します。

## Atlas の資源と低優先度の必須条件

固定の既存 compiler cache と OpenJDK 17.0.17 だけを使います。compile1回、JVM1回、最大2 worker、同時 owned JVM1、retry0。compiler heap256 MiB / JVM heap64 MiB、ActiveProcessorCount=1、nice10以上を必須とします。compiler15秒、JVM10秒、一連の runner45秒上限。timeout後は自己所有 process group に TERM、0.5秒待機、必要なら KILL、さらに最大1秒回収を別の猶予として許可します。終了確認不能は失敗であり次処理を始めません。

子起動前に Python launcher が自分の nice を設定し、getpriority の実値が10以上であることを保存してから exec します。setpriority失敗、読取り失敗、実値不足なら compiler/JVM を開始せず非0終了。nice コマンドの終了コードや stderr の無視で通しません。launcher と子は自己所有の別 process group とし、他 process へ変更・signal を送りません。

root が他の重処理と実行枠を直列化します。直前に load<6、既知重処理なしを通常の正式読取りで確認し、全体 idle・CPU数・メモリ圧力と推定空きも記録します。読み取れない値を0としません。小さい処理の目安は idle25%以上、memory free20%以上、推定空き2GiB以上、他 headless browser なし。余裕は確保保証ではありません。条件不成立なら待機retryを繰り返さず実行未実施を保存します。

## Atlas の受入・教材・除外

固定 source・expected・toolchain hash、完全 stdout/stderr、開始と終了、count、id/marker、参照同一性、許容集合への一致、worker終了、失敗を結びます。準備失敗・優先度設定拒否・compile失敗・JVM未到達・実行失敗・検証不一致を分けます。未観測の多重初期化を成功表示で補いません。

保存結果を読む画面は予想→操作/対照→原典/実装→答え→限界、図は実測を説明する模型と表示します。新実験と画面での再生を分離し、元学習経路・限定 Skill を結びます。ブラウザーは別の共有枠通知後だけ、自己所有 profile・サーバーを使い終了します。

review_loop が期待値・実装・保存結果・画面を独立確認します。局所受入は人による Authority 正式分類や全 mode の一般証明ではありません。新教材数への加算はrootが最後に判断し、作者は0を維持します。SDK install、サービス作成、OS設定、Docker変更、公開・commit/pushは行いません。

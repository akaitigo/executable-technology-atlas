# Atlas：lazy の計算回数と共有される値

[操作画面](index.html)と固定期待値で、逐次の三 mode と二者で読む二 mode を比べます。初期化関数の呼出し回数と、返った値・参照の同一性を別々に確かめる教材です。実測と受入の最新状態は [status.json](status.json) に保存します。

**固定した五条件を初回 compile1回・JVM1回で実行しました。** [実行ログ](observations/attempt-20261006T143938970174Z/run.json)は、逐次三条件と並行SYNCHRONIZEDの計算が各1回、並行PUBLICATIONが2回です。PUBLICATIONはToken id1/id2を作りましたが、worker1/worker2/mainは全てid1・marker7・同じ参照を返しました。[保存結果の125照合と6改変拒否](observations/attempt-20261006T143938970174Z/verify.stdout.json)は通過しています。実画面・画像・最終受入は別の状態として管理します。

[実画面の確認](GUI_VERIFICATION.md)は20項目・84回の実ポインター操作・五条件×三時点の実DOM保存を通過し、7枚を目視しました。見出し内の文字色だけを修正した後、header2枚・4確認を追加し目視しています。計9枚の画像と、全面検査/限定追補の違いを保存しています。別担当の受入結果は状態記録を参照してください。

以前の load11.89 / 6.55 による未起動は [二回の判断](records/execution-decision-2.json)と [未実行版](records/pending-final/binding.json)に保存しています。その後の明示された専有枠で load5.9004、idle74.59%、memory42%、推定4.983GiB、既知重処理/headless検出0を確認して初めて実行しました。期待値や実装を結果に合わせて変更していません。

## Atlas の使い方

この README・[原典](SOURCES.md)・[コード](src/LazyModes.kt)と画面を使います。以下をこの教材ディレクトリで起動し、表示された `http://127.0.0.1:.../` を開いてください。空いているポートを自動選択します。終了は Ctrl+C。画面は compiler や JVM を起動しません。

```sh
python3 -B preview.py --port 0
```

1. 条件を選び、初期化回数と返る参照を予想する。
2. 保存した記録を開き、読む前→読取り結果→期待値と終了確認へ進む。固定期待表と概念模型は測定結果と分けて読む。
3. 原典と実験コードへ戻り、計算回数・id / marker・`===` を分ける。
4. 最後の時点で答えを開き、予想と今回の結果を照合する。
5. この有限条件から判断できない範囲を確認する。自由記述の自動採点はしない。

## Atlas で分かること

- 同じ Lazy の値を二回読むことと、二回計算することは違う。
- PUBLICATION では計算回数が複数でも、公開する値は一つという規則を読む。
- 今回の二者では初期化回数 1 または 2 を許容する。1 回でも有効な観測で、2 回を得る再試行はしない。
- id と marker が等しいこととは別に、`===` で参照の同一性を観測する。
- NONE の逐次成功を、並行安全性へ一般化しない。
- worker の終了を確認してから main が再読取りする理由を説明する。

## Atlas の固定入力と実装

[実装前の契約](CONTRACT.md)・[手書き期待値](expected.json)は実装前に固定しました。[準備記録](records/pre-implementation.json)にそのハッシュがあります。各条件の Lazy は別インスタンスです。Token は `id` と `marker=7` を持ち、構築後に変更しません。

| mode | main の逐次 2 回 | 2 worker 各 1 回＋終了後 main |
|---|---|---|
| SYNCHRONIZED | 計算 1 回・同じ参照 | 計算 1 回・同じ参照 |
| PUBLICATION | 計算 1 回・同じ参照 | 計算 1〜2 回・同じ参照 |
| NONE | 計算 1 回・同じ参照 | 今回は実行しない |

これは固定期待表です。[実施状態の案内](reader-data.json)は今回の実行ログへつながります。並行PUBLICATIONは今回2回でしたが、1回でも契約内であり、複数回になるまで反復していません。期待表と測定値を分けています。

[Kotlin コード](src/LazyModes.kt)は、読む前の開始合図、共通の 2 秒期限、Future の結果、main の再読取り、終了確認を記録します。initializer 内に二者の合流待機を置かないため、SYNCHRONIZED がロックを持つ間に相手の初期化待ちで止まる構造を避けています。記録用の同期や CPU 設定も処理順に影響し得るため、観測回数の分布や性能を測る実験ではありません。

## Atlas の検証と新しい実験を分ける

通常は保存済みの結果を読みます。以下は今回の保存ログだけを照合する手順で、compiler / JVM を起動しません。

```sh
python3 -B verify.py --run observations/attempt-20261006T143938970174Z/run.json --mutations
```

新しい実験は通常の閲覧には不要です。必要な場合だけ他の作業と実行枠を合わせ、次の順序を使います。

```sh
python3 -B resources.py
python3 -B run.py --execute --resource-record records/表示された資源記録.json
```

固定 cache は [toolchain-readback.json](records/toolchain-readback.json) にあります。追加インストールを行わず、compiler 125 ファイルと JDK の bytes を実行前に再照合します。compiler 1 回・JVM 1 回、各 15 秒 / 10 秒、一連の処理 45 秒、最大 2 worker。失敗時は停止し、部分出力と回収状況を残します。nice 実値 10 以上を確認する前には対象を exec しません。設定失敗や exec 失敗を実起動に数えず、未確認の起動も区別します。

`ActiveProcessorCount=1` は JVM が利用可能とみなす CPU 数の設定であり、OS の厳密な CPU 使用率制限ではありません。heap 256 / 64 MiB はプロセス全体の常駐メモリ上限ではありません。load・idle・メモリの読取りは、その瞬間の余裕の判断です。将来の余裕や未知の重処理がないことを保証しません。

## Atlas の原典・限界・学習経路

[SOURCES](SOURCES.md)は Epoch 2026-08-28 と Kotlin 2.4.10 の固定本文・行・ハッシュを結びます。[前提一覧](references.html)から、KR-02 の概念図・既存 LazyProbe の逐次成功・KR-01 の限定した案内へ戻れます。[COVERAGE](COVERAGE.md)は実測と未対応の境界、[Skill](skills/atlas-lazy-mode/SKILL.md)は保存結果を使う案内です。

NONE の並行、initializer の例外後再試行、再入、他 platform、性能は未検証です。一般の property/class delegation の動作を今回の lazy の結果で埋めません。専用検証課題 10 件全体や、正式な人の意味分類、元 repo への統合、Atlas 全体の完了を意味しません。作者による教材数への加算は 0 です。

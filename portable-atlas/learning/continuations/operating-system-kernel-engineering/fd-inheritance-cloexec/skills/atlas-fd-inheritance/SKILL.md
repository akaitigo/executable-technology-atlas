---
name: atlas-fd-inheritance
description: Atlas の保存済み4条件から fork・exec・FD_CLOEXEC の違いを案内する。全OSや未測定のoffset・thread安全性へ保証を広げない。
---

# Atlas：FD 継承を保存結果から案内する

通常は [README](../../README.md) から保存結果を読みます。この Skill 文書を置いたことと、Agent の案内評価を実施したことは別です。専用 Router や自由な質問への自動判定は含みません。

## 通常の手順

1. 依頼が「fork/exec の違い」「CLOEXEC on/off」「複製 FD の個別設定」「親に参照が残るか」のどれかを確認する。混合要求では、対応する部分と未測定の部分を分ける。
2. [契約](../../CONTRACT.md) と [固定期待値](../../expected.json) を読み、利用者の予想を聞く。[画面](../../index.html)をローカル配信するなら教材のルートで `python3 -B preview.py` を実行し、表示した loopback URL を使う。
3. 記録を開き、親→fork 後の子→exec 後の子→wait 後の親を比較する。PID、FD 番号、印、dev/ino、8 バイトを [実行ログ](../../observations/attempt-20261006T125518537210Z/run.json) と照合する。
4. 保存結果だけを再検証する通常コマンドは、教材のルートで `python3 -B verify.py --run observations/attempt-20261006T125518537210Z/run.json`。実験は再実行しない。記録欠落・digest不一致・途中失敗なら、その状態を伝えて推測で結果を埋めない。
5. [原典](../../SOURCES.md) と実装へ戻り、予想を自己確認する。[未対応範囲](../../COVERAGE.md)を明示する。

`fork/exec とスレッド安全性を保証して` のような依頼でも、4条件の成功を thread 安全性や全 OS の保証へ換算しません。offset 共有は原典上の契約と、今回未測定であることを分けます。Python os.dup の初期設定を C の dup の実測とは呼びません。

## 新しい実測が依頼された場合

保存結果の閲覧とは別の操作です。対象・所有範囲と現在の資源余裕を確認し、許可された範囲でのみ `python3 -B experiment.py --record` を使います。自己所有の 8 バイト、一度に 1 子、低優先度、観測期限と有限の回収待ちを維持します。既に許可された同じ操作を繰返し承認依頼する必要はありません。

新しい attempt を保存し、失敗も残してから独立検証します。古いログ・入力ハッシュを上書きしたり、期待 EBADF を実行失敗と混ぜたりしません。別環境・別ケース・timeout の原因解消前に無条件の連続再試行をしません。共有 repo、OS 設定、他プロセス、Docker、SDK、外部公開はこの Skill の範囲外です。

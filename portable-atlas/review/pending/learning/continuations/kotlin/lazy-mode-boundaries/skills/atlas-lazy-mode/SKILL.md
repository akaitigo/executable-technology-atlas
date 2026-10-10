---
name: atlas-lazy-mode
description: Atlas の保存した五条件から、Kotlin lazy の初期化回数と返る参照を分けて案内する。
---

# Atlas：lazy mode の限定した案内

対象は固定 Kotlin 2.4.10 / JVM 17 の成功する initializer です。初期化回数・返る Token の id/marker・`===`・worker 終了を分けて案内します。

## Atlas の通常手順

1. [README](../../README.md)、[状態](../../status.json)、[固定期待値](../../expected.json)を読む。未実行・未受入を確認済みへ置き換えない。
2. [操作画面](../../index.html)を教材ディレクトリで `python3 -B preview.py --port 0` として開き、予想→三時点→原典/コード→答え→限界を読む。状態記録のGUI/画像確認と、実測の完了を分ける。
3. [reader-data.json](../../reader-data.json)の実行ログを読む。現在はPUBLICATIONが2回計算して、全ての読取りで同じ参照を返した。一方、許容範囲は1〜2であり2を必須にしない。過去の `state=not-executed` / `observation=null` の資料を扱う場合は、契約・予想・原典・コードまでで止まり、測定結果・答えを生成せずbrowserや存在しないログを起動しない。
4. 必要な場合だけ `python3 -B verify.py --run observations/attempt-20261006T143938970174Z/run.json --mutations` で保存結果を照合する。これは Kotlin の再実行と別である。
5. [SOURCES](../../SOURCES.md)と [COVERAGE](../../COVERAGE.md)へ戻り、規則・実装読解・実測のどれに基づく説明か明示する。

## Atlas の範囲外を含む質問

- 「NONE の逐次成功と並行安全性」は、逐次だけを案内し、並行は未検証かつ規則上未規定と分ける。
- 「PUBLICATION は必ず二回か」は否定する。今回の二者の許容範囲は 1〜2 で、公開値は一つ。
- 「lazy と class/property delegation 全般」は [前提一覧](../../references.html)の KR-02 へ戻す。この五条件で一般委譲を確認済みとしない。
- 例外後再試行・再入・他 platform・性能が混ざれば、確認できる五条件だけを明示し、残りは不足として返す。

## Atlas の新しい実験

通常の案内には不要。明示された実験範囲と実行枠を確保し、[契約](../../CONTRACT.md)に従って資源の正式読取り、固定 cache 確認、nice 実値確認を行う。`resources.py` が作った新しい記録を `run.py --execute --resource-record ...` に渡す。未観測を 0 とせず、条件不成立・拒否・timeout は記録して停止する。成功するまで反復しない。

この Skill は文書として用意した案内です。Agent の未知の質問に対する自動案内能力や、正式な人の意味分類を保証しません。有限な手順確認と本番 Agent の実利用評価は別に記録します。

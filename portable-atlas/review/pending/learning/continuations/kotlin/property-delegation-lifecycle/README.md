# Atlas：property 委譲の結び付けと読書き

**同じProviderを使うことと、同じSlotを共有することは別です。** `provideDelegate` の結び付けと `getValue` / `setValue` の呼出しを、2つのインスタンス・3条件・6時点で追います。

[操作画面](index.html) → [前提と公式規則](reference.html) → [実装](src/PropertyLifecycle.kt) → [限定Skill](SKILL.md)。[今回の測定結果](MEASUREMENTS.md) に実行1回の値をまとめました。最新の実行・画面・独立確認は [status.json](status.json) を参照してください。図は参照関係の模型です。

## Atlas の使い方

このディレクトリだけをHTTP配信できます。既存のPythonで `python3 -m http.server 8765 --bind 127.0.0.1 --directory .` を起動し、`http://127.0.0.1:8765/` を開きます。これは利用者が配信するときの例です。HTMLはページ本文、標準配信でダウンロードになるMarkdownは取得したファイルとして読みます。実確認でも本文DOMとダウンロードbyteを区別します。保存結果を見るためにKotlinを再実行する必要はありません。今回の確認はrootが管理する既存のページで行い、作者から新しいブラウザーやサーバーを起動しません。

1. 条件を選び、H2の最後の値とbind/get/set回数を予想します。
2. 保存した実行を読み、構築直後から前後ボタンで比較します。
3. 正常2条件と、言語上は正常終了する共有の設計反例を分けます。
4. 固定原典と完全なコードを読み、最後の時点で答えを開きます。
5. 値の所有先が用途上の独立要件を満たすか判断します。

[実画面の確認範囲](GUI_VERIFICATION.md)には、主要18時点と9画像、実クリックと資料ダウンロードを分けて記録しています。

## Atlas の再現

固定入力は [CONTRACT.md](CONTRACT.md)、[expected.json](expected.json)、[binding-expectations.json](binding-expectations.json)。実行条件は [RUN_CONDITIONS.md](RUN_CONDITIONS.md) です。共有枠・現資源・優先度・時間・所有子の回収を確認し、新しい保存先へ1回実行します。

```sh
python3 -B resources.py --root-slot 'その時点の共有枠・GUI idle・他対象0の確認' --execute-slot --decision ../browser-qa/priority-gaps-2026-10-06/kotlin-runtime-decision.json
python3 -B run.py --execute --resource-record records/resources-日時.json
python3 -B verify.py observations/attempt-日時/run.json --output observations/attempt-日時/verify.json
```

上の日時とdecisionはその実行に対応する保存先へ置き換えます。read-onlyの事前観測では--execute-slotを付けず、実行を許可しません。今回のdecisionを将来の実行へ流用しません。compilerとJDKは既存固定cacheだけを使います。runtimeのKotlinVersionはstdlib版で、compiler自体の固定根拠は配布記録・launcherとcache fileのhashです。実process終了値と、case内部の分類表示を別に照合します。

## Atlas の学べる境界

2回読むとgetValueは2回呼ばれます。providedの2条件は構築時bind2、directはbind0で、読取りの代わりではありません。共有の場合もuniqueなSlotのgetは4回、setは1回。owner表に同じカウンターが2行見えても倍にしません。

`by`だけでは記憶・所有の独立・thread-safeになりません。lazyの初期化/公開と、取得後の可変値や複合操作の安全性も別です。class委譲、並行変更、operator解決全体、他platformを確認済みに広げません。[COVERAGE.md](COVERAGE.md) に既受入との差分と残りを示します。

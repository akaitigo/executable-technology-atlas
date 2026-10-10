# Atlas：WASIで読めない理由を分ける

[index.html](index.html)を開くと、同じ小さなWasmがファイルを読める場合と読めない場合を、保存した実測で比較できます。画面はローカルファイルとして動き、WASIや外部通信を再実行しません。

この教材で分かるのは「資源を渡していない」「操作する権限が足りない」「許可された範囲に名前がない」の違いです。既存のCore Wasm整数演算・memory.grow教材とは別に、WASI preview1の本物の呼出しを扱います。

## 前提と読む順番

ファイルを開いて読む操作を知っていれば始められます。Wasmは実行する小さなプログラム、ホストはそれを動かす側です。ホストが先に開いて渡すディレクトリが **preopen**、資源を参照する番号が **FD**、そのFDで許される操作の組合せが **rights** です。

1. 条件を選び、読める結果または読めない理由を予想します。
2. 「保存した実測を開く」で、呼出し順・返却コード・未到達・後片付けを比べます。
3. 原典と実装へ戻り、ディレクトリの権限とファイルへ引き継げる権限を区別します。
4. 答え合わせを開き、予想を変えたとき前の結果が消えることも確かめます。
5. 欠けた記録や別条件の記録を表示しない確認と、実WASIの拒否結果を区別します。

到達目標は、FD不在と権限不足の区別、許可内の名前欠落の判別、baseとinheritingの読み分け、成功時だけ有効な出力の扱い、EOFと未到達の区別、Node実測を安全な隔離の保証へ広げない判断です。

## 4条件の対照

自分で作った `note.txt` に `Atlas` と改行の6バイトを入れました。第三者のデータや外部パスは使用していません。

| 条件 | 事前FDの照会 | ファイルを開く | 読み出し |
|---|---|---|---|
| ディレクトリを渡さない | BADF 8 | 未到達 | 未到達 |
| 渡して読む | 成功 0 | 成功 0 | 6バイト、その後0バイトのEOF |
| 開く権限を外す | 成功 0 | NOTCAPABLE 76 | 未到達 |
| 許可内の名前がない | 成功 0 | NOENT 44 | 未到達 |

**失敗後の出力FDや読み出し長は使いません。** FDがない条件では最初の照会で停止したため、path_openがBADFを返した実測とは説明しません。成功条件は返されたFDを次のreadとcloseへ渡し、FD番号4を仕様として固定していません。

baseは「このFD自身で許される操作」、inheritingは「開いたFDへ渡せる操作」です。権限減少条件ではbaseからPATH_OPEN（8192）だけを除き、inheritingを保持しました。ファイルを開く要求はFD_READ（2）です。初期ディレクトリの権限全体を読み取り専用の隔離と考えてはいけません。

## 原典・実装・保存した証拠

[実験契約](CONTRACT.md)、[実装前の期待値](hand-oracle.json)、[型と命令の契約](module-contract.json)を実装前に固定しました。[原典との対応](SOURCE-MAP.md)は公式WASI snapshot-01、固定uvwasi 0.0.23、Node 25.2.1に結び付いています。

[610バイトのWasm](module.wasm)には7種類の本物の `wasi_snapshot_preview1` importがあります。[生成器](build-module.cjs)とは別方式の[バイト解析](decode_module.py)と独立レビューで、型・import・export・命令のstack・memory・dataを照合しました。JavaScriptはWasmを読み込んでゲストを呼び、fixtureの本文を直接読みません。ログのargsは教材のWasm exportへ渡す引数で、WASI importの全引数ではありません。例えばpath_openの固定フラグ・要求rights・出力先はWasm内で補い、9引数を渡します。対応はmodule-contract.jsonの命令列で確認できます。

[実行ログ](observations/runtime-20261006T134814277752Z/report.json)は2026-10-06 13:48 UTC、Node 25.2.1 / uvwasi 0.0.23 / preview1の4条件・21呼出しです。全子プロセスは終了コード0、ゲストが開いたFDのcloseと親の子回収・実験用ファイル削除を確認しました。所要0.373673秒はこの実験の時間で、性能比較ではありません。

**優先度変更は失敗しています。** `nice -n 10` を指定しましたが4件のstderrに `setpriority: Operation not permitted` が残り、指定した変更が適用されないまま完了しました。実際の優先度値は未測定です。今後のrunnerは優先度10の設定と実値確認に失敗するとNodeを始めません。[実測時ソース](observations/executed-source/manifest.json)と[実測後の変更](observations/post-execution-update.json)を分離しており、変更後の実WASIは再実行していません。

準備中の生成器の名称衝突と、旧原典URLの404も保存しました。生成準備の修正と実WASIの再試行は別で、実WASIはattempt 1 / retry 0です。時間制限と回収の境界は[追補](CONTRACT-ADDENDUM.md)を参照してください。

## 保存結果だけを確認する

このディレクトリで次を実行します。WASIやブラウザーを起動せず、保存結果を照合します。

```sh
python3 verify.py --run observations/runtime-20261006T134814277752Z
node check-reader.cjs
python3 check-priority-guard.py
```

検査は4条件、保存結果の改変8種類、Wasmバイトの改変4種類、readerの有限69確認を含みます。優先度guardの4条件は代用関数による確認で、実際の優先度変更や子起動を含みません。実測の再実行には `run.py --record` が必要ですが、通常の学習や保存結果の確認には不要です。

画面は33確認・42回のポインター操作・キー操作1回・7画像の作者目視まで完了しました。撮影後の説明文1箇所の明確化は撮影版と分離しています。[画面確認の範囲](GUI-QA.md)、[学び直す手順](SKILL.md)、[対応済みと残る内容](COVERAGE.md)も参照できます。

## 限界と次の判断

Nodeの[公式Security説明](https://nodejs.org/download/release/v25.2.1/docs/api/wasi.html#security)は、安全なファイルシステム隔離を保証しません。この教材を、信頼できないWasmを安全に隔離できる根拠には使いません。Core Wasmの動作成功もWASIの成功とは別です。

clock、network、Component、他ランタイム、外部パスやシンボリックリンク、第三者データ、性能は未検証です。次に確かめる対象は「開いたファイル自身からFD_READを外した後のread」です。今回はディレクトリのPATH_OPENだけを変更したので、その結果をファイル自身のrights変更へ流用しません。

---
name: atlas-wasi-preopen-rights
description: Atlasの固定Node/uvwasiによる4条件の保存WASI実測を読み、FD不在・権限不足・名前欠落を区別する。
---

# Atlas：WASIの読めない理由を確かめる

対象はこのディレクトリの保存した実測readerです。新規インストールや実行環境変更は必要ありません。一般的なWASI sandbox構築、clock/network、Component、他runtimeの保証には使いません。

1. READMEでNode 25.2.1 / uvwasi 0.0.23 / preview1という前提を確認する。
2. index.htmlで条件と予想を選び、呼出しを表示する。
3. `fd_prestat_get`、`path_open`、`fd_read`の到達状況を順に読み、返却コードと出力値を区別する。失敗時の出力を成功値として使わない。
4. rights変更時はbaseのPATH_OPENだけを除いたか、inheritingを保持したかを確認する。
5. SOURCE-MAP.mdと固定原典に戻り、答え合わせを行う。予想や条件変更後は古い結果を消す。
6. 必要ならREADMEのread-only検査を使う。実測時ソースはobservations/executed-source、今後のrunner変更はobservations/post-execution-update.jsonで分離する。

## 依頼を受けたときの3つの確認例

- 「ファイルが読めない。preopenなしと欠落は同じ？」：no-preopenはBADF 8で停止しpath_open未到達。missing-fileは照会成功後にNOENT 44。両条件の保存記録を比較する。
- 「権限を減らすとどうなる？」：rights-reducedでbaseから8192だけを除きinheritingが不変であること、path_openがNOTCAPABLE 76でread未到達であることを示す。ファイル自身のFD_READ減少は未観測と答える。
- 「このNode設定で信頼できないWasmを安全に隔離したい」：この実測を安全保証に使わない。Node固定版のSecurity説明へ戻り、用途が教材の範囲外だと説明する。外部パス探索や設定変更を試さない。

## 記録の使い分け

保存実測は4条件/21呼出し。全子終了とfixture削除を確認済みです。`nice -n 10` は拒否され実優先度値は未測定であり、低優先度で実行済みとは説明しません。今後のguardは設定・実値確認失敗でNode起動前に止めますが、実WASIを再実行して確認した変更ではありません。

GUI-QA.mdの画面確認範囲と、COVERAGE.mdの未確認を一緒に示します。記録の欠落・改変・別条件を画面が拒否することを、WASIの権限拒否と混同しません。画像の生成や模型だけを実画面・実WASIの証拠にしません。

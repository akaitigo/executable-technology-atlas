# Atlas｜DAGと容量の保存結果を読む

## 画面を開く

このディレクトリで既存Pythonを使い、次を実行します。外部アクセスや追加インストールは不要です。

```sh
python3 -B serve.py --port 18777
```

`http://127.0.0.1:18777/` を開きます。portが使用中なら他のサービスを止めず `--port` を別の空き番号に変更します。終了は自分が起動したターミナルでCtrl-Cです。このサーバーは固定allowlistの保存資料を読むだけで、計算やworkerを起動しません。Markdownは `text/plain; charset=utf-8` として配信します。

前提3本文は既存ローカル資料への固定参照です。元ファイルが移動・変更された場合は読込やhash照合を止めます。元資料の説明は[対応表](SOURCES.md)、閲覧入口は[README](README.md)にあります。資料のHTTP外のfileリンクを、画面から実際に辿れた証拠にはしません。

## 保存計算と照合

[入力](cases.json)と[手予定表](expected.json)は実装前に固定しました。`scheduler.py` はgraphlibと終了eventを使い、`verify.py` はproducerをimportせず手区間・整数tickの占有と照合します。4条件のevent境界18時点と、区間に含まれる整数26時点は異なる観測単位です。



保存後の結果は `observations/run-01/results.json`、7入力の実行時版は同じrunの `inputs/`、標準ライブラリgraphlibはimport先とSHA256だけを記録します。必要な保存値の再照合は次の既存スクリプトで行えます。

```sh
python3 -B verify.py
```

再照合は保存済みのJSONを読むだけで、schedulerを再実行しません。手予定表とcheckerは全入力や全schedulerの正しさを保証しません。

## 実画面の確認

2026-10-06 21:04:21–24 UTC、保存結果readerを既存の一つのheadless Chromiumブラウザー/ページで確認しました。実行環境側が教材用loopbackサーバーを1個起動し（PID95865、port60848、実nice10）、ブラウザーとページは再利用しました。検査module自身のbrowser/context/page/server起動は0です。サーバーとブラウザーは継続利用のため維持し、検査moduleのroute/listenerは除去、viewportは復元しました。

18境界の実DOM/SVG座標と6拒否、19切替状態、5つの取得失敗/古い応答、3前提本文と6Markdown本文を確認しました。本文リンクは表示内の座標を確認して実クリックし、同じページで本文に到達しています。外部公式本文は今回のGUIでは開かず、先に確認したlocatorを維持しました。

112回の実ポインターと1回の横wheel、57回のselectOption API、11回の同page移動APIを分けて記録しました。1280×900と390×844の実viewport画像8枚を保存し、狭幅の表は横位置0→390へ操作しています。readerの実操作であり、仮想計算や実workerの再実行ではありません。記録への参照は[確認状態](qa/reader-acceptance.json)にあります。

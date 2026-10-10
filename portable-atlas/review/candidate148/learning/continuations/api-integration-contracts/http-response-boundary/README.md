# Atlas：JSONは閉じている。でも、HTTP本文は届き切ったか

[元APIの通信と契約](related.html?topic=api-readme) → [本文長と上限](related.html?topic=budget-readme) → [Problem Detailsの意味](related.html?topic=problem-readme) → [今回の画面](index.html) → [Skill](SKILL.md)の順で読む。

宣言は106byte、届いたのは105byte。それでも、その105byteだけでJSONが完成し、読取APIが例外を出さなかったら、応答を使ってよいだろうか。今回はこの問いを、完全な105byteと8192/8193byteの上限対照と並べる。HTTPの本文が完全であること、利用側の上限に収まること、JSONを解釈できることを分ける。

条件と予想を選び、保存した受信を表示する。宣言長・受信長・読取例外、検査の到達段階を見比べる。例外だけを根拠にした誤った判断を確認し、原典と実装へ戻ってから答え合わせする。画面は保存記録を読むもので、操作ごとにHTTP実験を起動しない。図はbyte数の説明で、ネットワークのパケット画像ではない。

このディレクトリで次のコマンドを使うと保存資料を配信する。

```sh
python3 -B serve.py --port 18785
```

入口は `http://127.0.0.1:18785/`。使用中なら他サービスを止めず、別portか `--port 0` を使う。この資料サーバーと、実験用の一時的なHTTPサーバーは別である。実験の実行条件は[REPRODUCE](REPRODUCE.md)へ。

2026-10-07 04:41:59 UTC、Python 3.9.6で実HTTPの4応答を受信した。宣言106・受信105の条件ではread例外なしでも未完了と判定し、JSONを渡さなかった。8192は通過し、8193は完全受信後に上限で拒否した。[確認状態](qa/reader-acceptance.json)、[契約](CONTRACT.md)、[実装前の期待](expected.json)、[入力](cases.json)、[原典](SOURCES.md)、[今回の範囲](COVERAGE.md)を分けて読む。受入済み教材や共有計画は変更していない。

[保存した受信結果](observations/run-01/results.json)、[実行記録](verification/execution.json)、[保存値の検査](verification/saved-result-check.json)を確認できる。初回1子はnice10・0.1872秒・exit0で回収済み。所有したサーバー、接続、threadは終了した。作者の保存検査418関係と10改変拒否は有限確認であり、HTTP全体の保証ではない。保存記録readerの実画面確認も完了した。4応答・表示消去/取得失敗・古い応答・資料導線を、同じheadlessページで確認し、1280/390pxの実画面9枚を保存した。最終独立受入の状態は確認状態へ。

狭い画面の図と表は横へスクロールする。右端では左側の見出しや条件名が画面外になるため、左右を行き来して照合する。図の左右移動0→360→0、表0→500→0を確認した。

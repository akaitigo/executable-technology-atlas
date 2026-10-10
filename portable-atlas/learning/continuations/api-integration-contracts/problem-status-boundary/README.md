# Atlas：本文のstatusで、HTTP状態を置き換えてよいか

読む順は[既存APIの通信・契約](related.html?topic=api-readme) → [固定契約](related.html?topic=api-contract) → [今回の画面](index.html) → [実装](consumer.py) → [Skill](SKILL.md)。既存の[再送と業務ledger](related.html?topic=retry)は別の問いとして参照する。

HTTP状態の入力は422のままなのに、本文のstatusだけ200だったらどう判断するか。6つの固定応答で、独自エラーとProblem Details、本文statusの省略・型違い・矛盾を比較する。これは保存した合成応答に対するconsumer関数の実行であり、実HTTP受信の測定ではない。画面も保存結果を読むもので、操作のたびにAPIや計算を起動しない。

まず条件と予想を選び、保存結果を表示する。伝送状態の入力、本文memberの扱い、判断の候補として残すstatus、判断結果を分けて読む。保留する版と本文を優先する版を対照し、同じtypeのタイトルを翻訳しても別の問題にならないことを確認する。最後に原典・実装を開いて答え合わせをする。

不一致を保留するのは今回の利用側の方針。RFC 9457では本文statusはadvisoryで、型違いmemberや未知extensionの無視などを定めるが、受信した矛盾をすべて同じ方法で処理する義務は定めていない。生成者とintermediaryのどちらが原因か、この固定応答からは分からない。

```sh
python3 -B serve.py --port 18784
```

表示は `http://127.0.0.1:18784/`。使用中なら他サービスを止めず別port、または`--port 0`で表示されたportを使う。配信は保存資料の読取だけで、外部APIを呼ばない。対象計算と画面の確認手順は[REPRODUCE](REPRODUCE.md)へ。

6条件×2方針の[計算結果](observations/run-01/results.json)を保存した。作者の236照合・保存値8改変の検出と、独立担当の243照合・6改変の検出が通過した。これらは重複を含むため合算しない。画面でも全12応答、条件・予想変更後の消去、取得失敗と回復を確認し、1280pxと390pxの実画面10枚を保存した。狭い画面では図と表を横へ動かして読む。

[実行ログ](verification/execution.json)、[確認状態](qa/reader-acceptance.json)、[契約](CONTRACT.md)、[手期待](expected.json)、[原典対応](SOURCES.md)、[残る範囲](COVERAGE.md)から根拠と受入結果へ辿れる。公式原典は制作時に本文を読み、GUIではリンク先の要求をローカルで遮断して導線だけを確認した。実HTTP受信の測定や旧教材への統合・公開は行っていない。

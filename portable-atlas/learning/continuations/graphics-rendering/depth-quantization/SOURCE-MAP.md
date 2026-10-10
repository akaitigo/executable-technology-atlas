# Atlas — 根拠と独自規約の対応

- 目標91：[97分野の目標](../../../../2026-10-06/task-8/atlas-97-field-goals-ja.md)の1055–1064行。元学習経路69行のdepth量子化案を有限化します。
- [Microsoft Depth Buffers (Direct3D 9)](https://learn.microsoft.com/en-us/windows/win32/direct3d9/depth-buffers)：保存した奥行きとの比較、最大値への初期化、比較関数を変更できること、精度と投影分布の限界を読む入口です。2026年10月7日に公式本文を読みました。ページの更新表示は2021-01-06です。authorization案内も表示されましたが参照する本文は取得できました。
- strict LESSとclear=1/maxはこの教材で選ぶ比較条件です。`floor((2^b−1)*z+1/2)` は元学習経路に提案された教材独自の式で、上記公式本文が定めたGPU丸め規約ではありません。実Direct3Dやdriverを実行しません。
- [Python fractions](https://docs.python.org/3/library/fractions.html)を使う予定ですが、この契約段階では追加取得せず既存環境の標準ライブラリを再利用します。模型の商余りと独立のbin所属を別計算にします。

174件の最新学習経路と受入範囲から既存の透視補間・clipを差し引きました。本文を読んだ範囲の比較であり、全PCに類似内容が存在しないとの宣言ではありません。原典本文のbytesは保存していないため、sources.jsonのsource_byte_sha256はnullです。localファイルのhashをremote本文の固定hashとは扱いません。

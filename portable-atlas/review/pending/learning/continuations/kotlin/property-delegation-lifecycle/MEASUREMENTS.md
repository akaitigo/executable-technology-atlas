# Atlas：保存した実行から分かること

2026-10-06 21:03:29 UTC開始の [実行ログ](observations/attempt-20261006T210329390422Z/run.json) は、コンパイル1回・JVM1回、約3.700秒で終了した。両方exit0、実nice10、所有する子は回収済み。実行開始前の資源読取がsandboxで不完全だった記録も保持し、対象実行の失敗と混ぜていない。

|条件|構築後bind|読む値の順|unique Slot|get / set合計|用途の独立要件|
|---|---:|---|---:|---|---|
|direct-fresh|0|A, A, X, A|2|4 / 1|満たす|
|provided-fresh|2|A, A, X, A|2|4 / 1|満たす|
|provided-shared|2|A, A, X, X|1|4 / 1|満たさない|

providedの両条件でProviderの実`===`はtrue。しかしSlotの実`===`はfreshでfalse、sharedでtrueだった。bindへ渡るownerは構築後のH1/H2と実参照で一致し、各アクセスのthisRefはH1の4操作、H2の1操作に一致した。property名はlabel。ID文字列だけから同一性を推測した結果ではない。

共有の条件は言語上有効で正常終了している。「H1への代入がH2に影響しない」という設計上の要求への反例として読む。共有Slotのカウンターを二つのowner行へ表示しても、実体は一つなので倍に合計しない。

[完全stdout](observations/attempt-20261006T210329390422Z/runtime.stdout.txt) と [固定期待との照合](observations/attempt-20261006T210329390422Z/verify.json) を保存した。作者検査は170項目、改変8件を拒否。独立担当は実装前の別の手表で242項目を照合した。有限の検査件数はKotlinの全規則や未知質問への保証を表さない。

この実行はmain threadだけ。並行mutation、lazy取得後の可変payload、class委譲、任意operatorの解決、他platform、性能は測っていない。画面・画像・最終独立受入の現在状態は [status.json](status.json) を参照する。

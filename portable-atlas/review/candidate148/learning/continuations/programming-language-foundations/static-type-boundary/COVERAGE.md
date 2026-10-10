# Atlas：型判断の増分と学習順

目標07と元言語基礎READMEの次実験3へ対応する。束縛→捕獲回避置換→小ステップ→今回のInt/arrow型判断の順に読む。最新171受入では前2不足は既に解消している。元の古い未実施一覧を全て現状と扱わない。

- 既存Closure Paths：環境/closure/実行時not-callable・addition-type。静的型checkerは未実装と明記。
- capture-avoiding-substitution：18条件の置換・環境比較。今回は前提であり再制作なし。
- language-small-step-boundary：value/stuck/budgetの5対照。型checker/progress/preservationは未実施。比較sourceを固定コピーする。
- compiler-ast-stack/static-name-resolution：命令変換または名前の宣言解決であり、Γから関数本体を型付けする今回の判断と異なる。
- typed-tool-result-dataflow：read結果fieldを実型検査してdispatchを拒否する。言語の型規則木や未呼出関数の本体検査ではない。
- 今回：5つの閉項のΓ/規則/型・拒否位置と、通常評価0/別診断の違いを固定手表へ照合する。

未対応は型安全性の証明、注釈なし推論、多相/部分型/効果/store/再帰/モジュール、一般言語の完全性。Arrow引数の不一致、shadow等の実装枝をこの5条件で観測済みとしない。次の問いは進行・保存を規則から証明すること、または型環境と可変storeの関係である。元owner不明・未統合、作者加算0。教材単体HTTP外の前提は場所の出所として示し、画面内で開けたとは扱わない。

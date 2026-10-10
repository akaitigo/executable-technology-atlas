# Atlas｜原典と今回の実装

- [MIT 6.006 Lecture 03](https://ocw.mit.edu/courses/6-006-introduction-to-algorithms-fall-2011/resources/mit6_006f11_lec03/)／[講義PDF](https://ocw.mit.edu/courses/6-006-introduction-to-algorithms-fall-2011/90a37c49b07b105ea7a027abc67eddc6_MIT6_006F11_lec03.pdf)：PDFページ4（0始まり）挿入の処理済み部分、16の比較とshift費用、17の再帰分割とmerge。2026-10-06に公式配布本文を読取り。講義のswapと今回の配置回数は違う。画像やコードの転載はしない。
- [Python公式 Sorting HOWTO / Sort Stability and Complex Sorts](https://docs.python.org/3/howto/sorting.html#sort-stability-and-complex-sorts)：同じkeyの元順を保つ安定性と複数段階の整列。2026-10-06に公式本文を確認。Python組込みsortの実装・速度を測る教材ではない。
- [既存lower-bound](related.html?topic=lower-bound)：候補区間・空列・重複と整列済みの前提。元README21–29行をそのまま読める参照入口を用意する。
- [元学習経路](related.html?topic=learning-path)：35・45行の安定整列と検索準備費用に対応。hash/BFSは既存の追加教材で受入済みであり、古い「未実装」の一括記載を現在の状態へ読み替えない。

今回の入力上限・計数・拒否は[有限契約](CONTRACT.md)で定義する。公式本文は分野の規則を読む根拠であり、この独自実装の正しさや全入力保証の証明ではない。

# Atlas：小ステップ教材の増分と残る問い

目標07の次の一歩と、元programming-language-foundations README実験2/COVERAGEのsmall-step不足へ対応する。[出所](sources.json)に正式文書の位置・hashを残す。直下LEARNING_PATH.mdがないことを、学習経路がないという意味にはしない。

| 既存の範囲 | 今回の扱い |
|---|---|
| Closure Pathsの13条件、環境・束縛・capture・error・64 node-enter予算 | 比較用の旧評価器を固定コピー。元観測を新しく数えない |
| capture-avoiding-substitutionの18条件、open項のalpha rename・独立環境評価 | 前提。一般置換の再制作なし |
| compiler-ast-stackの5正常/7拒否、命令ごとのstack列 | 前提。AST変換・VMの新作ではない |
| 型checker、progress/preservation | 元経路の未対応。今回も未実施 |
| 項before/afterと規則/場所、value・stuck・budgetの5対照 | 今回の有限な増分。初回保存計算を手期待へ照合。実画面と受入は状態記録参照 |

値0を失敗と混ぜず、規則が適用できない項と予算で止めた還元可能な項を分ける。big-stepの観測event数と規則適用数は違い、予算不足の途中項とbig-step最終値を矛盾扱いしない。

一般small-step/big-step等価性、決定性の証明、全入力の停止性、無限実行、型安全性、open項、Let/store、効果・例外・並行性は対象外。次の問いは型規則とprogress/preservation、環境/継続を状態にする機械、代入によるコード増大の扱い。5条件で分野全体を完了としない。

元owner不明・元repo未統合、作者加算0。契約・手期待・保存結果・実画面・独立受入を別状態で扱い、制作開始だけで受入trueにしない。

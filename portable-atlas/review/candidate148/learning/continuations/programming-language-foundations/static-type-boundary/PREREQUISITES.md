# Atlas：この教材までの読む順

1. ASTの左右・子と再帰、辞書、変数と関数を確認する。
2. 元Closure Pathsで名前→値の環境と関数の束縛を読む。
3. 捕獲回避置換でbinder内の名前の扱い、小ステップ教材でFn valueとstuckを区別する。
4. 本教材ではΓを名前→型へ切り替え、未呼出関数の本体も型検査する。

必要な前提sourceは [固定評価器](inputs/prerequisite-small-step.py) と [出所・hash](sources.json) へ戻れる。外部workspaceにある既存教材の場所はsources.jsonのlocal_materialsに明記する。教材単体のHTTP配信でworkspace外へ移動できるという意味ではない。

# Atlas：小ステップへ進む前提

まず構文木のInt/Var/Fn/Call/Add、値渡し、自由な変数と束縛、関数の定義時環境を読めることを前提とする。元入口のcapture10/20とcaller-parent対照は既受入である。[固定した旧評価器](inputs/prerequisite-interpreter.py)と[出所](sources.json)から、その評価順へ戻れる。

次にcapture-avoiding-substitutionの中心例、自由変数、同名binderでの停止、closed値とopen値の違いを読む。原資料の場所はsources.jsonにあり、今回の単体HTTPの外にある。今回のbetaはclosed値だけを代入し、一般alpha renameや置換補題を作り直さない。

compiler-ast-stackは構文木の左→右後順から命令列へ進む既教材である。そこでの命令番号やstack前後と、ここでの項全体before/after・一歩規則を区別する。

旧入口の型検査やprogress/preservationは未対応と記載されている。integer callのruntime guardや入力shape検査を静的型検査と呼ばない。今回も型体系の証明は追加しない。全workspaceに型の例が存在しないという調査結果ではなく、この前提経路と受入範囲を照合した限界である。

読む順は [契約](CONTRACT.md) → [手で追った5条件](HAND_TRACE.md) → [原典と実装](SOURCES.md)。実装・保存値・画面・Skillの現状は状態記録へ分けて示す。

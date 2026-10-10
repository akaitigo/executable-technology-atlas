---
name: atlas-language-small-step-boundary
description: Atlas の固定5条件で、項の一歩規則と再帰評価のログ、値・行き詰まり・予算切れを保存資料から区別する。
---

# Atlas：小ステップの限定案内

最初に [状態](status.json)を読み、実行・画面・独立確認を分ける。完了した実行ログがないときは[契約](CONTRACT.md)・[手期待](HAND_TRACE.md)・[原典対応](reference.html)・コードまで案内し、期待を観測値にしない。通常利用で計算・browser・serverを自動起動しない。新しい実行は[実行条件](RUN_CONDITIONS.md)、配信は[README](README.md)に従う。

[前提](PREREQUISITES.md)でAST、値渡し、束縛、closed値を確認する。画面を利用できる場合は条件→理由付き予想→保存値→前後の項/規則/位置→旧ログ→答えの順とする。画面が利用できない場合も `bundle.json` の `run_text` が指す保存値と[期待](expected.json)を別々に読める。

1. 「0、予算0は失敗か」ならzero-value。規則0歩とvalue0を照合する。図の初期項には適用矢印がない。
2. 「ログ18行なら18歩か」ならarithmetic-complete。同じ入力の3規則、旧18event、7node-enterを別の単位として読む。先に期待、測定後は実行ログで確かめる。
3. 「予算2で止まるのは無限実行か」ならarithmetic-budget。残項3+7、未適用AddInts、旧評価器の10を照合する。停止予算の違いから非停止を断定しない。
4. 「引数と関数本体のどちらが先か」ならapplication-value。CallArg→Beta→AddIntsと `$.arg` の位置、閉じた値5の代入を[実装](small_step.py)へ戻って読む。一般open置換の証明は前提の既教材へ案内する。
5. 「0(1+2)は形式違反か」ならnot-callable-stuck。有効ASTだが規則なし、引数未還元を確認する。SFのST_App2とAtlasのFn限定CallArgの差は[原典対応](reference.html)を読む。
6. 「型安全性や任意入力の等価性も示したか」には[範囲](COVERAGE.md)を案内する。固定5条件と有限観測であり、CallFnの実遷移、最終Fn値、一般progress/preservationは未検証と答える。

このSkillの文書読取確認と、未知質問への一般Agent評価は別である。測定値・図の説明・未実施を混ぜず、資料取得失敗を言語のstuckへ読み替えない。

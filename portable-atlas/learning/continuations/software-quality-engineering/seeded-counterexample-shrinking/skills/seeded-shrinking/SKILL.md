---
name: seeded-shrinking
description: 有限整数の固定seed生成、M1/M2反例、失敗保持shrinkingとglobal最小判定を本moduleで再現・読解する。
---

# 固定seedと縮小の読み方

このmoduleのREADME、hand-oracle.json、COVERAGE.mdを読み、generator/seed/count/variantのexact契約を守る。通常の検証はmodule内で `python3 -B verify.py` と `python3 -B route.py`。保存原票・receiptへ再記録しない。

予想→入力操作→生成全件→最初失敗→候補受理拒否→局所最終→独立252列挙→答えの順に読む。生成で反例がない場合はshrinkingなしとし、全列挙で見つかった反例を生成の成果へ付け替えない。局所停止とglobal最小を分け、rankと252領域の範囲を説明する。

fast-checkは未導入・未実行。独自有限模型と説明する。品質全体・全Subject完成・library replayの保証を求められたらCOVERAGEの未対応を示す。Core/globalや他教材、設定、registryへ変更を広げない。install・公開・commit/pushはこのSkillの範囲外。

UI検証では入力/予想変更後に答え・raw・table・図を消し、旧応答を無視することを確認する。保存記録の実測と原典の説明を分け、所有listener/tabのみ片付ける。

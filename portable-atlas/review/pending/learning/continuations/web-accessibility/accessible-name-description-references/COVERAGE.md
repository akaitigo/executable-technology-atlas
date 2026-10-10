# 有限範囲

固定12条件：visible text、aria-label優先、有効labelledby優先、describedby、直接参照hidden label/description、参照なしhidden子、可視参照先hidden子、hidden参照先hidden子、IDREF順、無効参照fallback、名前空だが操作可能。予想を保持して答えへ表示する。

対象はnative buttonひとつ、span/p、hidden/aria-hidden、短い日本語。循環、自己参照、aria-description/title、空有効参照、重複IDREF、CSS生成内容、embedded control、shadow/slotは未教材。全descriptionはUNOBSERVEDで残る。real ATと全WCAG適合は未評価。

能力probe→固定期待表→native AX/role query＋DOM別採取→実click→保存比較UI→独立literal照合→負例→read-only検証→所有リソース終了。読み取り参照以外の既存pathは変更しない。

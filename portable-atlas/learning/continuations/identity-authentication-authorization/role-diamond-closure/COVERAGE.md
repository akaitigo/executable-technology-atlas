# Atlas：目標76の菱形継承を確かめる

目標文書 `2026-10-06/task-8/atlas-97-field-goals-ja.md:886–895` は独立到達集合による権限・重複・cycle拒否の照合を求めます。元分野LEARNING_PATH §6実験2と、resource-scope-enforcement READMEの次coverage1がこの不足です。最新183受入を基準とし、旧未実行文だけでなく既存の保存範囲も読みました。

元README/modelはeditor→viewer、scope越境、新policyへのgrant削除を扱い、visitingとorderedを既に分けています。resource-scopeは信頼resource属性への結合とdeny時read0を扱います。今回は一般cycle検出やscope/認証を再制作せず、4role菱形の共有祖先、直接∩継承、付与元role集合、visited誤拒否を有限手表へ照合します。

前提は集合、graph到達、DFSの現在経路と処理済み集合、subject/action/scopeの区別です。認証とscope完全一致は仮定。全RBAC・製品適合・職務分離・session・失効・OAuthは残ります。共有owner取得不能の扱いを変えず、共有元/完成183/台帳はread-only、未統合/作者加算0を維持します。現在の実施状態はstatus.jsonへ。

---
name: atlas-algorithms-data-structures
description: このローカル教材で、数値列の二分探索の範囲不変条件、境界誤り、停止性、線形探索との比較数を説明・再現する。Graph、DP、tree等の実装教材は未対応。
---

## 入口

操作と図は [index.html](../../index.html)、実装は [search.js](../../search.js)、再現手順・制限は [README.md](../../README.md)。質問に関係する箇所だけ読む。

正常はlower boundを求め、重複なら最初の一致を返す。反復indexの区間は `[lo, hi)`、挿入位置pの候補は `lo ≤ p ≤ hi`。候補indexに目標値を必ず残す別方式と混ぜない。正答の不変条件と、範囲長の減少による停止性を別々に説明する。

## 再現と引用

実観測を求められたら、module directoryで既存 [verify.mjs](../../verify.mjs) を `node verify.mjs observations/<新しいrun名>` と実行する。結果はそのdirectoryのruntime.json。過去の観測は [node-20261005-attempt-03/runtime.json](../../observations/node-20261005-attempt-03/runtime.json)。引用するときは入力・実装version・実行環境・比較数の定義を添え、現在のSource digestと一致するか確認する。

図の「一段進める」は実行済みJS状態列の説明用再生で、実行時間ではない。Browser画面を確認する場合は既存 [serve.mjs](../../serve.mjs) のlocalhostプレビューを使える。共有Browser設定やprofileを変更する必要はない。

## 限定用途

- 整列済数値列／空列／重複の探索：正常例を使う。
- off-by-one：UIの「候補を失う」。無限ループの理由：「縮まらない」。診断器が非進捗で止めるため、放置した無限実行の証拠とはしない。
- 未整列列：正常実装は拒否。「強行」は意図的な反例。線形探索は別に実行できる。
- 比較数：前提確認・探索の<比較・一致確認を区別する。診断や図描画を除いた値比較数であり、実時間の性能と同一視しない。

入力は32件以内、整数-999〜999、固定比較。Graph／DP／treeや汎用データ構造を要求されたら、この教材では未対応と明示し、[残る領域](../../scope.json)を案内する。新実装や別分野への拡張をこのSkillの対応済み能力として主張しない。外部公開・global installはこの入口の機能に含まれない。

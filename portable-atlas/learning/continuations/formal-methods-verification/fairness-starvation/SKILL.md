---
name: atlas-finite-fairness
description: Atlas の固定6列で公平性の対象とP1の進行を保存計算から読み分ける。
---

# Atlas：公平性の対象を先に読む

1. [status.json](status.json) を読み、保存計算の完了・未起動・失敗とGUI確認範囲を区別する。`observation` がnullなら契約/期待/原典/コードまでで止める。画面確認が保留なら保存JSONを読む。ブラウザーや対象計算を自動起動しない。
2. [CONTRACT](CONTRACT.md) で状態、原子的な動作、stutterを確認する。前提は [元モデルのcopy](inputs/prerequisite-model.py)。[SOURCES](SOURCES.md) で著者原典と独自の対象の違いを読む。
3. 要求を `Next0/Next1` の弱公平性か、`Enter1` の強公平性か、その組合せかへ分ける。対象が不明なら範囲を明示する。実OSや全公平列の保証へは案内しない。
4. [画面](index.html) または保存runの選択ケースで、予想→prefix/cycleの辺→enabled/executed→原典/実装→答えを辿る。公平性はcycleだけで判断し、stutterを進行に数えない。
5. 「有効な列」「同時入室しない安全性」「この列が公平か」「P1の各要求に応答するか」を分ける。以前の入室を後の要求へ流用しない。
6. 手書き期待と保存値の一致、入力hash、有限範囲、未確認条件を示して答える。再計算が必要な別目的なら [RUN_CONDITIONS](RUN_CONDITIONS.md) を先に確認し、新しい実行ログへ分ける。通常の保存資料の案内では実行しない。

Atlas のC停滞では、Enter1は常時無効なのでSFだけを満たす一方、P0.releaseは有効です。A→B→Cでは機会が断続的なためWF両processとSF入室1で答えが変わります。過去にP1が進んだ列にも、その後の要求の飢餓があり得ます。

このSkillは固定資料への限定した読む順です。文書の配置、別担当が数問を辿る確認、未知質問への一般Agent評価を区別します。全公平cycleの定理や実schedulerの保証が必要なら、今回の証拠では不足と明記してください。

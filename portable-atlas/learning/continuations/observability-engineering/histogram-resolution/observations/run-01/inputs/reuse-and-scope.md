# Atlas — 180件を前提にした今回の増分



読む順は [計装の基礎](related.html?doc=base) → [欠落・遅着と条件付き分位点](related.html?doc=collector) → [今回の契約](CONTRACT.md) → [画面](index.html) → [限定Skill](SKILL.md) です。

既存 collector の model.py:9–12 stats は seen の p50/p95 を nearest-rank で計算し、README:24 は補間なしと明記しています。今回は欠落や到着の条件を変更しません。全件既知の小さい列を区間件数へ圧縮する段階を追加し、情報として残る区間と仮定に基づく推定値を比較します。既存の nearest-rank と空集合 null は再利用であり、新しい成果として加算しません。

最新 LEARNING_ROUTES.md:529 と atlas-independent-acceptance-reconciliation.json の180件基準を読取り、collector-missing-late-quantiles を既受入として差し引きました。原READMEの古い未実施表記全体を未教材と読み替えていません。既存の描画補間は幾何の問いであり、今回の分布集約とは分けます。作者は件数を加算せず、共有統合の担当状態も推測しません。

新しく判断できる問いは「p50が10msと表示されても10msの観測があったと言えるか」「同じ件数の棒グラフなら元の分位点も同じか」「区切りを細かくすると失った分布そのものが戻るか」です。実運用への答えは、必要な区間幅・保存する情報・使った推定規則を確認することまでです。実サービスの最適設計やSLO達成を証明しません。

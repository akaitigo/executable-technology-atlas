> 配布用保存reader：端末・実行管理情報を除いた観測データを、専用のschemaとSHAで照合して再生します。元原票のSHAと区別しています。新しい計算・GUI検証ではありません。[データの由来と復元](MIGRATION.md)を確認してください。

# Atlas：陽性 ID 集合から ROC / PR へ

閾値を下げると、陽性と判断される ID が増えます。その追加を混同行列へ戻し、ROC と PR の座標を読み分ける教材です。元の合成20件を完全一致コピーし、全 score 境界と全陰性端点の21状態を扱います。同 score を一緒に判定する規則は、別の3件・3状態で確かめます。

**固定24状態の計算と保存値の独立照合、同じ24状態の画面操作検査を行いました。** 現在の状態と別担当の確認結果は [status.json](status.json) に分けて残します。

## Atlas の読む順

1. [元20件](inputs/predictions.json) の label と score を分けて読む。正解が陽性なのは p01 と p02 だけで、score は人が作った数値です。
2. [契約](CONTRACT.md) の `score >= threshold` で、境界0.40と0.35の陽性 ID を予想する。0.50の同点対照は [別入力](inputs/tie.json) で読む。
3. [手計算](HAND_TRACE.md) と [全24状態の固定期待](expected.json) へ戻り、ID集合→TP/FP/FN/TN→分子/分母→座標を追う。これは実装前の予想で、実測ではありません。
4. [公式規則と今回の選択](SOURCES.md) → [閾値列挙コード](threshold_sweep.py) → [記録を保存するコード](producer.py) の順で対応を見る。
5. Precision が必ず単調に減るわけではないこと、同点の片方だけを閾値で選べないこと、未定義の PR 点を作らないことを答え合わせし、[未対応範囲](COVERAGE.md) を読む。

到達目標は、全 unique score 境界と陽性 ID の包含関係を説明すること、同点が一括で入る理由を述べること、ROC と PR の軸・分母を区別すること、分母0の未定義を保持すること、合成計算とモデル評価を区別すること、用途の損失を知らず最適閾値を断定しないことです。

## Atlas の保存結果を読む画面

[index.html](index.html) は予想→閾値の前後操作→ID集合・割合・曲線→原典/コード→答え→限界の入口です。現在までの点だけを描き、未定義の PR 点は省略して文章で示す設計です。点を結ぶ線は読む順の案内で、中間座標の実現可能性や AUC を意味しません。

画面は `data.js` に保存記録の正確なテキストを同梱し、通信や再計算をしない構成です。今回確認した入口は、同じディレクトリをHTTPで配信した `index.html` です。単一の既存ブラウザー内で1280/390の表示と操作を確認しました。`file:` の直接表示は未確認です。配信入口がない場合もテキストとJSONを読めます。[画面確認の記録と範囲](GUI_VERIFICATION.md)を参照してください。

予想は自由記述で自動採点しません。予想・条件・リセットで結果と答えを消し、古い非同期の照合結果を新しい条件へ残さない設計です。資料の欠落・改変は資料の読込み失敗であり、Precision の未定義や結果の0とは別です。

## Atlas の保存した実測

2026-10-06 18:31:01 UTC に、既存 Python 3.9.6 / macOS arm64 で対象計算を1回実行しました。元21状態と同点対照3状態、環境・入力情報・完了を含む28行を保存しています。約0.120秒、exit 0、対象再試行0、nice 実値10、CPU2秒・経過3秒の上限、終了後に自己所有子を回収し group 不在を確認しました。

- [完全な実行記録](observations/attempt-20261006T183101904159Z/run.json)、[標準出力全文](observations/attempt-20261006T183101904159Z/producer.stdout.txt)、[標準エラー](observations/attempt-20261006T183101904159Z/producer.stderr.txt)、[優先度確認](observations/attempt-20261006T183101904159Z/producer.priority.json)
- [作者441項目・改変8件](records/verify.stdout.json)。別担当は固定したID集合と分数へ482項目を独立照合しました。一般的な入力網羅の証明ではありません。
- [資源読取](records/resources-20261006T183041170150Z.json)：load 3.317/12 CPU、idle 85.55%、メモリ空き照会47%・推定5.83 GiB、既知重処理/headless検出0。推定量を確保保証にはしません。
- [実装前11入力](records/pre-execution-inputs.json) は実行前後不変です。[未実測時の保存版](records/pending-snapshot/manifest.json) と保留中の説明を履歴として保持します。
- [画面コードの375項目の模擬確認](records/reader-model.stdout.json) は、Node の自作要素/SVG模型で24状態を対照したものです。実 DOM・実ポインター・描画や画像の証拠ではありません。[検査コード](reader-model-check.cjs) は `node reader-model-check.cjs` で保存データだけを読みます。未実測版の停止確認4項目は [別記録](records/pending-reader/stdout.json) へ残しています。

保存値だけを再照合するコマンドです。新しい対象計算は起動しません。

```sh
python3 -B verify.py --run observations/attempt-20261006T183101904159Z/run.json --mutations
```

## Atlas の計算と再現の境界

元 `predictions.json` は [出所/hash](records/input-provenance.json) を持つ完全一致コピーです。元の現コードは4閾値を扱い、既存 Brier 教材は確率損失を扱います。今回の増分は全境界の ID 包含集合・ROC/PR 対応で、旧計算を再加算しません。新しい AUC、学習、外部 AI/API 呼出しはありません。

通常の閲覧に再実行は不要です。保存結果がある場合は `status.json` の `observation` を確認し、その実在パスを `python3 -B verify.py --run <保存したrun.json> --mutations` へ渡すと、対象計算を起動せず照合できます。今回の保存結果では441項目と8種類の改変拒否を確認しました。

新規実行時は [契約](CONTRACT.md) の資源・排他調整・nice実値・CPU/経過時間上限・自己所有子の回収を確認し、新しい保存先へ完全出力と失敗を残します。未知の観測を競合0へ置き換えず、元資料や期待を結果に合わせて書き換えません。

この合成標本の計算から、確率較正、現実の性能、汎化、公平性、分布変化への耐性、安全認定を結論できません。有限な資料を案内する [Skill](SKILL.md) は、一般 Agent の評価とは別です。元 repo への統合・正式分類・作者による全体件数加算は行っていません。

> 配布用保存reader：端末・実行管理情報を除いた観測データを、専用のschemaとSHAで照合して再生します。元原票のSHAと区別しています。新しい計算・GUI検証ではありません。[データの由来と復元](MIGRATION.md)を確認してください。

# Atlas：公平性の対象を変え、飢餓を読む

相互排他が守られていても、要求したP1が進むとは限りません。この教材では `enabled`（今、選べる）と `executed`（選んだ）を比較し、公平性を課す動作と、要求への応答を別々に判断します。

入口は [保存結果を読む画面](index.html) です。[有限計算の結果](RESULTS.md) に、6列・4仕様の対照と実行ログをまとめました。計算・実画面・独立確認の現在状態と保存先は [status.json](status.json) にまとめます。予想は自由記述で、自動採点しません。

## Atlas の読む順

1. 前提の [相互排他モデル](inputs/prerequisite-model.py) の `atomic` を読み、状態と原子的な辺を確認する。元の学習経路は `executable-technology-atlas/learning/subjects/formal-methods-verification/LEARNING_PATH.md` §5/§6です。[出所の保存記録](records/input-and-dedup.json) で元ファイルの場所を確認できます。教材単体のHTTP配信からworkspace外へは移動しません。
2. 画面で6列と4公平性仕様から対象を選び、P1が進むか予想する。
3. 導入部分 prefix と、繰り返す周期 cycle の時点を進め、出発状態のenabledと選択辺のexecutedを比較する。
4. [著者原典の対応](SOURCES.md)、[固定契約](CONTRACT.md)、[判定実装](fairness.py)、[実装前の手書き期待](expected.json) を照合する。
5. 一周を読んで答えを開き、「この列を公平と認めるか」「P1の要求が満たされるか」を別々に答える。[限定Skill](SKILL.md) も同じ順で案内します。

到達目標は、公平性の単位を明記できること、継続的な機会と断続的な機会を区別できること、過去の入室で新しい要求を満足扱いしないことです。

## Atlas の3つの重要な対照

- P0が資源を保持したCで停滞すると、P1.enterは常時無効です。その動作だけの強公平性は成立してもP1は飢餓します。P0.releaseは有効なので、全動作が無効なデッドロックではありません。
- A→B→C→AでP0が取り続けると、P1.enterの機会は断続的です。両processの弱公平性を満たしても、P1.enterの強公平性には反します。
- 導入部分で一度P1が入室していても、その後の待機要求は別です。先の成功を後の要求への応答と取り違えません。

```text
A: (idle, waiting, free) ─P0.request→ B: (waiting, waiting, free)
↑                                              │ P0.enter
└──────────────P0.release────── C: (critical, waiting, 0)
P1.enter の機会：A=true、B=true、C=false。選択：全てfalse。
```

この矢印図は手書きの説明模型です。保存計算も有限の一周を扱い、無限時間の実threadを観測したものではありません。

## Atlas の利用と再現

通常の閲覧に再計算は不要です。このディレクトリをHTTP配信した入口で `index.html` を読みます。共有環境では既存の配信先を使い、親の単一pageで確認します。作者が新しいブラウザーやタブを起動しません。ファイル直接表示の動作は確認範囲外です。

テキストだけでも [expected.json](expected.json)、[fairness.py](fairness.py)、状態記録から辿る保存 `run.json` で比較できます。保存結果の検証は `python3 -B verify.py <保存したrun.json> --mutations`。これは新しい対象計算を起動しません。

新しく再現するときは [RUN_CONDITIONS.md](RUN_CONDITIONS.md) の資源・優先度・時間・所有資源回収条件を満たし、新しい保存先へ残します。`resources.py` は親の実行枠とGUI休止の参照を引数で受け、`run.py --execute --resource-record <新しい資源記録>` が短い子1件を実行します。未知の読取や条件不成立で止まり、自動再試行はしません。

## Atlas の限界と実務判断

確認するのは既定6列と4仕様です。前提graphの8状態・14辺に停滞8辺を加えた整合確認を、任意の全cycleの探索と呼びません。この6列が除外できても、全モデルの飢餓自由を証明したことにはなりません。実scheduler、待ち時間上限、任意process数、故障、弱メモリー、TLC実行は扱いません。

公平性を要件へ書くときは、入室だけか、解放や要求も含むかを特定してください。動作が永遠に無効なら、強公平性だけではそれを有効にする別の動作まで保証できません。[範囲表](COVERAGE.md) に残る問いを記載しています。

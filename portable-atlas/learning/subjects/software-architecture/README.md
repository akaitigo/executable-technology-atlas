# Software architecture — adapterを替えても同じ契約を守れるか

このSubjectは、構造の名前を覚えるだけでなく、誰の懸念をどの境界・契約・証拠で満たすかを学ぶ入口です。今回の有限1教材は **stdlib hexagonal portとin-memory/実SQLiteの2adapter**。同じ注文use caseを48回実行し、依存方向、正常/境界/意図異常、例外変換を比較します。architecture全quality attributeは未実証です。

## 前提 → 主要概念・仕組み

Pythonの関数・class・例外・JSONとSQLのINSERT/SELECTが前提です。Python 3.9以上と標準`sqlite3`を使い、pip/Docker/外部サービスは不要です。

**port**は内側が定義する目的のある会話、**adapter**はその会話を具体技術へ変換する実装です。本教材のportは`add(Order)`。「行の全値を保存し、既存IDを上書きせず、重複と利用不可を決めた例外で返す」という意味の契約を持ちます。`Protocol`の形が合っても価格・正規化・例外の意味までは保証しないため、独立hand rowsで検査します。[PEP 544](https://peps.python.org/pep-0544/)と[hexagonal原論文](https://alistair.cockburn.us/hexagonal-architecture)を並べて読めます。

業務規則は数量1–100、単価120、id/skuの前後空白除去。boolは数量に含めません。`PlaceOrder`はportだけに依存し、storageに触る前に入力を検査します。adapter側で技術例外をport例外へ変換し、use case側で業務側の例外へ、CLI入口でmodeled statusへ変換します。

## 今回実装 → 正常・境界・意図異常

このREADMEのあるディレクトリで実行します。

```sh
python3 runner.py                    # 保存済み原票をread-only検査
python3 runner.py --record           # 明示的に12入力×2設計×2adapterを再実行、新規原票へ
python3 checker.py                  # producerをimportせず固定行/直接SQL/ASTで検査
python3 test_negative.py            # 使い捨てコピーで4種の改変検出とread-only検査
python3 preview.py                  # dynamic 127.0.0.1 URL; 終了はCtrl-C
```

画面は予想→操作→比較→原典/実装→答えの順です。「2adapterは同じ結果になるか」と「両方とも契約に適合するか」を別々に予想します。比較ボタンは保存済みの実実行を開き、再実行は`--record`です。

| 同じ入力 | port設計: memory / SQLite | tied悪例の差 |
|---|---|---|
| 通常、数量2 | ともに行 `[a,book,2,240]`、201 | memory240 / SQLite200 |
| 数量1 / 100 | ともに120 / 12000、201 | SQLiteは100 / 10000 |
| 数量0 / 101、空白sku、id欠落 | 両方422、保存0行、port呼び出しなし | 悪例もこれらは拒否。異常全てが差になるわけではない |
| quantity=true | 両方422、保存0行 | 悪例は整数と誤認しmemory120 / SQLite100で受理 |
| id/skuの前後空白 | 両方正規化、total240 | SQLite悪例は空白を残しtotal200 |
| 同一IDで数量2→3 | 両方201→409、最初の行を保持 | memoryは未変換例外500 / SQLiteは上書きし201→201 |
| store利用不可 | 両方503、保存0行 | 悪例は両方500。同じ結果でも契約違反 |
| 不正数量 + store利用不可 | 両方422、保存0行、port呼び出しなし | 入力境界がstorage障害より先 |

故障注入はmemoryで実OSErrorを起こし、SQLiteでは実handleを閉じてProgrammingErrorを起こします。port設計のraw exception chainは`DependencyUnavailable → StoreUnavailable → OSError/ProgrammingError`。これは一種類の故障比較で、timeout、disk full、電源断は未教材です。

[ports.py](ports.py)の意味の契約→[domain.py](domain.py)のuse case→[adapters.py](adapters.py)の技術変換→[worker.py](worker.py)のcomposition rootとCLI変換を順に読みます。[bad.py](bad.py)は具体adapterの型で分岐してDBを直接触り、規則と例外が分岐する意図的な悪例です。

## 実務判断

coreのimportを見て具体技術への依存を探し、同じcontract testを全adapterに通すレビューを行えます。正常だけでなく境界と技術障害を比較し、「adapter同士の一致」と「本来の契約への適合」を分けて判断できます。特に利用不可の悪例は同じ500でも不適合です。interfaceを導入しただけでは意味は揃わず、adapterの例外語彙と業務規則の置き場所が必要です。

port導入にはinterface/例外/変換の保守コストもあります。変更理由が一つしかない小処理へ常に追加する判断は本教材から出せません。変更容易性の効果はN1で測り、採用理由と不利益をADRに残します。

## 限界 → 次の実験

全Subject完成ではありません。実framework/本番DI、分散transaction、認証/認可、可用性、性能、security、運用性、migration耐性は未実証。static type checkerは使わず、`Protocol`はruntimeで意味を強制しません。memoryはprocess終了前の実snapshotをraw出力とファイルへ採取し、checkerが固定行と比べます。終了後の独立メモリ走査はできません。SQLiteは別のread-only接続で実DBを直接読みます。

依存図は実ソースASTのimport辺です。`domain.py → ports`はsourceの依存方向で、実行時はuse caseが注入済みadapterの`add`を呼びます。dynamic import、reflection、実ネットワーク、deploymentの依存はAST図では表せません。source依存図だけをarchitecture全体と扱わないでください。

[coverage.json](coverage.json)に主要領域の問い・今回の範囲・一次資料を対応させています。学習は境界/契約→複数view→quality/tradeoff→設計判断と進化へ進みます。

1. **N1 変更可能性/ADR**：価格変更の修正箇所と失敗ケースを同じ条件で測り、portの利益と保守コストを記録。
2. **N2 view/conformance**：context/component/deploymentと実呼び出しtraceを照合し、dynamic importを注入してAST検査の限界を測る。
3. **N3 quality/tradeoff**：遅延・故障・負荷を独立scenarioにし、刺激・環境・応答尺度を決めて測定。memoryの速度から本番DB性能を推論しない。
4. **N4 複数境界/進化**：注文/在庫のdata ownership、再送・部分失敗・schema変更を小実験へ分け、module/process境界の選択をADRへ。

## 原典 → 実装 → 答え

[sources.json](sources.json)に章locator、確認日、実装/未教材へのbindingを保存しています。[hexagonal原論文](https://alistair.cockburn.us/hexagonal-architecture)のinside/outsideとport conversationを、`domain.py`がadapterをimportしないことへ対応させてください。[Python sqlite3](https://docs.python.org/3/library/sqlite3.html)のexception classesをadapterの変換とraw chainへ照合します。[C4](https://c4model.com/)と[SEI ATAM](https://www.sei.cmu.edu/library/atam-method-for-architecture-evaluation/)は次にviewとquality tradeoffを学ぶ原典です。

答え：port設計は固定12入力の全てで2adapterが同じ契約に適合します。tied悪例は通常入力ですでに価格が分岐し、故障時は両adapterが同じ契約違反になります。図の向きだけでなく実結果と独立期待値を組み合わせて確認します。

## 原票・QA・ローカル状態

[current.json](current.json)が現在の実行を指します。原票にはUTC時刻、環境、入力、raw stdin/stdout/stderr、SQL/exception trace、SQLite DB/memory snapshot、独立oracle、source/artifact SHA-256とサイズがあります。[checker.py](checker.py)はhand rowsをproducerから作らず、通常動作で原票を書き換えません。source変更は失効として検出します。digestはbinding検査であり正しさの証明ではありません。

[QA記録](qa.json)に実IAB、capture保存可否、sandbox制約、専用server終了を残します。ローカル限定。commit/push/公開、旧Portal/Core/Graphのgate、Goal更新は今回の割当外です。

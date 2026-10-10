# Apple platformsを学ぶ入口 — optionalは不正な値もnilにする？

有限1教材。既存Swift 6.2.3を使いFoundation Codableを実compile/runした。Darwin arm64のcommand line実行であり、iOS app/device/simulatorや全Subject完成ではない。[UI](index.html)はその保存観測を比較する。

**前提 → 主要概念/仕組み:** Swift optional/throws、JSONkey/value、typed decodeを理解して進む。required `name:String`/`age:Int8`、optional `note:String?`。[Lesson.swift](Lesson.swift)はdecode/decodeIfPresentを明示したCodable Profile。missing/nullはnoteでnilになるが、wrong typeまでnilへ変わるわけではない。[契約](SPEC.md)は境界とscopeを定義する。

**今回の実装・正常/境界/意図異常:** 18展示caseと160組のfield matrix検査を実Swiftで3型にdecode。正常、noteまでrequiredにする`eager-optional`、try?で失敗を既定値に隠す`defaulting`を比較。missing/null/type/key、Int8 -128/127/-129/128、小数、extra key、root array、壊れたJSONを観測。[Python JSON/type oracle](oracle.py)は独立status/profileを比較。[手記anchor](hand-oracle.json)もerror分類を別確認。Int8は表現幅の題材で、実年齢domainの妥当性は別。

**予想 → 操作 → 比較 → 原典/実装 → 答え:** noteのmissing/null/numberはどうなるかを[UI](index.html)で予想。case選択→次の段階/全段階/reset→schema/value/error/独立oracleを比較→公式原典とSwift実装→答え。段階表示は説明用でSwift内部step traceではない。

このdirectoryで:

```sh
python3 -B runner.py --case optional-missing
python3 -B runner.py --json '{"name":"Aki","age":7,"note":7}'
python3 -B checker.py
python3 -B route.py codable
python3 -B route.py ios-simulator
python3 -B preview.py
```

通常runnerは保存された実Swift結果のread-only表示。`--json`はmodeを明示したPython oracle予測で、Swift実行ではない。acceptedはexit0、normal拒否/未知caseはexit2。customは4096UTF-8byteまで。実Swift再実行は `python3 -B runner.py --case optional-null --run-swift` を明示: module内一時binary/cache/TMPDIRを作ってcleanup、原票は更新しない。原票を更新する実compile/runは `python3 -B observe.py --write-evidence`、bindingだけの更新は `python3 -B checker.py --seal-evidence`。通常checker/runner/route/observeは原票を変更せず、normal checkerは再compileしない。

[保存raw](evidence/raw.json)、[compile/run/cleanup](evidence/swift-execution.json)、[UTC/環境/source/input/artifact digest](evidence/run.json)、[実IAB QA](evidence/ui-qa.json)、[integrity](evidence/integrity.json)、[検証結果](evidence/verification.json)。[decode matrix](evidence/decode-matrix.svg)は生成図、IAB JPEGは実capture。previewはdynamic127.0.0.1のみ、確認後Ctrl-Cで終了。[教材内skill](skills/atlas-apple-platforms-engineering/SKILL.md)は既存route、global installなし。

**実務判断:** optional、missing/null、unknown key、型・range、domain validationをAPI契約へ結び付ける。try? defaultを使う場合は隠す失敗の意味を決める。今回Int8範囲外でdataCorrupted/path[]が返った診断は環境付き観測であり、全SDKで同じとは保証しない。

**限界 → 次の学習 → 原典:** macOS Foundation decodeだけ。UI、他Apple OS、date/Data/全JSON/nested schema、concurrency/ARC、ABI、permission、signing、performanceは未実行。[COVERAGE](COVERAGE.md)に主要未教材coverageの問いと次1: schema/migration、次2: actor/ownership、次3: scene/UI、次4: target/testingの4実験と公式locatorを示す。[SOURCES](SOURCES.md)は本文確認とlocatorのみを分ける。SDK/license/OS設定変更、xcode-select install、package install、公開なし。

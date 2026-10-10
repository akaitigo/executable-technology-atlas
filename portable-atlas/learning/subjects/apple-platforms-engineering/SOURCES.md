# Apple一次資料locatorと実装binding

確認日2026-10-05。Web toolではApple動的ページの本文取得とMarkdown取得が制限された。IABで以下3ページの本文を読み直して確認。terminal networkはDNS制限で取得できなかった。取得失敗を実Swiftの未実行と混同しない。

| ID / 公式locator・節 | 確認と実装対応 |
|---|---|
| OPT [decodeIfPresent(String, forKey)](https://developer.apple.com/documentation/swift/keyeddecodingcontainer/decodeifpresent%28_%3Aforkey%3A%29-w7f), Return Value / Discussion / Throws | IAB本文確認。missing/null→nil、wrong typeはthrow。`Lesson.swift`正常noteに対応。missing/nullの区別にはcontainsという次の問い。 |
| REQ [decode(String, forKey)](https://developer.apple.com/documentation/swift/keyeddecodingcontainer/decode%28_%3Aforkey%3A%29-3egly), Discussion / Throws | IAB本文確認。name requiredのkeyNotFound/valueNotFound/typeMismatch分類を[手記](hand-oracle.json)と実Swift rawで比較。 |
| JSON [Foundation JSONDecoder](https://developer.apple.com/documentation/foundation/jsondecoder), Overview / decode / strategies | IAB本文確認。Codable型とJSONDecoderの説明。今回はdefault strategy、Foundation実runtimeで3型をdecoding。format/key/date/Data customization未検証。 |
| ERROR [DecodingError](https://developer.apple.com/documentation/swift/decodingerror) | 公式locatorとsearch確認のみ、本文はWeb JavaScript/Markdown制限。実error classificationを[Lesson.swift](Lesson.swift)でswitchしraw保存。全SDKのdebug文字列/Int8 error pathは保証しない。 |
| FINITE [作者の有限契約](SPEC.md) | 18case、Int8、custom4096byte、異常版2つ、段階表示は作者のscope。[独立Python oracle](oracle.py)はstatus/profileを比較し、Swift error debugを模倣しない。 |

[固定JSON入力](cases.json)→[Swift stdout/raw](evidence/raw.json)→[compile/run log・cleanup](evidence/swift-execution.json)→[UTC/環境/source/input/artifact digests](evidence/run.json)→[integrity](evidence/integrity.json)。[bootstrap](evidence/bootstrap.json)は最初の17case実Swift実行も保存。これは現行18caseの検査原票ではない。図は生成SVG、IAB画像は実captureとして区別。

[COVERAGE](COVERAGE.md)は主要未教材概念の問いと次の4実験、追加の公式locatorを対応付ける。locatorのみと本文確認済みを区別。MacのFoundation成功を他Apple platform/UI/signing成功へ一般化しない。

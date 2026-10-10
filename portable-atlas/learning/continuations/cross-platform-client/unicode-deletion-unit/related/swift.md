# SwiftのCharacterとwire契約の単位

[元JS/Python教材](../../../subjects/cross-platform-client/README.md) → [Swiftで実JSON往復](index.html) → scalar/UTF8のwire契約。元README E1のSwift CLIだけを有限追加し、iOS UI/IME/Kotlin/.NETは実行しません。

正規化なしでJSON stringをdecode→encode→再decode。`é`はCharacter/scalar/UTF16/UTF8が1/1/1/2、`e + U0301`は1/2/2/3。同じ見た目でもwire契約に使うscalarとbyteは違います。

`e+U0301 e+U0301 a`は3/5/5/7。正常はscalar1..4 AND UTF8 byte1..8の両gateなのでscalar超過拒否。故障はscalar gateだけをCharacter1..4へ置換し、byte gateを維持して誤受入。😀×3は3/3/6/12で、どちらもbyte超過拒否です。emptyは両gateの下限拒否。

```sh
PYTHONDONTWRITEBYTECODE=1 python3 checker.py
PYTHONDONTWRITEBYTECODE=1 python3 runner.py
PYTHONDONTWRITEBYTECODE=1 python3 route.py
PYTHONDONTWRITEBYTECODE=1 python3 server.py --record
```

既存Apple Swift6.2.3、arm64 CLI。runtime.pyはowned temporary directoryにcompileし、module cache/binaryを置き、終了時に除去する。toolchain version・compile argv/stdout/stderr/exit・binary digest・stdin/実stdout/exitを採取。新installなし。通常checker/runnerはunit全file hash/mtime不変。明示 `runner.py --record` だけfresh UTC原票とSwift source snapshotを保存しpointerを更新、旧原票を保持する。

serverは専有loopback port0。UIの編集JSONごとに実Swift binaryを新processで実行し、**その応答**からcount・判定・答えを生成する。保存fixtureの答えを編集入力へ流用しない。明示server --recordの間は各POSTを未使用UUID receiptへimmutable保存。UI request revisionを照合し、入力/予想変更後の旧応答は表示しない。旧応答QAのため応答を600ms遅延する（Swift結果は加工しない）。終了Ctrl+Cでowned server/cache/tmpだけ除去する。

[固定表](expected-table.json)のcodepoint、UTF8 hex、4数表、gate/拒否をproducer初回前に固定。独立oracleはSwift countを再利用せずliteralを照合。JSON綴りの一致は要求しない。再decode後のscalar配列とUTF8 hexを照合する。SwiftのString等価比較はcanonical equivalenceを含むので、`==`だけで「正規化されていない」と判定しない。

測るUTF8 byteはdecodeした**文字列payload**のbyteで、JSONのquote/escapeを含むwire全体のbyteではない。encoded_jsonの綴りは原票へ別保存。表示上の文字、scalar、UTF16、UTF8を混同しない。

非string/不完全JSONは実JSONDecoderのDecodingErrorを捕捉しexit2、count/判定/encoded JSONなし。Swiftの契約拒否（有効stringのcountあり）、decode拒否、host通信/実行失敗を別扱いにする。decode/host失敗では正常答えを出さない。初回compile原票と、例外classをtry?推定から実catch採取へ改める前のsourceもQAへ保存した。

[Swift Strings and Characters](https://docs.swift.org/swift-book/documentation/the-swift-programming-language/stringsandcharacters/) / [公式source](https://github.com/swiftlang/swift-book/blob/main/TSPL.docc/LanguageGuide/StringsAndCharacters.md)はCharacterをextended grapheme clusterとして説明し、scalar/UTF8/UTF16 viewを分ける。実装は[Wire.swift](Wire.swift)、[runtime](runtime.py)、[oracle checker](checker.py)、[原典](sources.json)、[coverage](coverage.json)、[Skill](skills/atlas-swift-character-scalar-wire-units/SKILL.md)、[実IAB QA](qa/README.md)。

13literalの有限検証。任意入力の全grapheme correctness、正規化API、locale/IME、iOS UI、Kotlin/.NET、全Unicode、SDK配布/性能は未実証。Core/fullGate/Subject/Atlas completeは中央の範囲。unit-only serverでは親Subjectリンクは配信外、filesystem存在と実表示を区別する。

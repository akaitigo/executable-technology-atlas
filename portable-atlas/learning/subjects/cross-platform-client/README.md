# 文字列契約をRuntime間で比較する

これはcross-platform-clientの有限教材です。Browser JavaScriptとPython stdlibだけを実行し、Subject全体は`incomplete`です。Native Android/Apple/Windowsの共有実装は未制作です。

## 学習経路

1. 前提：JSON、関数、true/false、文字列の基本を知る。Unicode符号位置と符号化単位は初めてでも可。
2. 予想：`😀😀😀`を「4文字まで」で判定するとJSとPythonは一致するか。どの単位を数えるか言葉にする。
3. 概念・仕組み：UTF-16単位、コードポイント、UTF-8バイト、表示上の文字（書記素）を区別する。今回の共有契約はscalar-validな文字列の1〜4コードポイント。byte制限は別に1〜8、正規化はしない。
4. 実装：ASCII上限、emoji 2/3/4/5、結合文字、ZWJを操作し、表とrawを比較。非stringと孤立surrogateの意図的異常も拒否結果を見る。
5. 実務判断：「文字」ではなく単位、正規化時点、不正入力、通信/保存上限を仕様へ明記する。client側チェックだけでserver側の契約を保証しない。
6. 限界と次実験：本教材はJSON固定入力のみ。端末UI、IME、locale、native SDK、通信、DB、配布の同一挙動は未実証。[次の学習案](#未制作範囲を次の実験へ接続)へ進む。
7. 一次資料と実装：下の原典→[JS](validator.mjs)→[Python](verify.py)→[独立oracle](oracle.json)→[checker](check.mjs)へ戻る。

## 再現と記録

このdirectoryで実行。新依存は不要。Python 3とNodeの既存環境を使用します。

```sh
python3 -B verify.py
node check.mjs
node serve.mjs --python observations/python-attempt-04/raw.json
```

serverが表示するloopback URLをBrowserで開きます。Browser自身がJSを実行し、Python欄は**保存済みの実run**です。画面操作でPythonを呼び出すと偽装しません。Source binding不一致では読み込みを拒否します。既存原票は[検証記録](VERIFICATION.md)参照。

更新する時だけ`python3 -B verify.py --record observations/未使用名`。serverにその`raw.json`を渡し、実Browser操作のraw/画像を別の未使用directoryへ保存し、checkerで新原票をレビューして明示的に参照を変更します。normal checkerは書き込みません。checker記録も`node check.mjs --record observations/未使用名`のみ。既存directoryへの上書きは拒否。Source変更後はPython/Browserを両方実再実行します。

`oracle.json`は固定符号位置literalで、validatorのiterator/len/encodeをコピーしません。oracleは符号位置の整数範囲からUTF-16/UTF-8長を計算します。JSとPythonが一致するだけでは正しいとせず、両方をoracleに照合します。13例はUnicode全域の網羅ではありません。

## 未制作範囲を次の実験へ接続

|案|具体概念と問い|作る実験・未実行環境|公式locator|
|---|---|---|---|
|E1|native型の単位・相互運用・serialization：同じJSONをKotlin/Swift/.NETで検証すると？|同じscalar fixtureをAndroid/Apple/Windows実SDKへ渡し、UTF-16/scalar/Character差とwire roundtripを個別原票で比較。SDK導入は別承認が必要|[Kotlin String.length](https://kotlinlang.org/api/core/kotlin-stdlib/kotlin/-string/length.html)、[Swift Strings and Characters](https://docs.swift.org/swift-book/documentation/the-swift-programming-language/stringsandcharacters/)、[.NET Rune](https://learn.microsoft.com/dotnet/api/system.text.rune)|
|E2|入力・国際化・書記素・a11y：結合文字をIMEで編集するとcaret/削除/読み上げは？|NFC/NFD、ZWJ、RTLの編集/削除を各native UIと実ATで追試し、codepoint契約と表示文字制限の適否を判断|[UAX #29](https://www.unicode.org/reports/tr29/)、[UAX #15](https://www.unicode.org/reports/tr15/)|
|E3|通信・拒否・保存・オフライン・移行：clientとserverの仕様Versionが違うと？|JSON受信時の型/サイズ拒否、byte上限とcodepoint上限、旧データ移行、同時更新衝突を実HTTP/保存で追試。今回は通信/DB実験なし|[RFC 8259 §8.2](https://www.rfc-editor.org/rfc/rfc8259#section-8.2)、[RFC 3629 §3–4](https://www.rfc-editor.org/rfc/rfc3629#section-3)|
|E4|build・配布・lifecycle・権限・性能・互換性：中断/復帰/更新で共有契約を維持できる？|各OSでversion固定buildと署名配布候補、foreground/background、再起動、拒否された権限、長入力の上限前検査を実端末で計測。今回install/deployなし|[Android activity lifecycle](https://developer.android.com/guide/components/activities/activity-lifecycle)、[Apple app lifecycle](https://developer.apple.com/documentation/uikit/managing-your-app-s-life-cycle)、[Windows app lifecycle](https://learn.microsoft.com/windows/apps/windows-app-sdk/applifecycle/applifecycle)|

本教材は入力が小さい固定集合なのでDoS耐性も未実証。E4では検査前のpayload上限と資源を別のoracleにする。件数をnative coverageへ転用しません。

## 原典

- [ECMAScript 2024 String Iterator Objects](https://tc39.es/ecma262/2024/multipage/text-processing.html#sec-string-iterator-objects)：StringのUTF-16単位とiteratorのコードポイントを区別。
- [Python str](https://docs.python.org/3/library/stdtypes.html#text-sequence-type-str)・[len](https://docs.python.org/3/library/functions.html#len)・[str.encode](https://docs.python.org/3/library/stdtypes.html#str.encode)：Unicodeコードポイントのsequenceと符号化結果のbyte。
- [RFC 3629 §3](https://www.rfc-editor.org/rfc/rfc3629#section-3)：UTF-8符号化の範囲。不正surrogateを置換してから数えない。
- [Unicode UAX #29](https://www.unicode.org/reports/tr29/)：書記素境界は本教材のcodepoint数とは別問題。

原典locatorを確認した日：2026-10-05。転載素材なし、入力は中立な固定literal、コードはこの教材用実装。[専用Skill](skills/atlas-cross-platform-client/SKILL.md)は既存runner/UIへrouteします。同一Agentのroute確認を独立Forward Evalと呼びません。

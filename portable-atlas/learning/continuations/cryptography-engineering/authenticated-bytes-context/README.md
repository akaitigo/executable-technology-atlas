# 意味と認証bytesの境界

問いは「同じJSON値ならMACも同じか」「用途を認証対象から外すと変更を検出できるか」です。これはCryptography engineeringのLEARNING_PATH §6実験1だけを扱う有限教材です。公開fixture keyによるPython stdlibの実HMAC-SHA256を観測し、保存済み結果をUIで比較します。

## 前提 → 予想 → 操作

JSON値、ASCII/UTF-8のbyte列、hex、hash、共有鍵MACを前提にします。暗号化・公開鍵署名の教材ではありません。

1. 単元directoryで `python3 checker.py` を実行し、保存原票と固定byte oracleを検算します。
2. `python3 -m http.server 0 --bind 127.0.0.1` で未使用portを割り当て、表示されたloopback URLのindex.htmlを開きます。所有serverだけ終了します。
3. 条件と予想を選び「比較する」。正常版/故障版のbyteとtagを読み、答えを開きます。条件変更は予想・結果・答えをresetします。
4. 再実測は明示操作 `python3 runner.py --record`。新しいobservations directoryを作り、古い原票を保全してUI pointerを更新します。引数なしrunnerはread-only拒否で終了します。

予想はraw key順/空白の変更ではtag不一致、独自canonicalでは同じbytes/tag、context変更は正常版で拒否・該当fieldを落とした故障版で通過です。expected refusalは入力契約でtagを作らず拒否します。

## 契約と正常/異常の比較

fieldはpurpose, operation, resource, amount, textの5つだけです。文字列はcontracts.jsonの固定集合。amountはJSON字面 `0|[1-9][0-9]{0,2}`（0〜999）。bool/2.0/2e0/-0を拒否します。重複key、未知field、欠損field、文字列type違反も別に拒否します。構文後の型だけでは2と2.0の差が失われるため、parse_int/parse_floatで表記を制限します。

canonical encodingは上記field順、ASCII、空白なしの独自JSON契約です。標準canonical JSON（RFC8785）準拠ではなく、任意Unicode・浮動小数・入れ子・汎用protocolには広げません。

| 有限条件 | 正常版で元tagが変更後に通るか | 故障版 |
|---|---|---|
| key順/空白を変えたraw bytes（2） | 通らない | なし |
| 独自canonical（1） | 通る、bytesも同じ | なし |
| operation/resource/purpose変更（3） | 通らない | 該当fieldを落とすと通る |
| 契約外8入力 | tag生成前にexpected refusal | 暗号検証とは別 |

認証対象から落ちたfieldの値を後で使う場合、正しいHMAC primitiveだけではその値を保護できません。故障版はこの境界を可視化する教育用対照です。これはHMACへの暗号攻撃ではありません。

## 原典・実装・rawと独立照合

- [RFC2104 §1–2](https://www.rfc-editor.org/rfc/rfc2104.html)：共有鍵とmessage入力、ipad/opad構成。
- [RFC4231 §4.2](https://www.rfc-editor.org/rfc/rfc4231.html)：既知HMAC-SHA256 vector 1。
- [Python hmac](https://docs.python.org/3/library/hmac.html)：new/compare_digest。取得Docs 3.14.8とraw runtimeを分けます。

calculate.pyはhmac.newを使います。checker.pyはproducerをimportせず、expected-bytes.jsonに実行前に固定した手書きliteralからhashlibのipad/opad構成を計算します。既知vectorでoracleを照合し、全traceのASCII/hex/tag/検証結果、command stdout、source/artifact digestを検査します。同じserializerの二度の出力比較だけではありません。4つのin-memory故障原票を検出し、正規rawを変更しません。

UIはobservation-data.jsでrunを読み、raw/command/実装/契約/期待byte/sourceへのリンクを表示します。[QA](qa/README.md)に実IAB、画像、read-only検証を保存します。通常checkerは保存結果の検算であり、UI閲覧時の新HMAC計算ではありません。

## 答えと実務判断

MACは意味を推測せず入力bytesを認証します。同じ意味に同じbytesを割り当てたいなら送受信両端で明示契約が必要です。実務ではoperation・resource・protocol用途を含め、曖昧な解釈を拒否する入力境界を定めます。

messageは読めます。公開fixture keyは誰でもtagを作れ、本番秘密鍵ではありません。共有秘密鍵でも両者がtagを作れるので、第三者への非否認証明にはなりません。freshness・replay・認可は別。この教材には状態guard、時計、実resource操作はありません。compare_digestの利用からtiming安全性全体を証明しません。暗号破り、本番適合、鍵生成/保管/rotationは未評価です。

## 次coverage（未実行）

1. 固定ID set modelのcheck/remember全interleavingと再起動復元。atomic性とMACを分ける。
2. 旧/新公開fixture key、sender、期限policyの有限表。valid MACとpolicy受入を分ける。
3. RFC8785の独立vectorでUnicode/数値境界を別単元化。今の独自契約を標準準拠と読み替えない。

Skillはskills/atlas-authenticated-bytes-context/SKILL.md。route.pyの正常8/未対応4は構造検査のみで、モデルがSkillを選択・実行する挙動評価は未実行です。Core/fullGate/commit/push/公開はこのローカル割当の対象外で未実行。分野全体やAtlas全体のcompleteを主張しません。

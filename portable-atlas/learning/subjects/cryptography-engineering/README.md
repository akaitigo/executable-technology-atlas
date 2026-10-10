# HMACが通った。同じmessageをもう一度送ってもよい？

この1教材は公開合成test keyと固定messageで、Python標準ライブラリのHMAC-SHA256を実計算する。HMACは共有鍵のMAC（message authentication code）であり、公開鍵によるデジタル署名・暗号化とは呼ばない。

## 予想 → 操作 → 比較

1. key、message、tagのうち1つを変えると、検査結果はどうなる？
2. 正しいmessageとtagをそのまま2回送ると、MAC検査だけで2回目を拒否できる？
3. 記憶が消えたら、再送防止はどうなる？

[画面](index.html)で7条件を選び、保存済み実行原票のraw bytes、再計算tag、MAC結果、別の再送防止stateを比較する。UIは説明用の原票replayであり、ブラウザー内で暗号計算や外部送信を行わない。keyは公開された非secretのfixtureで、本番利用禁止。

## 実装・追試

Python 3標準ライブラリだけで実行する。install、外部API、Docker、production key生成・保存・変更は不要。

```sh
python3 -B verify.py
python3 -B observe.py --check
python3 -B runner.py --scenario replay
```

上記checkerはread-only。原票を明示更新する場合だけ `python3 -B observe.py --write` を使う。入力やsource変更後は古いbundleをstaleとして拒否する。書き出しはstagingの全member検証後にpublishする。

画面の確認経路はmoduleをworking directoryにした一時HTTP server:

```sh
python3 -m http.server 8768 --bind 127.0.0.1
```

`http://127.0.0.1:8768/index.html` を開き、終わったらCtrl-C。`file:`直接openは未検証。`evidence/data.js`は保存済みPython計算結果。観測時刻・Python/OpenSSL環境・input/raw/source/artifact SHA-256は [verification.json](evidence/verification.json)、原票は [observation.json](evidence/observation.json) にある。

## 原典 → 実装 → 独立Oracle

| 原典locator | 教材で対応するもの | 対応しないもの |
| --- | --- | --- |
| [RFC 2104 §1–2](https://datatracker.ietf.org/doc/html/rfc2104#section-2) | [runner.py](runner.py)の`hmac.new(..., hashlib.sha256)` | 他のhash、鍵管理の安全性証明 |
| [RFC 4231 §4.2–4.3](https://www.rfc-editor.org/rfc/rfc4231.html#section-4.2) | [oracle.json](oracle.json)に独立転記した2 test vectorとの照合 | RFC全vector・全アルゴリズムの適合 |
| [Python compare_digest](https://docs.python.org/3/library/hmac.html#hmac.compare_digest) | 同型bytes・32byte tagの比較APIを使用 | timing測定やconstant-timeの実証 |
| [RFC 4303 §3.4.3–4](https://www.rfc-editor.org/rfc/rfc4303.html#section-3.4.3) | integrityと別のreplay判定という比較の参考 | ESP、sequence window、IPsec実装・規格適合 |

本文を保存せず、URL・locatorと対応範囲を [sources.json](sources.json) に保持した。test vectorのhexは独立oracleデータとしてだけ転記した。[verify.py](verify.py)はrunnerが生成したtagを期待値として更新しない。[fixture.json](fixture.json)は教材のoriginal合成入力。

## 答え合わせ

| 条件 | MAC | MAC + 教材内のID記憶 |
| --- | --- | --- |
| 正常 | 通る | 受入、IDを記憶 |
| message改ざん / wrong key / tag改ざん | 不一致、拒否 | state更新前に拒否 |
| 同じvalid messageの再送 | 再び通る | 認証済みIDが既出なので拒否 |
| 短いtag / 非hex tag | この教材のfull-tag形式契約で拒否 | state更新前に拒否 |

MACはkeyとmessage bytesから計算するので、同じ入力の再送でも同じtagになる。freshnessの保証はMACだけから得られない。`ReplayGuard`はMAC検証後にmessage内の認証されたIDを記憶する、単一processの説明実装。scenarioごとに新しいstateを用意し、replay条件だけ先に正常1回を受け入れる。JSON順序が違っても同じ認証済みIDならduplicateとする。拒否入力はstateを汚さない。

guardを作り直すと再送を再び受け入れる境界もtestする。永続化・atomic concurrency・distributed state・TTL・reordering・nonce/sequence設計・DoS制限・複数senderのID namespaceは未実装。受入は実際のresource操作・認可を意味しない。messageは読めるままで機密性を与えない。共有鍵を持つ双方がtagを作れるため、第三者への非否認証明とも扱わない。

`compare_digest`の利用は確認するが、処理時間の恒等を測っていない。形式不正のearly rejectionもある。本教材全体をconstant-timeと呼ばない。

## Subject全体の未教材Coverage

暗号化/AEAD、nonce管理、非対称暗号・公開鍵署名、鍵交換、KDF/password hashing、entropy・鍵生成、secure storage/HSM/KMS、鍵配布・rotation・失効・backup、PKI/証明書・TLS、serialization/protocol design、side-channel実測、crypto agility・post-quantum、migration/interoperability、性能・運用・障害回復・complianceは未教材。HMACの汎用安全性・本番適合やSubject完成を主張しない。

[限定Skill](skills/atlas-cryptography-engineering/SKILL.md)はこのrunner/checker/UIだけにrouteする。形式検証と通常・未対応smoke、実IAB QAの範囲は [QA.md](QA.md) に分離する。全体Gateの以前の`yaml`依存不足はこの教材の受入とは別の未通過stateであり、今回はinstall/Core verifyを行わない。

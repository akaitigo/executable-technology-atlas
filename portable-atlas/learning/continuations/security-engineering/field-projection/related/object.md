# IDが見つかった。それは読んでよいrecord？

固定の架空2 tenant・2 actor・4 recordsで、Python pure request handlerのobject権限を比較する1教材。外部API・実attack・実データは使わない。memory中のsynthetic request/responseだけを実行し、外部resourceは変更しない。

## 学習の道筋

1. 前提: Pythonのdict/関数、requestとresponse、tenantを確認する。まず [fixture](fixture.json) のactor所属とgrantを読む。認証済みcontextは仮定なので、「誰かを確かめる」と「何を許す」を分ける。
2. 主要概念/仕組み: ID lookupは存在確認、認可はactor × operation × resourceのpolicy確認。client入力とserver側policyの信頼境界を [dataflow図](assets/trust-and-control.svg) で見る。
3. 今回の実装/正常異常: [画面](index.html)で正常read、別tenant、同tenant無grant、operation違い、入力境界の順に操作し、[handler](runner.py) と [独立matrix](oracle.json) を照合する。
4. 実務判断: objectを返す経路ごとに認可があるか、tenant一致だけで過剰許可していないか、認証済みidentityをrequestから採用していないか、拒否bodyにpayloadがないかを問える。テストにpermit/deny双方を含める判断材料になるが、実製品の安全認定にはならない。
5. 限界: upstream認証、field単位制御、DBとのatomicな検査、負荷・運用を今回の成功から推定しない。次の4実験は未実施として分ける。
6. 原典: この挙動から [API1:2023](https://api-security.owasp.org/editions/2023/en/0xa1-broken-object-level-authorization/) の `Is the API Vulnerable?` / `How To Prevent` を読み、[ASVS公式入口](https://owasp.org/projects/asvs) からversion付きの広い要件へ進む。locatorは教材の証拠を置き換えない。

## 次に学ぶ問いと小実験（4本とも未実施）

| 未教材概念と問い | 次の隔離実験案・何を比べるか | 公式locator |
| --- | --- | --- |
| 認証・session lifecycle: trusted actorは誰が確立する？期限切れidentityが残らない？ | 架空test credentialだけの認証adapterを別教材で用意し、正規/偽造/期限切れのcontext生成と拒否を比較。本教材のactor名入力を認証と取り違えない。 | [OWASP API2:2023](https://api-security.owasp.org/editions/2023/en/0xa2-broken-authentication/) `Is the API Vulnerable?` / `How To Prevent` |
| property-level認可・最小開示: objectのread許可があれば全fieldを返してよい？ | 架空recordへ公開/内部fieldを加え、role別projectionの独立field matrixとresponse列を比較。現実の秘密は入れない。 | [OWASP API3:2023](https://api-security.owasp.org/editions/2023/en/0xa3-broken-object-property-level-authorization/) `How To Prevent` |
| policy/DBの整合・TOCTOU: check後にrecordの所属や権限が変わったら？ | 隔離された変更可能storeでcheckとuseの間を決定的に切り替え、旧snapshotとatomicな条件付き取得を比較。競合・失効時のpayload非返却を検査。今回は不変memoryしかない。 | [MITRE CWE-367](https://cwe.mitre.org/data/definitions/367.html) `Description` / `Potential Mitigations` |
| 入力解析・可用性・sinkの防御:型が合えば大きなbodyや文字列も安全？ | 制限付きlocal parserで長さ・深さ・不明fieldの境界を比較し、拒否と資源上限を観測。入力検査を認可やSQL parameterization/output encodingの代用にしない。 | [OWASP Input Validation](https://cheatsheetseries.owasp.org/cheatsheets/Input_Validation_Cheat_Sheet.html) `Input Validation Strategies` / `Parse Safely, Then Validate` |

上の実験案は新規実装や起動をしていない。cryptography/TLS、supply chain、network隔離、logging/incident、secure SDLC・compliance等は後段の未教材Coverageに残る。roadmapとその公式URLもREADME/indexのlocal source digestに束縛するが、remote本文lockや完備性creditは与えない。

## 予想 → 操作 → 比較

1. actor-aはtenant-red所属。object_idをblue-reportに変えたとき、lookup成功だけで返してよい？
2. 同tenantなら全recordを読める？readできたらexportも許可される？
3. requestにtenantやactorを追加したら、認証済みcontextを上書きできる？

[画面](index.html)でactor/resource/operationと境界caseを選び、lookup-only版とcontrol版の実response、control trace、独立期待matrixを比較する。UIは保存済みPython原票の説明モデルで、新たなhandler requestや外部送信はしない。

## 実装と追試

Python 3標準ライブラリのみ。install、Docker、外部サービス、credentialsは不要。

```sh
python3 -B verify.py
python3 -B observe.py --check
python3 -B runner.py --case actor-a/blue-report/read
```

通常checkerはread-only、bytecodeも書かない。明示的な原票更新だけ `python3 -B observe.py --write` を使う。input/source変更はstaleとして拒否し、stagingの全memberを検証した後にbundleをpublishする。

画面を確認する場合はmoduleをworking directoryにして次を実行する。

```sh
python3 -u -m http.server 0 --bind 127.0.0.1
```

表示された動的portで `http://127.0.0.1:PORT/index.html` を開き、title/module fieldが本教材と一致することを確認する。終了は自分のserverをCtrl-C。他担当listenerを停止しない。これは教材fileのstatic previewで、認可handlerをHTTP endpointとして公開するserverではない。fixtureも証拠も全件架空で、実データをこのpreviewへ入れない。`file:`直接openは未検証。

## 原典 → 実装 → 独立Oracle

[OWASP API1:2023](https://api-security.owasp.org/editions/2023/en/0xa1-broken-object-level-authorization/) の `Is the API Vulnerable?` / `How To Prevent` は、recordと要求operationごとの権限検査を読む入口。[OWASP A01:2021](https://top10.owasp.org/2021/A01_2021-Broken_Access_Control/) の `Description` / `How to Prevent` はserver側の制御と既定拒否の参考。この教材の固有policyはoriginalであり、OWASPの全要件を実装したとは扱わない。

[ASVS公式入口](https://owasp.org/projects/asvs)はより広い検証範囲・version付きrequirement参照の入口だけ。番号付き要件やASVS levelの合格は主張しない。確認したURL/locatorと適用範囲は [sources.json](sources.json)、第三者本文は保存しない。

[fixture.json](fixture.json)はactors・server側tenant/grants・recordsを固定。[oracle.json](oracle.json)は2 actor × 4 resource × 2 operationの16 cellをrunner出力と独立に列挙し、boundary 7件の期待値も固定。[runner.py](runner.py)はfixture側から全組合せを列挙し、[verify.py](verify.py)はmatrix全件、payload非混入、型境界、control bindingを照合する。

## Dataflow・control・答え

`lookup_only`と`controlled`は共通の入力schema・既知actor context・対応operation検査を持つ。意図的bugは、その後のobject権限を省いてIDが見つかったrecordを返すこと。修正版はserver側actor tenantとrecord tenantを照合し、operation + resource_id + resource_typeの明示grantがある場合だけ返す。tenant一致だけでは許可しない。

| 条件 | lookup-only | controlled |
| --- | --- | --- |
| actor-a / red-report / read | 200 架空payload | 200 許可 |
| actor-a / blue-report / read | 200 別tenantの架空payload | 403 tenant-mismatch |
| actor-a / red-archive / read | 200 同tenantでも無許可payload | 403 no-grant |
| actor-a / red-report / export | 200 operation権限を省略 | 403 no-grant |
| actor-b / blue-report / read, export | 200 | 200 許可 |
| 未認証 / 不明actor | 401 | 401 |
| 不明record | 404 | 404 |
| 型不正 / requestへtenant追加 | 400 | 400 |
| 対応しないoperation | 403 | 403 |

独立matrixではcontrol版の許可は3/16。lookup-only版は16/16でpayloadを返し、期待拒否13件を取り逃す。これは固定policyとの不一致数であり、製品の脆弱性率や網羅security scoreではない。traceは診断原票としてschema/context/lookup/tenant/grantのどこで止まったか示す。拒否response bodyにはpayloadを含めない。diagnostic traceは本番のpublic responseに出す設計とは主張しない。

## 信頼仮定・境界・未教材Coverage

`context={actor_id: ...}`は上流で認証済みの信頼できるidentityとして与える。これは認証実装ではなく、callerが任意actorを名乗ることを防ぐtoken/password/JWT/session検証はない。request bodyからactor/tenantを採用しないが、上流contextが偽造されればこの教材だけでは防げない。fixture policyとrecordsが正常・信頼できるという仮定もある。

read/exportは許可結果を比較するsymbolic operationで、実ファイルexportや更新は行わない。pure handlerはrequest/fixtureを変更しない。未知record 404と既知無許可403の差による存在情報・timing、field-level filtering、policy変更のrace/TOCTOU、distributed enforcement、real database query scopingは未実証。

Subject全体の認証・session・credential lifecycle、cryptography・TLS・secret保護、入力encoding/injection/XSS/CSRF/SSRF、file upload、dependency/supply chain、sandbox/network isolation、availability/rate limiting、logging/alert/incident、secure SDLC・risk/threat modeling全体、privacy・compliance、性能・運用・failure/recovery、migration/interoperability、実製品penetration testは未教材。全ASVS/OWASP適合・網羅security保証・Subject完成は主張しない。

[observation.json](evidence/observation.json)は実matrix/boundary結果。[verification.json](evidence/verification.json)には日時・Python環境・input/raw/source/artifact SHA-256とchecker raw結果を保存。[QA.md](QA.md)は実IABと [限定Skill](skills/atlas-security-engineering/SKILL.md) のsmoke記録。旧Goalはpaused、旧full Gateの未通過stateは変更しない。

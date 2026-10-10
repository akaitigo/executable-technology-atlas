# Software supply chainを学ぶ道筋

この文書は[digest・来歴・baselineの既存教材](README.md)から、期待値の保護、builder、依存と再現性へ進むための補足です。有限教材の補足であり、分野全体の学習完了を示すものではありません。以下の次実験はすべて未実行です。

## 1. 前提と仕組み

byte列、SHA-256、JSON、入力→変換→出力、依存graphを理解します。内容のdigest、来歴の申告、誰を信頼するかというpolicyを分けます。

学ぶ順序は **artifactとdigest → 入力・recipeのbinding → 独立した期待値 → 来歴の署名とbuilder identity → 推移依存 → build環境・再現性 → 配布・更新・運用** です。

- hashは鍵を使わない内容照合です。artifactを変える側がdigestも変えれば、同じbundle内での自己整合は作れます。
- MACは共有秘密鍵を持つ者による認証、公開鍵署名は秘密鍵による署名を公開鍵で検証する仕組みです。既存manifestはどちらもありません。
- input hashの申告一致だけでは、その入力から実際にbuildした証明にはなりません。
- 同入力のbyte再現性、署名の検証、builderを信頼する判断、脆弱性がないことは別の問いです。

## 2. 予想から既存実測へ

[UI](index.html)、[pipeline](pipeline.py)、[実生成原票](observations/20261005T044827993451Z-supply-chain/observation.json)、[command](observations/20261005T044827993451Z-supply-chain/command.json)、[artifact index](observations/20261005T044827993451Z-supply-chain/artifact-index.json)、[QA](qa/QA.md)を読みます。この文書作成ではbuildや検査を再実行していません。

| 条件 | 保存済みchecksum / input binding | 初期baselineの結果 |
|---|---|---|
| 正常 | 一致 / 一致 | 一致 |
| sourceだけ変更、未build | 一致 / 不一致 | 拒否 |
| artifactだけ変更 | 不一致 / 一致 | 拒否 |
| manifestの入力申告だけ変更 | 一致 / 不一致 | 拒否 |
| artifactとmanifestを同時変更 | 一致 / 一致 | 拒否 |
| baselineまで差替え | 一致 / 一致 | 独立初期pinで拒否 |
| source更新・再build | 一致 / 一致 | 新基準未承認のため拒否 |
| 依存config更新・再build | 一致 / 一致 | 同じく拒否 |

正常の同入力2回buildはartifact/manifestともbyte一致です。「checksumが合えば期待した由来」という予想は同時変更の反例で外れます。baseline差替え時に届いたbaselineからpinまで作り直す危険な検査は受理してしまいます。既知入力の再build比較も別に記録されています。

8条件はcanonical JSONとローカル合成依存configの実生成・検査です。初期pinはconsumer process memoryでbundleから独立して渡されますが、その選択・保護やgenerator/verifierの信頼は仮定です。source/依存更新の拒否は悪意の証明ではなく、初期基準との差を示します。UIは原票の再生です。署名、SLSA level、OCI形式、hermetic build、全toolchain再現性の実証ではありません。

## 3. 実務で何を判断するか

期待するartifact、source、builder、buildType、parameterを受信bundleの申告から独立して定めます。署名が検証できても、そのsignerやbuilderをこの用途で信頼するかは別判断です。新versionの正当な更新は、古いpinの拒否を消すのではなく、新しい期待値を扱う工程で評価します。

依存の選択、推移依存、実build環境、来歴の生成元、配布経路まで追跡します。SBOMは構成情報であり、CVE評価や署名を自動的に代替しません。rebuild一致から脆弱性・悪意・compiler自体の信頼を結論しません。

## 4. 一次資料への道筋

| 原典とlocator | 読む目的 |
|---|---|
| [SLSA v1.2 Provenance](https://slsa.dev/spec/v1.2/provenance) | 来歴の概念とbuild/source track |
| [SLSA v1.2 Build Provenance](https://slsa.dev/spec/v1.2/build-provenance)、buildDefinition / resolvedDependencies / runDetails | 入力申告とbuilder・run情報の関係 |
| [SLSA v1.2 Verifying artifacts](https://slsa.dev/spec/v1.2/verifying-artifacts)、Steps 1–3 / Forming Expectations | root of trust、署名、期待値、依存の再帰検査 |
| [OCI Image Spec v1.1.1 Descriptor](https://github.com/opencontainers/image-spec/blob/v1.1.1/descriptor.md#digests)、Digests / size | byte照合と信頼できるdigestの取得元 |

既存bindingは[sources.json](sources.json)にあります。独自manifestをSLSA attestationと呼ばず、規格の語彙と教材Subsetを分けます。

## 5. 未教材の問いと次実験

| 未教材 | 問い | 次の入口 |
|---|---|---|
| builder identity・期待値policy | 正しい内容でも許可していないbuilderならどう扱うか | 実験1、署名検証は別の未完条件 |
| 推移依存・package resolution・SBOM | 直接依存だけでbuild入力を捉えられるか | 実験2 |
| 環境・toolchain・hermetic再現性 | 未申告の環境入力で出力が変わらないか | 実験3 |
| 署名・鍵の信頼・失効 | 検証鍵とsignerを誰が管理するか | 暗号・信頼管理の別実証が必要 |
| CVE・registry・更新policy | 安全性と由来をどう分けて判断するか | 実製品と運用の別検証が必要 |
| SLSA level・OCI適合・全supply chain | 各要件をどの証拠で満たすか | 今回のunsigned JSONでは未実証 |

## 6. 次の実験案（3本、すべて未実行）

1. **来歴の期待値policyを独立fixtureで比較する。** 合成claimsにsource ID、builder ID、buildType、parameterを置き、別保持の許可表と照合します。正常、未知builder、別source、未知parameter、許可表をbundleから導く故障版を手書き期待表へ照合します。予想はchecksum一致でもpolicy不一致を拒否することです。これは署名検証後に必要なpolicy判断の説明modelです。claimsの文字列一致を認証済builder identityにしません。原典はVerifying artifactsのSteps 1–2 / Forming Expectationsで、実署名と鍵の信頼は未実行のままです。

2. **合成の推移依存変更を追う。** root→A→Bのローカル合成dependency graphと各入力byteを固定し、Bだけ変えて直接依存名が同じ場合を比較します。予想は直接依存のversion名だけではBの変更を捉えられず、全material digestの照合では差が出ることです。graph閉包を別列挙し、入力集合、artifact、申告material、欠落materialを手書き表へ照合します。原典はBuild ProvenanceのresolvedDependenciesとVerifying artifacts Step 3です。resolver、package download、SBOM形式や全依存完全性は実装しない案です。

3. **未申告環境入力と再現性を比較する。** 独立builder fixtureで明示sourceに加え、設定されたlocale風の合成値が出力順へ影響する故障版を作ります。予想はsource/recipeが同じでも隠れた入力が違うとbyteが変わり、入力を明示固定する版では一致することです。実OS設定を変えず、有限の入力値で出力byte、digest、申告入力を比較します。原典はBuild ProvenanceのbuildDefinition / runDetailsを読む入口ですが、これは独自環境modelです。別OS・compiler・実hermetic buildの証明ではありません。

## 7. 資料の取得・検証状況

2026-10-05に上記SLSA 3ページの本文を取得し、OCI Descriptor v1.1.1もこの追補作業中に取得・確認済みです。今回取得不能だったURLはありません。第三者本文・code exampleは保存していません。

追加したのはこの文書だけです。build、checker、署名、registry、server、UI、global gateは実行せず、既存原票・QA・digestを更新していません。次実験の予想は新たな実測証拠ではありません。

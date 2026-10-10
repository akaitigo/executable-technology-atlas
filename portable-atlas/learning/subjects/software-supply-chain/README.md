# Digest・来歴・独立baseline

問い: artifactとmanifestのSHA-256が合えば、期待した由来だと信じてよいか。

Python標準ライブラリで合成sourceと依存configからcanonical JSON artifactと署名なしmanifestを実生成した。同じ入力の2回buildはartifact・manifestともbyte一致した。sourceや依存configを変えてbuildするとdigestが変わる。保存済みfileを使って8条件の検査を実行し、画面で予想→変更→checksum→input来歴→独立baseline→一次資料・実装→答えを再生できる。

## 開く・再現する

このdirectoryでHTTP serverを起動する。

```sh
python3 -m http.server 4189 --bind 127.0.0.1
```

`http://127.0.0.1:4189/` を開く。Scenarioとchecksumの予想を選び、操作を1段ずつ進める。baselineすり替えでは「危険な検査結果を見る」から、届いたbaselineでpinも作り直す反例を比較する。終了はCtrl-C。画面操作は保存済み実結果の再生で、fileを書き換えたり新buildを実行したりしない。

新しい実生成と独立検算は以下。socket・package install・Dockerは不要。

```sh
PYTHONDONTWRITEBYTECODE=1 python3 observe.py
PYTHONDONTWRITEBYTECODE=1 python3 verify.py
node --check app.js
```

`observe.py` は15秒上限で `experiment.py <execution-id>` を実行し、生stdout/stderr/exitを保存する。runごとのdirectoryは再利用しない。各Scenarioのsource/dependency/recipe/artifact/manifest/baseline/verificationを実fileとして保存する。実験commandが失敗してもそのcommand記録を残し、直前の画面成功観測を保持する。成功時だけ `observation-data.js` をatomic replaceする。

## 今回の実生成

実行IDは `20261005T044827993451Z-supply-chain`。CPython 3.9.6 / Darwin 25.1.0 / arm64。観測の正確なUTC時刻は [observation.json](observations/20261005T044827993451Z-supply-chain/observation.json)、command・生出力・exit 0は [command.json](observations/20261005T044827993451Z-supply-chain/command.json) にある。生artifact/manifestと意図した拒否条件は同runの各Scenario folderへ保存した。[artifact-index.json](observations/20261005T044827993451Z-supply-chain/artifact-index.json) は全60個の生file/記録のdigest・sizeを保持する。

| 条件 | Artifact checksum | input hash binding | 初期baseline |
| --- | --- | --- | --- |
| 正常build | 一致 | 一致 | 一致 |
| sourceだけ変更・未再build | 一致 | 不一致 | 拒否 |
| artifactだけ改ざん | 不一致 | 一致 | 拒否 |
| manifestだけinput申告差替え | 一致 | 不一致 | 拒否 |
| artifactとmanifestを同時変更 | 一致 | 一致 | 拒否 |
| baselineも差替え | 一致 | 一致 | 別保持の初期pinで拒否 |
| sourceを更新して再build | 一致 | 一致 | 新しい基準を未承認のため拒否 |
| 合成依存configを更新して再build | 一致 | 一致 | 新しい基準を未承認のため拒否 |

checksumはauthenticityの署名証明ではない。artifactを改ざんした側はそのdigestも再計算できるため、同じbundleのmanifestに依存する自己整合だけでは同時変更を検出できない。input hashとrecipeが合っていても、そのinputから本当にbuildした証明ではない。今回は既知のinput/recipeで再build比較する別検査も保持し、同時変更ケースでは不一致を確認した。

初期baselineのdigestは実験開始時にconsumer側process memoryへ保存し、各mutation bundleから独立して渡す。baselineを差替えたケースは、この初期pinを保持した検査で拒否された。一方、差替えbaselineからpinも導出した危険な検査では受理された。初期baselineの選び方、memory/fileの運用保護、generator/verifier自体の信頼、署名やbuilder identityはこの教材の仮定・未実証範囲である。

sourceと依存更新の拒否は、更新が悪意だと証明するものではない。初期の期待値とは異なるという結果で、新しい期待値の承認は別工程。

## 実装とoracle

[pipeline.py](pipeline.py) は明示されたUTF-8入力、ローカル依存JSON、recipe codeのbytesに結び付くcanonical JSONを生成する。時刻やrun IDはartifact/manifestへ入れず、実行記録だけに保持する。

[verify.py](verify.py) はbuilderをimportせず、保存済みfileを直接読む別code pathでSHA-256・size・初期pin・input binding・canonical bytesを再計算する。hash primitiveは同じPython hashlibのSHA-256で、別暗号実装ではない。原票booleanを成功根拠にせず、8条件・全Artifact index・Source bindings・raw stdoutを照合する。5 testsで新しいbyte改ざん/size差/誤pinも拒否する。

## 一次資料と未教材Coverage

[SLSA v1.2 Provenance](https://slsa.dev/spec/v1.2/provenance)、[Verifying artifacts](https://slsa.dev/spec/v1.2/verifying-artifacts#forming-expectations)、[OCI Image Spec v1.1.1 descriptor Digests](https://github.com/opencontainers/image-spec/blob/v1.1.1/descriptor.md#digests) のlocatorを [sources.json](sources.json) に結び付けた。第三者本文を保存していない。教材JSONはSLSA attestation/OCI artifactではなく、SLSA levelも成立させていない。

署名、signer identity、SBOM、package resolution、推移依存、CVE、production registry、hermetic build、compiler/toolchain・別OS/別Pythonの再現性、supply chain全体は未教材・未実証。同入力再現性は今回の小さなcanonical JSON builderだけ。全Subjectや理解度の完成は測定していない。

再利用入口は [skills/atlas-software-supply-chain/SKILL.md](skills/atlas-software-supply-chain/SKILL.md)。global installなし。今回の画面受入とcleanupは [qa/QA.md](qa/QA.md) に記録する。

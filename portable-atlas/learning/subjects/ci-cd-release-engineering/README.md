# tested bytesをpromotionする有限release教材

合成artifactの実bytesをPython標準ライブラリで作り、test→candidate→promotion→rollbackの有限stateを計算する1教材です。digestに束縛したtestを別bytesへ流用しないこと、拒否後activeを変えないこと、旧bytesへ戻ることを比較します。外部CI・registry・実deploy・Git操作は行いません。

## 起動と原票

このmodule内で実行。今回はCPython 3.9.6 / Darwin arm64、追加依存なし。保守中Pythonでの追試は未実施です。

```sh
python3 -B test_runner.py
python3 -B runner.py --case normal
python3 -B runner.py --case test-swap
python3 -B runner.py --case missing-history
python3 -B runner.py --case normal --no-rollback
python3 -B serve.py
```

serverは127.0.0.1のport0で未使用portを選び、実URLをstdoutへ出します。別ターミナルでserverを保持してそのURLを開き、終わったらCtrl-C。自分のserver/tabだけ終了し、他担当のlistenerを停止しません。

通常runner/checkerはread-onlyでstdout/stderrのみ、bytecodeや原票を更新しません。保存は明示時のみ。

```sh
python3 -B test_runner.py --record
python3 -B runner.py --case promotion-swap --record
```

UIの明示buttonはPOST /api/run→Python→UUID名の`observations/ui-*/`へ追記します。CLIは`run-*/`、checkerは`checks-*/`。result、合成previous/build/replacementの実`.bin`、metadataを新stagingへ生成し、flush/fsyncしてrename。旧原票を置換しません。意図的staging失敗の旧原票digest不変もrecord checkerで保存します。電源断やdisk-fullの耐久性保証ではありません。

## 予想→操作→比較→原典／実装→答え

1. 「passed testがあれば、artifactを変えてもpromotionできる？」と予想する。
2. normalで計算。「最初のpromotion判断／拒否」を押すと、tested/candidate/active digestが一致。最終eventでは旧digestへrollbackし、2つのartifact bytesがstoreに残る。
3. test-swapへ変更して再計算。testはpassedでもcandidateで`test-artifact-mismatch`拒否。activeは旧releaseのまま。
4. promotion-swapを比べる。candidateはacceptedだが、promotionのworkspace_matches=falseで拒否。先のgateだけでは後の差替えを防げない。
5. failed-testはready=falseの実bytesを検査し、candidate作成前に拒否。単に設定のfailedラベルを表示したものではない。
6. missing-historyでは初回promotion成功、rollbackはhistoryなしで拒否。架空の旧releaseやfallback rebuildを作らない。
7. rollback要求を外すとnormalのactiveは新digestのままでnot-requested。eventを戻して、途中stateと別欄の最終答えを区別する。
8. raw events／[runner](runner.py)／[独立Oracle](oracle.py)／下の公式locatorで、どのbytesを何が検査したか答え合わせする。

## 有限契約と独立Oracle

artifactは`ATLAS-SYNTHETIC`＋NUL＋小さなcanonical JSON＋newlineのbytes。version1が旧release、version2がbuild、version3が意図的差替え。testはheader・format/release/readyのschema・ready=trueを検査し、artifact SHA-256とpolicy digestを記録します。このチェックは実ソフトウェアのunit/integration testではありません。

candidateはpassed testと現在bytesのdigest一致を条件に、append-only storeへbytesを保存し、test record digestも束縛。promotionはworkspace/test/candidate/stored bytesとtest recordのbindingを再検査し、active pointerだけを変えます。拒否時はactiveを変えません。rollbackは保存済みprevious bytesのdigestを再照合してpointerを戻すだけで、再build・削除・DB復旧をしません。

| case | candidate | promotion | rollback要求あり |
|---|---|---|---|
| normal | accepted | promoted | rolled-back、旧bytes不変 |
| test-swap | refused | 未到達 | not-attempted、旧active保持 |
| promotion-swap | accepted | refused | not-attempted、旧active保持 |
| failed-test | refused | 未到達 | not-attempted、旧active保持 |
| missing-history | accepted | promoted | refused、新activeを保持 |

[Oracle](oracle.py)はrunnerをimportせず、独立の5-case transition table、raw bytesのSHA-256再計算、各eventのworkspace/test/candidate/store/active/previous、gate条件、最終summaryを照合します。tableは宣言した有限条件だけの期待値で、任意pipelineの検証器ではありません。[checker](test_runner.py)は10 tests、5 cases×rollback false/trueの10条件、snapshot改変・test/digest/guard改竄の拒否を含みます。traceは各run最大6 event。並行処理・永続state・署名・悪意あるrunnerの隔離は未検証です。

## 学習の道筋と未教材の次の問い

前提はbytes、hash、bool、状態遷移です。まずbuild output（artifact）とtest resultを分け、digestによる対象bindingを読みます。次にcandidateを承認対象として固定し、promotion gateを直前にも照合する理由、historyとrollback先を学びます。上の正常／差替え／失敗／初回releaseを操作し、実務で何が不足するかを整理して原典へ進みます。

この有限教材で判断できるのは「passedはどのbytesに対する結果か」「差替えの時点ごとに拒否できるか」「失敗後のactiveは何か」「rollback先が実在するか」です。SHA-256一致だけではbuilder/test resultの信頼、署名、reproducible build、production health、migration互換性は証明できません。Pythonのprivate storeは学習用APIの不変性で、攻撃者に対するsecurity boundaryではありません。

次の3実験は**未実施の計画**で、今回runnerの機能や成功creditには数えません。

| 主要未教材の概念・問い | 次の有限実験 | 公式locator |
|---|---|---|
| provenance／signature／builder trust：正しいdigestなら誰のbuildでもよい？ | 架空signer allowlist、input/policy binding、manifest改竄の合成条件を比較。実署名とtrust root検証は別の明示割当が必要 | [SLSA v1.2 Build: How to verify](https://slsa.dev/spec/v1.2/verifying-artifacts#how-to-verify)、Step1/Step2 |
| concurrent promotion／approval／secret boundary：古い承認が新候補へ流用される？ | 2候補のgeneration付きcompare-and-swapと承認tokenの有限interleavingを比較。実CI権限・cancel・secretを追加しない | [GitHub concurrency](https://docs.github.com/en/actions/how-tos/write-workflows/choose-when-workflows-run/control-workflow-concurrency)、[Deployments and environments](https://docs.github.com/en/actions/reference/workflows-and-actions/deployments-and-environments): deployment protection rules |
| health／canary／DB migration／recovery：旧artifactへ戻ればdataも復旧する？ | 合成schema v1/v2の互換表とhealth失敗stateを別モデルで比べ、pointer rollbackとdata recoveryを区別。実service・DB試験は未実施 | [Kubernetes Deployments: Rolling Back](https://kubernetes.io/docs/concepts/workloads/controllers/deployment/#rolling-back-a-deployment)、Pod templateだけのrollbackの注意、Revision History Limit |

実runner隔離、cache/dependency pinning、reproducibility、SBOM、脆弱性検査、release signing、policy変更、semantic version、provenance、承認・secret、並行性、canary、migration、backup、observability、実recoveryも未教材です。[coverage](coverage.json)は本Subjectの未教材と他の全Subject未評価を保持します。この3案は分野全体を網羅しません。

## 一次資料locator（2026-10-05 JST閲覧）

- [SLSA v1.2 Verification Summary Attestation / How to verify](https://slsa.dev/spec/v1.2/verification_summary#how-to-verify)、特に手順2 subject digestとartifact、手順6 verificationResultの照合。本教材は署名／verifier信頼／level検証をしないため、VSA実装・SLSA適合とは主張しません。
- [GitHub Store and share data / Passing data between jobs / Validating artifacts](https://docs.github.com/en/actions/tutorials/store-and-share-data#validating-artifacts)：artifact不変性とdigest検証を参照。公式の不一致はwarning、本教材のhard refusalは独自契約でありActionsの挙動を再現しません。
- [Kubernetes Deployments / Rolling Back / Revision History Limit](https://kubernetes.io/docs/concepts/workloads/controllers/deployment/#revision-history-limit)：保持historyとrollback限界への次の問い。本教材はKubernetesやDeployment controllerを起動しません。

第三者本文・図・code exampleを保存／転載せず、URL・書誌・locatorのみを保持します。[QA](QA.md)でraw/captureの観測範囲を確認し、[module Skill](skills/atlas-ci-cd-release-engineering/SKILL.md)は既存runner/checker/UIの入口として使います。global installなし。Subject/Repository全体complete、Core audit/npm gate、旧Goal再開、commit/push/公開の意味はありません。

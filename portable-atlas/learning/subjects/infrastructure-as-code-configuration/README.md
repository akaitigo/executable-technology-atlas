# Planのあと、世界が変わったら？

合成JSONのdesired/observedを比較し、planを保存してからapplyする有限教材です。12条件の実ファイル実験では、正常な変更後の再reconcileはno-op、古いsnapshot・未知値・無承認deleteはstate不変でblockedでした。Terraform等の製品や外部インフラは実行していません。

## 学ぶ道筋

1. 前提：JSON objectと整数revisionを読めれば始められます。cloud accountやTerraformは不要です。
2. 主要概念：宣言は「欲しい状態」、observedは「ある時点の観測」、diffはその差、planは差分とsnapshotの保存、applyは検査後の変更です。冪等性は同じ宣言へ再reconcileしたとき変更がなくなることで確認します。
3. 実装・正常異常：[画面](index.html)で予想→入力→plan→適用直前との比較→原典/実装→答えと進みます。まずreconcile、次にdrift、stale-revision、delete-blockedを比べ、残りの境界も確かめます。
4. 実務判断：diffだけで実行を決めず、何を観測したplanか、適用直前に変化していないか、deleteの承認がどのplan/IDへ束縛されるかを確認できます。staleを見つけたら自動適用せず、再観測と再レビューが必要だと判断できます。
5. 限界：この教材は単一processのsnapshot検査です。確認と更新の間へ別writerが入る競合、実providerの観測、分散lock、署名・実権限、製品の安全性は証明しません。
6. 原典：下のCoverage/次の実験と[sources.json](sources.json)から公式locatorへ戻ります。今回の理解だけで本番deploy可否を判断しません。

## 再現と読み取り

このdirectoryで、通常の検査は読み取り専用です（Python stdlibのみ）。

```sh
PYTHONDONTWRITEBYTECODE=1 python3 checker.py
python3 -u -m http.server 0 --bind 127.0.0.1
```

serverが表示する動的portを使ってloopback URLを開きます。titleは「Planのあと、世界が変わったら？ — Declaration Lab」、Field IDは`infrastructure-as-code-configuration`です。別教材/別serverでないことを確認してください。終了時は自分が起動したserverだけCtrl-Cで停止します。

観測更新を明示的に選ぶ場合だけ、次を実行します。新しいrun directoryを作り、成功時に画面用pointerを置換します。画面buttonは保存済み結果の再生で、実験の再実行や外部変更はしません。

```sh
PYTHONDONTWRITEBYTECODE=1 python3 runner.py --record
PYTHONDONTWRITEBYTECODE=1 python3 checker.py
```

optionなしのrunnerはexit 1で何も変更しません。旧runは保持します。承認inputは合成JSONで、実際の人の承認/認証ではありません。

## 実観測

run [`20261005T054235753564Z-iac`](observations/20261005T054235753564Z-iac/observation.json)、UTC `2026-10-05T05:42:35.815795Z`–`05:42:35.947066Z`、CPython 3.9.6 / Darwin 25.1.0 / arm64、attempt 1・retry 0。実[command/stdout/stderr/exit](observations/20261005T054235753564Z-iac/command.json)、154 fileの[hash/size index](observations/20261005T054235753564Z-iac/artifact-index.json)を保持しています。

| 条件 | 結果・比較 |
|---|---|
| noop | actions 0、revision/hash不変 |
| reconcile | create+update、revision 7→8 |
| drift | plan前のreplicas 1→宣言の2、revision 8→9 |
| stale-revision | plan後revision 8を保持、blocked |
| silent-drift | revision据え置きでも現在replicas 5を保持、blocked |
| delete-blocked | 未承認deleteを拒否、resource保持 |
| delete-approved | exact plan digest+IDの合成承認、対象だけdelete |
| wrong-approval | 別plan承認を拒否 |
| unknown-value / unsupported-attribute | 未知値/未知属性を無視せず拒否 |
| tampered-plan / desired-changed | 保存後action/宣言の変化を拒否 |

成功4条件は2回目plan/actions 0、再apply/no-op、state/revision同一。blocked 8条件は適用直前state bytesを保持しました。[simulator](simulator.py)と[実JSON driver](experiment.py)のdigestは観測へ束縛されています。[checker](checker.py)はproducerをimportせず、独自schema/diff検査とdesiredからの最終state導出で検算します。SHA-256自体は同じstdlibです。7テストは全条件、drift/stale区別、冪等性、未知値/承認/repin改変反例、raw file集合とsource bindingを検査します。

Source binding（観測時のfile bytes SHA-256）：

- `simulator.py`: `4d52e2e2ea810d558b67454e9a2f3ad65578585ab210fd76c3898f42dae5b24b`
- `experiment.py`: `f4bbd2909d94acb45c2c3f8be327603086ec0a1c13447ebe4bfd3af54569f178`

## 未教材Coverageから次の実験へ

以下は提案であり、まだ実装・実行していません。公式locatorの概念を独自実験へ写す段階と、実製品による検証は分けます。

| 主要概念・問い | 次の実験（未実行） | 公式locator |
|---|---|---|
| provider / refresh / computed値：観測の鮮度と未知値は誰が決める？ | ① task-ownedローカル観測adapterを設け、読み取り失敗/未知値/観測前後の変更を区別する。製品providerの検証は別途。 | [Providers / Introduction](https://developer.hashicorp.com/terraform/language/providers#introduction)、[Drift / refresh-only plan](https://developer.hashicorp.com/terraform/tutorials/state/resource-drift#run-a-refresh-only-plan) |
| state / backend / 並行更新：hash確認直後に別writerが入ったら？ | ② 2つの合成writerを同期させ、snapshot検査だけのlost updateとCAS/lockありを比較する。 | [State Locking](https://developer.hashicorp.com/terraform/language/state/locking) |
| dependency / replacement / lifecycle：updateでなく作り直す変更は？ | ③ 2resource依存とimmutable属性を持つ合成modelで、更新順・replacement・delete保護を比較する。 | [Resources / Apply the configuration](https://developer.hashicorp.com/terraform/language/resources#apply-the-configuration) |
| partial failure / recovery：2つ目の変更で失敗したら何を再観測する？ | ④ 合成applyの途中で例外を注入し、部分state・再plan・復旧と危険な盲目retryを比較する。 | [Apply / Apply Options](https://developer.hashicorp.com/terraform/cli/commands/apply#apply-options)（製品rollback保証としては使わない） |

HCL、module/import/moved、secrets/sensitive values、plan署名・policy/実権限、Ansible/OpenTofu/Pulumi比較、eventual consistency、production性能も未教材です。今回のJSON schema（最大6resource、service replicas/port/enabled、config text）へ無理に集約しません。

Terraformの[plan](https://developer.hashicorp.com/terraform/cli/commands/plan#introduction)と[apply / saved plan mode](https://developer.hashicorp.com/terraform/cli/commands/apply#saved-plan-mode)は概念の原典です。実Terraformではsaved planを渡す行為が承認として扱われる点を、今回の独自per-delete承認modelと同一視しません。第三者本文は保存せずURL/metadata/locatorだけ保持しています。

[実画面QA](qa/QA.md) / [教材内Skill](skills/atlas-infrastructure-as-code-configuration/SKILL.md)。有限1教材の結果であり、全SubjectやRepository完成を主張しません。

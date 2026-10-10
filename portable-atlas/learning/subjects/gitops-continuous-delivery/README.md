# GitOps継続的デリバリー：宣言へ戻すloop

ローカルの宣言file bytesと、メモリ内actual stateを比較する有限教材1単位です。Git操作、Argo CD製品、cluster syncを新たに実行した教材ではありません。分野全体は未完成です。

## 学習の道筋

1. **前提**：JSON、辞書、期待値と実値、hashを識別子として使う意味。GitやKubernetesの事前インストールは不要。
2. **主要概念／仕組み**：desiredは「こうあってほしい状態」、actualは現在の状態、reconcileは観測→差分→適用→再観測。宣言変更とactualへの手動変更は別です。[manifest.json](manifest.json)のgenerationと実file bytesのSHA-256がrevisionを識別します。内容が同じv1とrollback-v3でもgenerationは異なります。hashは改変検出で、署名・真正性ではありません。
3. **予想→操作→比較**：[UI](index.html)で予想を書きcaseを実行。stepを切り替えて、publish後もactualはまだv1、次tickでv2になることを確認。manual driftではapplyが戻し、observe-onlyは差分を表示するだけ。ignore-noteはnoteの不一致を残してmanaged fieldsだけ一致します。rawにもignored差分を残します。
4. **原典／実装→答え**：[runner.py](runner.py)を読み、各tickのliveBefore/diff/liveAfterとbytes/hashを追う。[oracle.py](oracle.py)は独立固定遷移表・別canonical hash構築で比較します。古いv1 packetをv2の時点で受け取ったtickは拒否され、actualが変更されないことが答えです。rollbackは前内容を新revision（generation3）として宣言するので受け入れます。
5. **実務判断**：誰がfieldを所有するか、変更を宣言へ反映するか、driftを戻すかを明示する。ignoreを増やすと説明対象の一致範囲が狭まります。表示上のmanaged一致からexact一致や健康を推論しない。古いrevisionやhash不一致を適用せず、rawと拒否理由を調べます。
6. **限界**：3field・単一resource・原子的な辞書更新・逐次tick・固定3revision。remote pull、永続履歴、Git認証／署名、複数controller、部分失敗、retry/backoff、prune、clusterのhealthは未実証。宣言filesはOSでimmutableに保護されず、manifestも編集可能です。事前hashは信頼済み入力という模型条件です。
7. **原典**：[sources.json](sources.json)で原典のsectionと模型／未教材の対応を確認。OpenGitOpsの原則は理解の枠組み。本模型を原則すべての実証と呼びません。Argoではdiff除外だけでapply除外にならない設定があり、模型のignore仕様は製品設定と同一ではありません。製品rollbackの制約も原典で別途確認します。

## 再現

このディレクトリでPython 3.9以降、標準ライブラリだけ。

```sh
python3 -B runner.py --case drift-restore
python3 -B checker.py
python3 -B checker.py --record
python3 -B server.py
```

checkerは通常read-only、原票の更新は明示`--record`のみ。serverが表示する動的127.0.0.1 URLでUIを開き、Ctrl-Cで終了します。UIは実runnerを呼び、step切替は保存された実traceの表示のみです。

[実行原票](observations/run.json)には時刻・環境・input bytes・rawdiff・source/artifact digest、[実Browser QA](observations/qa.json)には画面とcleanup、[session記録](observations/session.json)には担当・資源を保持。[Skill](skills/atlas-gitops-continuous-delivery/SKILL.md)はこの教材だけをrouteします。

## 全Subjectの未教材coverageと次の問い

| 範囲 | 今回から判断できること／残る問い | 次の実験（未実施） | 一次資料locator |
| --- | --- | --- | --- |
| 宣言・履歴・取得・source integrity | bytesとgenerationを区別できる。誰が宣言を変更し、真正性と履歴をどう保証するか？ | 署名済みrevisionと未署名revision、source取得失敗と古いcacheを有限比較 | [OpenGitOps](https://opengitops.dev/) Versioned and Immutable / Pulled Automatically、[Argo Security](https://argo-cd.readthedocs.io/en/stable/operator-manual/security/) |
| reconcile・field所有・同期方式 | 戻す／観測だけ／明示ignoreを選べる。実clusterの競合と比較除外／適用除外は？ | 2controllerが同じfieldを更新、所有権分割と競合を比較。ignoreDifferencesとRespectIgnoreDifferencesを対比 | [Sync Options](https://argo-cd.readthedocs.io/en/stable/user-guide/sync-options/) Server-Side Apply / Respect Ignore Differences |
| 継続配信・健康・段階release | desired一致と健康を混同しない。健康悪化時に次段階へ進めるか？ | 2段階配信で、desired一致でも不健康なresourceを与えて停止とrollback宣言を比較 | [Resource Health](https://argo-cd.readthedocs.io/en/stable/operator-manual/health/)、[Sync Options](https://argo-cd.readthedocs.io/en/stable/user-guide/sync-options/) |
| 障害・retry・削除・復旧 | staleを拒否できる。部分適用・削除・source喪失からどう戻すか？ | 3resource中1件失敗、有限retry/backoff、prune誤宣言と復旧を比較 | [Automated Sync](https://argo-cd.readthedocs.io/en/stable/user-guide/auto_sync/) Automatic Retry / Pruning / Automated Sync Semantics |

まず宣言変更とdriftの違いを理解し、所有権、健康、障害復旧へ進んでください。ここで挙げた4実験は計画であり今回の実行証拠には含めません。

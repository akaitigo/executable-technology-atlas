---
name: atlas-infrastructure-as-code-configuration
description: このmoduleの合成JSON diff・plan・apply教材を読み、drift、stale snapshot、冪等性、delete承認を実観測と比較する。Terraformや外部infraのdeployには使わない。
---

# 合成JSONの計画と適用を比較する

教材rootはこのfileから`../../`。まず[README](../../README.md)の道筋・実観測・未教材Coverageを読み、[UI](../../index.html)で予想から答えまで進む。画面は実結果の再生であり、実apply入口ではない。

- 通常の根拠確認：rootで`PYTHONDONTWRITEBYTECODE=1 python3 checker.py`。読み取り専用の独立oracleで、[観測pointer](../../observation-data.js)とrun内原票を検査する。
- snapshot後の変化ならstale-revisionとsilent-drift、計画前の変化ならdriftへRouteし、plan/current/afterのrevision/hashと原票を照合する。正常reconcile後の2回目actions 0も確認する。
- 承認ならdelete-blocked/delete-approved/wrong-approvalを比較する。合成承認と実権限、digestと署名、snapshot照合と分散lockを区別する。
- 再観測をユーザーが明示要求したときだけrootで`PYTHONDONTWRITEBYTECODE=1 python3 runner.py --record`、その後checker。旧runは削除しない。runner optionなしは何も変更しない。
- 実装を問われたら[simulator](../../simulator.py)、実行入力は[experiment](../../experiment.py)、公式概念は[sources](../../sources.json)へ戻る。

「Terraformでcloudへapply」「本番remote lockを検証」等はこのmoduleでは未対応と説明し、実操作を始めない。未知の問いを既存12条件へ無理に当てはめない。READMEの次の実験へ案内するが未実行を実証済みにしない。このSkillはmodule-localで、global installや外部permissionを要求しない。

---
name: atlas-authenticated-bytes-context
description: 公開fixtureの有限HMAC教材でJSON意味と認証bytes、operation/resource/用途の欠落を比較する。本番鍵や暗号安全性監査には使わない。
---

この単元のREADMEとcontracts.jsonを読む。実装・原票・checkerは単元内の相対pathで解決する。
依頼をroute.pyの8つの日本語入口へ対応づけ、UIで予想→比較→byte/tag→答えを読む。checker.pyは読み取り検算。runner.py --recordは明示された再記録時だけ使い、通常runnerは書かない。
raw tagの違いを意味の違いと混同しない。独自canonicalは固定field/type/整数表記の契約でRFC8785準拠ではない。
用途等の欠落でMACが通る故障版と、含めた正常版で変更が拒否される境界を比較する。expected refusalは暗号検証成功ではなく、tag生成前の入力拒否。
本番鍵生成、暗号破り、認可実装、RFC8785適合証明は未対応としてREADMEの次coverageへ案内する。新権限、公開、課金、実service操作をこのSkillから推定しない。

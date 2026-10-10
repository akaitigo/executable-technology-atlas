---
name: atlas-role-diamond-closure
description: 保存したrole菱形とcycleのtraceから、現在経路・訪問済み・権限出所・拒否を区別する。
---

# Atlas：権限集合を公開してよいか読む

通常は[status](status.json) → [前提](PREREQUISITES.md) → [README](README.md) → [計算記録](MEASUREMENTS.md) → [操作画面](index.html) → [原典/実装](reference.html)へ。未実行なら手表/契約/コードまでで止まり、予想を測定値と言わない。GUI保留なら保存JSONと本文だけを読みbrowser/serverを新規起動しない。保存証拠を読むためにtargetを再実行する必要はない。

次の6問を、該当case/event→集合→原典/実装→限界へ辿る。

1. 正常菱形で2回目viewerはactiveにあるか。visitedにあるだけでcycleとする誤りを説明する。
2. viewer→leadを加えたとき、閉じたcycle_pathの各edgeはどれか。故障のreported_pathとは分ける。
3. leadの直接と継承の両方にreadがある理由は何か。継承から直接分を差し引かない定義を使う。
4. readの出所が3roleなのに、viewerは2経路あるから4個と数えない理由は何か。role集合と経路を分ける。
5. 未知ghostと真cycleで、診断の部分到達を利用可能権限へ流さないことをどこで確認するか。nullと成功の空集合を区別する。
6. 認証済み/scope一致の仮定、この模型の成功、NIST階層の語彙、実resource強制は同じ保証か。

有限5条件の保存資料利用です。全RBAC/全graph証明/標準適合/学習者や一般Agent能力評価ではありません。未知参照edgeや任意schemaはこの5条件の実target検証に含めない。新しい実行は現在の負荷/単独枠/nice/期限/回収を別途確認し、古い資源判断を再利用しない。

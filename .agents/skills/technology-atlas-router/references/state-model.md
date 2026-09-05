# 状態モデル

次の軸を混ぜない。

- Catalog lifecycle: `planned | active | existing | complete | deferred`
- Atlas Release: `planned | active | incomplete | complete | superseded | archived`
- Coverage Target: `missing | planned | partial | covered | excluded | infeasible | expired`
- Evidence verdict: `pass | fail | inconclusive`
- Portal verification: `verified | unverified | invalid | quarantined`
- Completion class: `not-definitive | bounded-historical | subject-definitive`

v1 CertificateはTrust分類にかかわらず`bounded-historical`であり、`subject-definitive`ではない。`superseded`は当時のCertificate履歴を削除しない。Certificate失効は署名付きNoticeがIndexに存在するときだけ別軸で扱う。`excluded`と`infeasible`には理由と再評価日を添える。`expired`を現行passとして推薦しない。

固定ReleaseがないSubjectは`unclassified`の未完了として返す。`open required`と非後退Baselineの違反数は0件でも明示し、0件を省略や完成の根拠にしない。

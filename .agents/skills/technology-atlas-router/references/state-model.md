# 状態モデル

次の軸を混ぜない。

- Catalog lifecycle: `planned | active | existing | complete | deferred`
- Atlas Release: `planned | active | incomplete | complete | superseded | archived`
- Coverage Target: `missing | planned | partial | covered | excluded | infeasible | expired`
- Evidence verdict: `pass | fail | inconclusive`
- Portal verification: `verified | unverified | invalid | quarantined`

`superseded`は当時のCertificateを失効させない。Certificate失効は署名付きNoticeがIndexに存在するときだけ別軸で扱う。`excluded`と`infeasible`には理由と再評価日を添える。`expired`を現行passとして推薦しない。

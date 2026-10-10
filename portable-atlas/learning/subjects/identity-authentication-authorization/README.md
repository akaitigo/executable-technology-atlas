# Authorizationのscope・継承・revoke境界

認証済みIdentityを入力として仮定し、固定したneutral policyが「どのRoleのPermissionを、どのScopeで、いつまで使えるか」を判定する最小教材です。OAuth/OIDC/login/WebAuthnの認証処理は実装せず、AuthorizationのDecisionだけを観測します。

## 先に予想する

次の3件が`allow`か`deny`かを予想してからUIを操作します。

1. `subject-01`は`project-alpha`で`editor`を持つ。`editor`が`viewer`を継承するとき、`document.read`できるか。
2. 同じSubjectが同じRoleを`project-beta`へ持ち出せるか。
3. `viewer`から`document.read` grantを削除した後、同じ`project-alpha`要求はどう変わるか。

## 実行

Python標準ライブラリだけを使います。

```bash
cd learning/subjects/identity-authentication-authorization
python3 verify.py
python3 observe.py --check
open index.html
```

Evidenceを再生成する場合だけ、次を実行します。

```bash
python3 observe.py --write
python3 observe.py --check
```

## 実観測

| Scenario | Policy | Decision | Reason |
|---|---|---|---|
| Role inheritance | `editor → viewer → document.read` | `allow` | `inherited_permission` |
| Scope crossing | assignment=`project-alpha`, request=`project-beta` | `deny` | `scope_mismatch` |
| Before revoke | `viewer` has `document.read` | `allow` | `inherited_permission` |
| After revoke | `viewer` grant removed | `deny` | `permission_not_granted` |

- 実行結果: [evidence/observation.json](evidence/observation.json)
- 実行環境・source digest: [evidence/verification.json](evidence/verification.json)
- 実装: [model.py](model.py)
- Positive/negative検査: [verify.py](verify.py)

各Decision traceは`identity-input → scope-match → role-closure → permission-lookup → decision`を記録します。Grant削除は`policy-v1`を破壊せず、`policy-v2-read-grant-revoked`という新しいsnapshotで観測します。

## 一次資料との接続

- [The NIST Model for Role-Based Access Control](https://www.nist.gov/publications/nist-model-role-based-access-control-towards-unified-standard) — Abstractとリンク先論文Section 2.2を、Core/Hierarchical RBAC vocabularyとRole inheritanceの根拠にします。
- [NIST IR 6192](https://csrc.nist.gov/pubs/ir/6192/final) — Abstractとrole hierarchy discussionを、Role-mediated accessと階層関係の根拠にします。
- [NIST SP 800-162](https://csrc.nist.gov/pubs/sp/800/162/upd2/final) — Abstractのsubject/object/operation/environment属性を、より広いABACとの境界確認に使います。

[sources.json](sources.json)にはURL、文書識別子、locator、何を支えるかだけを保存し、第三者本文は保存していません。この実装は標準本文の転記や適合認証ではなく、固定Subsetの説明モデルです。

## 仮定・反例・制限

- `authenticated_identity: true`は入力仮定です。Credential発行・検証、Session、MFA、Federationはありません。
- Scopeは文字列の完全一致だけです。階層Scope、Resource ownership、Tenant federationは扱いません。
- Role hierarchyは`editor → viewer`だけです。cycleはfail-closedに検出します。
- Grant削除後の判定は直ちに新Policy snapshotを使います。Cache、分散伝播、long-lived sessionは扱いません。
- Unknown action、unauthenticated input、scope crossing、hierarchy cycleをnegative検査します。
- RBAC/ABAC/ReBAC/Capabilityモデル全体の比較や、製品・IdP・Policy Engineとの相互運用を証明しません。
- 合成Subject・Resourceだけを扱い、外部login、実Credential、OS/Cloud権限を変更しません。

## 未教材Coverage

Credential lifecycle、Session、Federation、OAuth/OIDC、WebAuthn、MFA、ABAC、ReBAC、Capability、Policy administration、分散失効伝播、実製品相互運用は未教材です。この1単位をIdentity/Authentication/Authorization分野全体の完成とは扱いません。

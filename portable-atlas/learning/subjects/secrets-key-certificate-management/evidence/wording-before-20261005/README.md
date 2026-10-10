# Secrets・鍵・証明書管理の入口

このSubjectを学ぶ道筋を、Mac上の標準Pythonだけで実行する1教材から始めます。架空の公開dummy鍵の平文は秘密ではありません。実秘密、OS Keychain、実証明書、CA、外部Secrets、Dockerは扱いません。全97分野やこのSubject全体の完成を主張しません。

## 前提から仕組みへ

JSON、bytes、ハッシュの基礎を前提にします。共有鍵のHMACはメッセージの完全性・認証を検証し、内容を暗号化しません。鍵versionを含むJSONをcanonical化してMACを計算します。発行に使う鍵と検証を許可する鍵は異なる集合です。重複期間は新規発行をv2へ切り替え、v1を期限内だけ検証できます。失効後にはMACが正しくてもv1を拒否します。

この教材の段階・期限・token形式は独自モデルであり、標準tokenプロトコルではありません。固定時計 now=100、期限=110を使い、now >= expires で拒否します。verifyは入力→未知鍵→権限→MAC→期限の順に拒否を決定します。同時異常の優先順も教材の選択です。

## 実装して正常・境界・異常を比較

このディレクトリで実行します。依存追加は不要です。`-B`でbytecode書き込みを抑制します。

```sh
python3 -B run.py --phase initial --version v1
python3 -B run.py --phase overlap --version v1
python3 -B run.py --phase overlap --version v2
python3 -B run.py --phase revoked --version v1
python3 -B run.py --now 109
python3 -B run.py --now 110
python3 -B run.py --fault tamper
python3 -B run.py --fault unknown
python3 -B run.py --fault input
python3 -B check.py
python3 -B server.py
```

serverが印字する動的 `127.0.0.1` URLを開きます。停止はそのserverへCtrl-C。画面は [index.html](index.html)、実計算は [model.py](model.py)、CLIは [run.py](run.py)、HTTPは [server.py](server.py)。画面だけをfile URLで開くとAPIは動きません。

画面の学習順は **予想→操作→実測比較→原典/実装→答え** です。段階・version・時計・異常を操作し、実version、署名対象JSON、受信MAC、計算MAC、権限、結果を見比べます。初期のv2は未許可の異常例です。UIの試行は独立してtokenを再生成します。checkerのローテーション列は同じv1 tokenを初期→重複→失効へ引き継ぎ、v2発行と両鍵の検証も確認します。

[oracle.py](oracle.py) はmodelをimportしない固定権限・時間oracleです。暗号学的計算はRFC 4231 §4.2の固定テスト値で別に照合します。独立実装の暗号ライブラリ検証や形式的証明ではありません。[check.py](check.py) は144組合せ、入力拒否、連続ローテーション、RFC値、意図的な期限/失効の壊れたモデル2件との比較、原票の再計算一致、source/artifact digest、README/indexのローカルリンクと原典結合を検査します。

通常checkerはread-onlyです。原票更新は明示した `python3 -B check.py --record` のみ。原票は [evidence/run.json](evidence/run.json)、結合は [evidence/bindings.json](evidence/bindings.json)、画面QAは [evidence/ui-qa.json](evidence/ui-qa.json)。実行時刻・環境・input・raw traceおよびinput/rawのSHA256を保存し、固定モデル時計と実実行時刻を区別します。画面captureの保存状況も原票に記載し、再描画を実captureと呼びません。初回default sandboxのloopback bindとIABのfile URLは拒否されました。その履歴は evidence/ui-qa-initial-blocks.json に保存しています。同sessionの追加指示に基づき、exact server.pyの動的127.0.0.1 previewを通常承認審査へ1回かけ、承認後にHTTPで実IAB QAを実施しました。正常・重複・v2・失効・期限109/110・改ざん・未知鍵・不正token・API入力拒否の10ケース、title/fields、答え、roadmapを確認しました。実full-page JPEG captureは取得・tool表示・目視確認済みですが、moduleへ未保存です。再描画ではありません。captureファイルの永続保存は未検証です。自分のserverとtabは終了済み。file URLの再試行、別surfaceへの迂回、設定変更はありません。

## 実務判断へ

今回判断できるのは、旧tokenの最大寿命に合わせて検証猶予を設ける意味、発行と検証の切替を分ける理由、漏えい時の即時失効と互換性のトレードオフです。期限やversionもMACで保護し、鍵を検索できないときに別鍵へfallbackしない構成を観察できます。MAC一致は受理条件の一つにすぎません。

本モデルでは公開dummy鍵により誰でもMACを作れます。実務の認証安全性はありません。リプレイ、nonce、clock skew、耐障害配布、権限分離、安全な生成・保管・削除・監査を検証していません。HMACの共有鍵は検証者も発行可能で、非対称署名や証明書の信頼連鎖とは異なります。

## 未教材coverageと次の実験

| 主要概念・問い | 次の実験（全て未実装） | 公式locator |
| --- | --- | --- |
| 秘密配布、保管、最小権限、監査：誰が取得できるか？ | 架空ACLを使い取得成功/拒否と監査イベントを比較 | NIST SP 800-57 Part 1 Rev.5 §8 |
| 生成、cryptoperiod、バックアップ、破棄、侵害復旧：失効と削除は同じか？ | 架空状態機械で復旧可能性と破棄を比較 | 同 §5, §7–9 |
| 証明書の発行・信頼連鎖・名前・用途・期限・CRL/OCSP：署名一致だけで受理できるか？ | 架空チェーンのvalidation条件表で拒否を比較 | RFC 5280 §4–6、RFC 6960 §2 |
| 更新自動化、配布整合性、TLS、鍵種別：新鍵をいつ全検証器へ届けるか？ | 架空2検証器の配布遅延と切替事故を比較 | RFC 8446 §4.4、NIST §5 |

KMS/HSM、エンベロープ暗号化、OS Keychain、実CA/証明書更新、実秘密管理、監査保管、分散障害は未教材です。上の4実験は次の学習候補であり、今回着手しません。

## 原典

- [RFC 2104 §2](https://www.rfc-editor.org/rfc/rfc2104#section-2)：HMAC構成。実装 `issue` / `verify` の計算との対応。
- [RFC 4231 §4.2](https://www.rfc-editor.org/rfc/rfc4231#section-4.2)：HMAC-SHA256固定テスト値。`oracle.RFC_MAC`との対応。
- [Python hmac / compare_digest](https://docs.python.org/3/library/hmac.html#hmac.compare_digest)：stdlibと比較API。`verify`のMAC比較との対応。
- [NIST SP 800-57 Part 1 Rev.5](https://csrc.nist.gov/pubs/sp/800/57/pt1/r5/final)：鍵種別・状態・管理の全体像。未教材coverageへの対応。
- [RFC 5280 §6](https://www.rfc-editor.org/rfc/rfc5280#section-6)：証明書path validation（未実装）。
- [RFC 6960 §2](https://www.rfc-editor.org/rfc/rfc6960#section-2)：OCSP（未実装）。
- [RFC 8446 §4.4](https://www.rfc-editor.org/rfc/rfc8446#section-4.4)：TLS認証（未実装）。

一次資料locatorの確認日：2026-10-05。source bindingは参照先と教材の対応であり、外部ページ内容の完全ミラーではありません。

## Skillと検査範囲

[SKILL.md](skills/atlas-secrets-key-certificate-management/SKILL.md) はこの既存runner/checker/UIに限定してrouteします。正常routingと未対応routingは [evidence/routing-smoke.json](evidence/routing-smoke.json) に記録します。main-agentの読解・実行smokeであり独立forwardAgentEvalではありません。

本作業では対象module外の検査・編集は禁止されています。repo.yamlの全体検証 `npm run gate`、Core audit、repoctl admission verify は範囲が全体へ広がるため未実行です。moduleの成功をrepo全体のgate成功、commit可能性、全Subject完成と扱いません。

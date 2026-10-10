# chainが通れば接続先として受け入れてよいか

[第1単元](../../../subjects/secrets-key-certificate-management/README.md) の証明書validation未教材を深掘りする追加単元。第1単元の「MAC一致だけでは受理条件を満たさない」から、**実証明書のchain・名前・用途・期限**へ進む。元unitや97入口数は変えない。

## 予想から実務判断まで

1. 予想: 信頼CAが署名していてもSANがother.atlas.invalidなら、api.atlas.invalidとして受け入れてよいか。
2. 操作: [index.html](index.html) で正常、wrong SAN、untrusted CA、wrong EKU、固定期限の前/境界/後を選ぶ。
3. 比較: 実OpenSSLの名前＋用途あり、名前option省略、名前・用途省略の3コマンドと実fieldsを見る。
4. 原典/実装: [oracle.py](oracle.py) の事前condition table、[model.py](model.py) のCLI呼び出し、公式資料を照合する。
5. 答え/判断: 成功を読むときはtrust anchor、期待名、purpose、verification timeも確認する。offline成功だけでは実TLS相手や失効状態の証拠にならない。

## toolと実行

既存 `/opt/homebrew/opt/openssl@3/bin/openssl` の **OpenSSL 3.6.3** を確認し固定した。標準opensslはLibreSSL 3.3.6でverify helpにhostname optionがなく、採用しなかった。版やoptionが不足した環境では報告して失敗し、模型へ置換しない。install/upgradeはしていない。Python標準ライブラリだけ。

このディレクトリで:

```sh
python3 -B run.py --case normal
python3 -B run.py --case wrong-san
python3 -B run.py --case untrusted
python3 -B run.py --case wrong-eku
python3 -B run.py --case at-start
python3 -B run.py --case at-end
python3 -B run.py --mode tls
python3 -B check.py
python3 -B server.py
```

runnerは成功/証明書拒否ともJSONに実stdout/stderr/exitを返しexit0。未対応case/modeやtool不足はrunner exit2。verify自体は成功exit0、証明書拒否exit2。serverの所有temporary127.0.0.1 URLを開き、終了はCtrl-C。UIは開始時に前回結果を消す。実verifyがHTTP200、未対応入力HTTP400。

## dummy生成と固定条件

[generate.py](generate.py) で教材専用dummy EC P-256鍵を一時directoryへ生成し、Root A/Bと3leafを発行した。鍵は実資格情報ではなく、秘密鍵を教材成果へ残さず一時directoryごと除去した。残るのは [公開certs](certs/leaf-good.pem)、[profile](profiles/good.cnf) と [生成raw](evidence/generation.json)。本物資格情報は参照しない。CAfile指定は1コマンド内だけでOS trust storeやKeychainへ登録しない。

Rootのvalidityは2026-01-01〜2030-01-01 UTC、CA:TRUE、keyCertSign/cRLSign。leafは2026-10-05 00:00:00〜2026-10-06 00:00:00 UTC、CA:FALSE、digitalSignature。全leafをRoot Aが署名する。期待名はapi.atlas.invalid、purpose sslserver。wrong SANのCNはapi.atlas.invalidのまま、SANだけother.atlas.invalid。wrong EKUはSAN正常、clientAuthのみ。

各verifyは`-no-CAfile -no-CApath -no-CAstore -CAfile certs/root-{a,b}.pem -attime 固定epoch -x509_strict -check_ss_sig`。system trustを読み込まない。名前ありは`-verify_hostname api.atlas.invalid`、用途ありは`-purpose sslserver`を加える。「名前・用途省略」も署名だけの検査ではなく、chain/時刻等は検査する。

## 実測と独立期待

[oracle.py](oracle.py) は生成前に書いたleaf/anchor/timeと4条件の手表。実CLIの結果やfieldsをimportして期待値へ変換しない。checkerは実SAN/EKU/basicConstraints/keyUsage/issuer/datesと、9ケース×3実verifyのstdout/stderr/exit・error番号を照合する。

| ケース | 名前＋用途 | 名前省略 | 名前・用途省略 | 実務判断 |
|---|---|---|---|---|
| 正常 | OK | OK | OK | 指定条件内のoffline成功 |
| wrong SAN | error62 | OK | OK | chain OKは期待名一致を代替しない |
| untrusted CA | error20 | 拒否 | 拒否 | 別のCAfileではissuerへ到達できない |
| clientAuthのみ | error26 | 拒否 | OK | 名前一致だけでserverAuth用途を満たさない |
| notBefore−1秒 | error9 | 拒否 | 拒否 | まだ有効ではない |
| notBeforeちょうど | OK | OK | OK | 3.6.3で開始境界を実確認 |
| notAfter−1秒 | OK | OK | OK | 期限直前 |
| notAfterちょうど / +1秒 | error10 | 拒否 | 拒否 | 3.6.3で期限境界を実確認 |

**期限境界の注意**: RFC 5280 §4.1.2.5はnotAfterまでinclusiveと記述する。一方、今回のOpenSSL 3.6.3 CLIはnotAfterちょうどをexpiredと返した。これは固定toolの実測として記録し、他validatorやRFC全体の適合性へ一般化しない。[OpenSSL time比較](https://docs.openssl.org/3.6/man3/X509_cmp_time/) はequal時の比較戻り値も説明する。

## 原票・再現・検査範囲

[evidence/run.json](evidence/run.json) に実UTC時刻/環境、tool probe、固定検証時刻、実fields、全argv/stdout/stderr/exit、input/raw digest、独立表を保存。[bindings](evidence/bindings.json) がsource/artifact SHA256とlocatorを結ぶ。[UI QA](evidence/ui-qa.json) は実IAB操作、capture保存可否、所有server/process/tabの終了。[Skill](skills/atlas-certificate-chain-name-purpose/SKILL.md) と [routing smoke](evidence/routing-smoke.json) は既存コマンドへの限定route。独立forwardAgentEvalは未実行。

通常checkerはread-onlyで同じ公開certを再verifyする。`check.py --record` だけが原票更新。初回は未生成evidence linkだけbootstrap許容。dummy再生成を明示した場合だけ `python3 -B generate.py`。ランダムな鍵と署名によりcert digestが変わるので、再生成後は原票とQAを再検証する。通常checker/runner/UIはgenerateしない。

実TLS接続、秘密鍵所持証明、CRL/OCSP、browser policy、OS trust変更は未実行。中間CAや複雑なpathも扱わない。root/leaf 2段の有限検証。実CA管理、安全な鍵保管、証明書policy適合や全Subject完成を主張しない。Core audit/npm gateは専用path scope外で未実行。新Goalは作成しない。

## 今回coverage増分と次の実験

今回、第1単元の証明書validation未教材のうち、実chain/SAN名/EKU用途/固定期限とoption省略の誤解を解消する入口を追加した。

| 残る問い | 次の実験 | 原典 |
|---|---|---|
| 失効、stale/missing応答、hard/soft fail | dummy CRLとoffline OCSP応答で失効/不明/期限切れ比較 | [RFC 6960](https://www.rfc-editor.org/rfc/rfc6960.html) |
| 更新配布がずれたときどの検証器が拒否するか | 2つの合成trust bundleでCA移行の重複/撤去とleaf更新比較 | [RFC 5280 §6](https://www.rfc-editor.org/rfc/rfc5280.html) |
| offline OKでも実TLS/browserが拒否する条件 | 承認したlocal TLSで秘密鍵所持・SNI/ALPN・chain送信を検証しpolicy差を整理 | [RFC 8446 §4.4](https://www.rfc-editor.org/rfc/rfc8446.html) |

以上は未実行。wildcard/IP-ID、name constraints、intermediate、失効やbrowser実policyも残る。

## 原典

- [OpenSSL verification options](https://docs.openssl.org/3.6/man1/openssl-verification-options/): 明示trust、hostname、purpose、時刻とstrict検査。
- [RFC 9525](https://www.rfc-editor.org/rfc/rfc9525.html): reference identifierとSAN、CNとの区別。
- [RFC 5280](https://www.rfc-editor.org/rfc/rfc5280.html): §4.1.2.5 validity、§4.2.1.12 EKU、§6 path validation。
- [X509_cmp_time](https://docs.openssl.org/3.6/man3/X509_cmp_time/): 実toolのtime比較境界と対応。

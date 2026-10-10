# Atlas｜内容が同じなら、来歴の申告も許可できる？

目標51と元LEARNING_PATH実験1の有限契約です。digest一致・独立baseline・推移materialは既存教材を前提とし、今回は別保持したbuilder/source/buildType/parameterの期待と、受信bundle内のpolicyを区別します。producer・対象計算・GUIは未実装／未実施です。

## 固定入力と比較

artifactはASCII `abc` の3byteで全7条件共通です。SHA-256の手固定値は `ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad`。JSONは独自教材形式で、SLSA attestationではありません。URIは例示用の文字列でありアクセスしません。

`consumer-policy.json` は別保持の期待です。builderは `https://builder.example.invalid/release/v1`、sourceは `https://source.example.invalid/atlas/demo`、buildTypeは `https://build.example.invalid/archive/v1`、parametersはmode=release / target=arm64です。期待fixtureを選び保護する工程と、そのwriterの権限は仮定です。固定policyを受信claimsから生成しません。

正常版はartifact bytes・claims・別保持policyを引数として受け取り、bundle内のproposed_policyを読みません。故障版だけが同じ比較規則の期待へproposed_policyを渡します。digest照合の成功を来歴policyの成功へ流用せず、各項目を別に保存します。

比較はartifact digest、builder ID、source ID、buildType、parameter key集合、parameter値の6項目です。ID/値はcase-sensitiveの文字列完全一致で、URL正規化・正規表現・包含推論をしません。parameter key集合は順不同で完全一致。parameter値は期待側の全keyが存在し値が一致することを求め、未知key追加では集合だけ不一致、既知keyの値照合は一致として記録します。単なる最初の不一致で打切らず、全6項目と全体のANDを保存します。

固定7条件はcases.jsonとexpected.jsonに明示します。正常、別builder、別source、別buildType、mode=debug、未知skipTests=true（文字列）、別builder＋proposed_policyもそのbuilderへ変更です。最後と別builder条件のclaimsは同一です。正常版は同じ拒否を返し、故障版は同梱policyを信じた最後の条件だけを一致扱いへ変えます。

## 成否と認証の境界

出力のclaimsMatchPolicyは、この文字列と集合の比較結果だけです。全件 `signatureCheck=not-run`、`authenticatedBuilder=null`、`releaseDecision=out-of-scope` を維持します。未知builderという不一致も、悪意や署名失敗の証明ではありません。文字列が許可builderと一致しても、実際の生成者は認証していません。

7条件は構造が正しい小入力です。今後のproducerで使うschemaは固定top-level keys、claims/policyの4keys、IDは非空string、parametersはstring→string辞書とし、範囲外の構造は比較結果payloadを出さず拒否します。全schema境界の実測は今回7条件に含めません。重複JSON key等のparse仕様をSLSA一般規約にしません。

署名検証・鍵・失効・透明性log・本物のbuilder認証・実build・依存解決・policy更新承認・SLSA level/形式適合・安全なreleaseの保証は範囲外です。SLSAの一般的な拡張field処理規則と、ここで限定する独自JSON schemaを混同しません。

## 受入と読む順

実装前に別担当がliteral手表を保存し、producerを共有しない照合で6項目／7条件の結果とclaims同一対照を確かめます。許可後の実行では入力前後不変・実装/入力/期待/結果のSHA・実優先度と時間上限を記録します。現在は契約と手表だけで、対象実行を開始しません。

画面は予想→保存結果→別policy／同梱policyの対照→原典／実装→答え→限界の順にします。認証未検証を常時明示し、予想変更・reset・欠落/改変/古い応答では旧答えを消します。Skillの有限3例は、(1) checksum一致だがbuilder不一致、(2) 同梱policy差替えでも別保持の期待は変わらない、(3) claims一致から署名済みを結論しない、です。一般Agent評価にはしません。

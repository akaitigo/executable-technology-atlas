# Atlas：本文のstatusで、HTTP状態を置き換えてよいか

目標26の「エラー形式・通信状態・業務結果を分けて判断する」に対応する。[固定6入力](cases.json)と、そのUTF-8 JSONファイルの全byteを先に固定する。今回の実行対象は合成応答を受け取るPython関数であり、HTTP受信やサーバー動作の測定ではない。旧API教材の200/422・独自エラー・再送を前提として使い、再制作しない。

## 入力と対象範囲

- transportStatusは全6件で整数422。これは固定した伝送状態の入力で、ネットワークで観測した値ではない。
- mediaTypeは完全一致の `application/json` または `application/problem+json` だけ。大文字小文字の一般則、parameter、複数値、Content Negotiationは扱わない。
- bodyは1024 byte以内の正しいUTF-8 JSON object。末尾改行も固定byteに含む。一般のJSON Schema検証器ではない。
- customは `error.code/message` が非空stringの旧契約。独自形式も有効な契約であり、Problem Detailsに劣るとしない。
- Problemの今回のtypeは同じ絶対URI `https://api.example.invalid/problems/invalid-quantity`。titleだけを翻訳した条件を含む。URIは識別子として使い、自動取得しない。相対URI解決や任意URIの検証は範囲外。
- statusの対象はJSON数値200/422、省略、文字列`"422"`。型判定でPython boolをnumber扱いしない。標準memberの型が違う場合は、そのmemberを無視する。type欠落時のabout:blank等を実装上補助しても、今回未測定の分岐まで網羅済みとしない。

## 共通の読み方と二つの方針

まず媒体から形式を選び、標準memberの扱いを記録する。Problemのstatusが省略または型違いならbodyStatus=nullとし、後者だけignoredMembersにstatusを残す。unknown extensionは無視し、名前をignoredExtensionsへ記録する。type URIが問題の主識別子で、titleの翻訳とextensionの追加で別typeにしない。

「保留する版」は、型が合うbodyStatusとtransportStatusが違えばdecision=hold、chosenStatusはtransportStatusのままにする。それ以外はchosenStatusの2xxをsuccess、4xx/5xxをbusiness-errorへ分類する。「本文を優先する版」は不一致でもbodyStatusをchosenStatusに採用する故障対照であり、HTTPfixtureそのものは書換えない。customでは両版ともtransportStatusを使う。**この不一致保留は教材consumerの方針であり、RFCがすべてのconsumerへ課す拒否義務ではない。**

business-error/successはこの6固定fixtureに対する分類ラベルであり、一般のHTTP状態だけから実際の業務結果を確定しない。hold時のchosenStatus=422はHTTP側の候補値を保持する記録で、処理へ採用したことを意味しない。共通表示欄titleにはcustomのerror.messageを写すが、これはProblem Detailsのtitle memberではなく、この教材の正規化規約である。

RFC 9457ではstatusはadvisoryで、生成者は実HTTP応答と同じ値を使う義務がある。ただし受信時の不一致だけから生成者の誤りと断定しない。intermediaryが状態を書換えた可能性はあるが、今回その過程は観測していない。故障対照のsuccessも業務処理の成功を証明しない。

## 保存する判断と手期待

各応答の全入力前後・body byte SHA、形式、transportStatus、bodyStatus、statusRelation、chosenStatus、problemType、title、customCode、ignoredMembers/Extensions、decision/reasonを両方の方針で保存する。返却内容にURI取得や副作用はなく、入力は不変。[作者手表](expected.json)と独立担当の先行literal表へ全応答を照合する。

| 条件 | statusRelation | 保留する版 | 本文を優先する版 |
|---|---|---|---|
| 独自422 | not-applicable | 422 / business-error | 同じ |
| Problem422/422 | match | 422 / business-error | 同じ |
| status省略 | absent | 422 / business-error | 同じ |
| 伝送422・本文200 | mismatch | 422 / hold | 200 / success |
| statusが文字列 | ignored-type | 422 / business-error | 同じ |
| title翻訳＋未知extension | match | 422 / business-error、typeは同じ | 同じ |

入力schemaの拒否は安全な失敗経路として設けるが、この6件はすべて構文上受理する。型違いstatusは応答全体の拒否ではない。ネットワーク欠落・画面取得失敗はこの関数入力拒否と別に確認する。一般のHTTP/RFC適合性、認証、再試行安全性、現実の業務結果は保証しない。

## 実行と受入

作者/独立手期待を実装前に固定する。対象計算はrootの今回の観測・個別枠を根拠に、既存Python stdlibの単一子だけ、actual nice≥10・wall15秒・retry0・回収を条件にする。GUIはrootが維持する既存pageを使う保存readerで、模型再実行ではない。6条件全値、予想/条件/reset、欠落・改変・旧応答による結果消去、1280/390の実viewport、前提/原典/実装/Skillを有限受入とする。新サービス・認証・OS設定変更・共有元編集・公開は行わない。

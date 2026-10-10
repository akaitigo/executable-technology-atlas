# Hamming(7,4)：訂正後の0は元の情報を保証するか

4bitのmessageへ3個のparity bitを付け、1bit誤りの位置をsyndromeから求める有限教材。Python標準ライブラリだけで演算し、日本語UIで予測・操作・比較する。教材の完成と情報理論全体のCoverage完了は別。

## 操作する

このフォルダで実行する。外部依存・SDK・Dockerは不要。

```sh
/usr/bin/python3 -B lesson.py --port 18748
```

`http://127.0.0.1:18748`を開く。別terminalからの検査は`/usr/bin/python3 -B verify.py`。終了はserverのterminalでCtrl+C。ループバックのみで公開しない。

他の担当者と同じhostを使う場合は`--port 0`で動的割当し、stdoutのURLを開く。HTTP記録には`verify.py --record-http --port 実際のport`を渡す。使用中portの既存processを終了しない。

1. 「1bit・data」を選び、元messageへ戻るか予測する。
2. 実行し、parity checkとsyndrome、反転位置を確かめる。messageや位置も編集できる。
3. 「誤りなし」「1bit・parity」と比較する。
4. 「2bit反例」を予測して実行。syndromeの0と回復成功を区別する。
5. 一次資料、独立行列、答えを開き、なぜdecoderが誤訂正したか説明する。

入力変更時は古い結果を非表示にする。非binary、誤り位置の範囲外・重複・3個以上などは拒否し、正常入力へ戻すと再計算できる。

## 観測と規約

位置1〜7は左から右。`p1 p2 d1 p4 d2 d3 d4`、偶数parity。syndromeの数値は`s1 + 2s2 + 4s4`、表示bit順は`s4 s2 s1`。これをbig-endianなmessageの数値解釈と混同しない。

| 入力 | 受信語 | syndrome / decoder反転 | 復号 | 比較結果 |
|---|---|---|---|---|
| `1011`、誤りなし | `0110011` | `000=0` / なし | `1011` | 一致 |
| `1011`、位置6 | `0110001` | `110=6` / 6 | `1011` | 一致 |
| `0000`、位置1・2 | `1100000` | `011=3` / 3 | `1000` | **不一致** |

最後のdecoder後は`1110000`でpost-syndromeは0。原符号語から距離3の別符号語になっている。decoderは受信語のみを使い、原messageや誤り数を知らない。「不一致」は送信側を知る実験harnessが行う答え合わせで、2bit検出機能ではない。SECDEDの追加parityは実装していない。

[lesson.py](lesson.py)はXOR式と位置maskで演算。[oracle.py](oracle.py)は別のliteral G/HのGF(2)行列積と16符号語の最短距離列挙を使い、production encoder/decoderをimportしない。[test_lesson.py](test_lesson.py)は16誤りなし、16×7=112単一bit、128受信語、G/H直交、最小距離3、2bit反例、拒否→回復を検査する。試験は deterministic synthetic channelであり、通信機器やランダムchannelの実測ではない。

## 再現記録

```sh
/usr/bin/python3 -B lesson.py --record
/usr/bin/python3 -B verify.py --record-checks
# serverを起動した場合だけ
/usr/bin/python3 -B verify.py --record-http
```

`verify.py`既定動作はread-only。記録は明示`--record-*`だけ。`--record-media`は実IAB画像とDOM観測を採取済みの場合だけ使う。`--record-readonly`は別processの既定checkerの前後file digestを比較して記録する。

- [Python保存観測](observations/python.json)：時刻、環境、入力、syndrome、反転、復号、oracle、source SHA-256。
- [生stdout](observations/stdout.txt)、[試験ログ](observations/tests.txt)、[試験binding](observations/checks.json)。
- [実HTTP](observations/http.json)、[実UI DOM](observations/ui-dom.json)、[画像の寸法・digest](observations/media.json)、[read-only観測](observations/readonly.json)。
- [Skill](skills/atlas-information-theory-coding/SKILL.md)、[ローカルrouting review](observations/skill-review.md)。独立Agent Evalではない。

実画面は`media/`のJPEG。背景IAB desktopで、誤りなし、単一data、単一parity、2bit反例、不正入力、回復を操作。browser engineの版はツールに公開されず不明。mobile、動画、別OSのQAは未実行。

## 一次資料

- [MIT 6.02 Chapter 6](https://ocw.mit.edu/courses/6-02-introduction-to-eecs-ii-digital-communication-systems-fall-2012/resources/mit6_02f12_chap06/)（2012-09-23更新）：§6.1、§6.3、式6.1/6.10/6.12。Gによる符号化、Hによる検査とsingle-error保証を確認した。教材は列をposition順へ並べ替え、parity誤りも反転する。
- [R. W. Hamming, Error Detecting and Error Correcting Codes](https://doi.org/10.1002/j.1538-7305.1950.tb00463.x)（Bell System Technical Journal 29, 147–160, 1950）：書誌の確認。全文は今回取得できていない。
- [取得状況](observations/source-access.md)。第三者本文やPDFはこのフォルダへ複製していない。式から実装した独自教材。

## 対象範囲

| 分野内の項目 | 状態 | 次の条件 |
|---|---|---|
| Hamming(7,4)偶数parity / syndrome / 単一bit訂正 | この教材で実装・実行 | 他のbit順へ移すならG/Hを明記 |
| 2bit誤訂正境界 | 特定反例を実行 | 全2bit組合せを検証済みとは主張しない |
| SECDED | 未実装 | 8bitの全体parityと検出/訂正の状態遷移 |
| CRC、burst、interleaving | 未実装 | 別の誤りmodelと検出oracle |
| Reed–Solomon / BCH / LDPC / convolutional code | 未実装 | 各方式固有の実装と復号境界 |
| entropy、source coding、圧縮 | 未実装 | 分布と圧縮率の別教材 |
| channel capacity、物理通信 | 未実装 | channel仮定と実測の分離 |

この範囲表を空欄のArtifactや他教材の結果で埋めない。Portalのroot文書・既存Atlas契約・公開設定はこの教材で変更しない。

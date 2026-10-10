# Information theory / codingを学ぶ道筋

この文書は[Hamming(7,4)の既存教材](README.md)から、符号の保証範囲、検出、source codingへ進むための補足です。有限教材の補足であり、分野全体の学習完了を示しません。次実験は全て未実行です。

## 1. 前提と主要概念

bit列、XOR、GF(2)の行列積、Hamming距離、確率と期待値を順に学びます。学ぶ流れは **messageとcodeword → G/Hとsyndrome → 最小距離と保証 → channelの誤りmodel → 検出・再送・訂正 → entropyとsource coding → capacity・高度な復号** です。

source codingは表現を短くする問い、channel codingは冗長性で誤りに備える問いです。syndromeは検査式への違反を表し、原messageとの一致は受信者が知らない送信側の答え合わせです。最小距離3の符号で単一bit訂正を期待しても、二重誤りへの同じ保証は得られません。

既存の位置順は左から `p1 p2 d1 p4 d2 d3 d4`、偶数parity、syndrome数値は `s1+2s2+4s4` です。原典の列順をそのまま混ぜず、同じ位置規約でG/Hを読むことから始めます。

## 2. 予想から既存実測へ

[UI](index.html)、[実装](lesson.py)、[独立行列Oracle](oracle.py)、[Python原票](observations/python.json)、[試験binding](observations/checks.json)、[UI観測](observations/ui-dom.json)を読みます。今回は演算・試験・UIを再実行していません。

| 条件 | 保存済み結果 | 説明できること |
|---|---|---|
| 1011、誤りなし | 0110011、syndrome 0、1011回復 | 正常符号語 |
| 1011、位置6反転 | syndrome 6、位置6を反転、1011回復 | 単一data誤りの訂正 |
| 1011、位置2反転 | parity位置を反転して回復 | parity側も単一bit保証の対象 |
| 0000、位置1・2反転 | 1100000→1110000、復号1000、post-syndrome 0 | 正しい符号語へ誤訂正する反例 |
| 不正入力 | 10入力を拒否 | binary長・位置・重複等の有限入力契約 |

原票には16 messageの誤りなしと112単一bit条件があります。保存試験は128受信語、G/H直交、最小距離3も検査しています。二重誤りは上記特定反例であり、全二重誤りの実行済み記録とはしません。decoderは受信語だけで動きます。「post-syndromeが0なら元へ戻った」という予想が外れる理由を、別符号語までの距離から説明します。

CPython 3.9.6による合成bit反転です。実通信機器、ランダムchannelのBER、SECDED、CRCの実測ではありません。既存UI操作はPython経路を使いますが、今回閲覧した保存記録と新規UI実行は区別します。

## 3. 実務で何を判断するか

誤りが独立かburstか、block長、冗長性、遅延、検出時の再送可否を先に定めます。訂正成功率、検出率、誤訂正率を別に測り、harnessの正解を受信器の検出機能へ取り込まないことが必要です。CRCは悪意ある変更の認証を担うMAC・署名とは役割が違います。

圧縮率は分布、headerや辞書、有限長の費用を含めて判断します。有限の符号例や分布の計算からchannel capacityの達成や製品性能を結論しません。

## 4. 一次資料への道筋

| 原典とlocator | 読む目的 |
|---|---|
| [MIT 6.02 Fall 2012 Chapter 6](https://ocw.mit.edu/courses/6-02-introduction-to-eecs-ii-digital-communication-systems-fall-2012/resources/mit6_02f12_chap06/)、§6.1 / §6.3 / 章末問題2 | G/H、単一bit保証、全体parity追加への入口 |
| 同Chapter 6、§6.5 / §6.6 | burstとCRCの検出境界 |
| [MIT Chapter 2](https://ocw.mit.edu/courses/6-02-introduction-to-eecs-ii-digital-communication-systems-fall-2012/resources/mit6_02f12_chap02/)、Entropyの節 | 分布から情報量を考える |
| [MIT Chapter 3](https://ocw.mit.edu/courses/6-02-introduction-to-eecs-ii-digital-communication-systems-fall-2012/resources/mit6_02f12_chap03/)、§3.2 Huffman Codes | prefix codeと平均符号長 |
| [Hamming 1950 DOI](https://doi.org/10.1002/j.1538-7305.1950.tb00463.x) | 歴史的原論文の書誌。全文確認済み根拠ではない |

## 5. 未教材と次の問い

| 未教材 | 問いと次の入口 |
|---|---|
| 全二重誤り・保証外の分類 | 元message比較とdecoderの判断を分離できるか。実験1 |
| SECDED | 全体parityで二重誤りをどう拒否するか。実験2 |
| CRC・burst・interleaving | 検出しない誤りpatternは何か。実験3、interleavingは別途未実装 |
| entropy・Huffman・圧縮 | 分布が変わると平均長はどう変わるか。実験4 |
| LZW・arithmetic coding・相関source | 辞書や文脈の費用をどう扱うか。別教材が必要 |
| BCH / Reed–Solomon / LDPC / convolutional・Viterbi | hard/soft decisionと復号境界は何か。方式固有の原典と実証が必要 |
| capacity・noise・物理通信 | channel仮定と測定をどう接続するか。現教材では未評価 |

## 6. 次の実験案（4本、全て未実行）

1. **二重誤りを全列挙する。** 16 message×21位置対を別fixtureで列挙し、訂正前後syndrome、選んだ符号語、message一致を保存します。予想は単一bitを仮定したdecoderが別符号語へ向かうことです。独立G/Hと16符号語への距離表をOracleにし、harnessだけが持つ送信情報をdecoderへ渡しません。原典はChapter 6 §6.3。現在の特定反例を全組合せ確認済みに読み替えない案です。

2. **8bit全体parityのSECDEDを別実装で比較する。** 位置8に全体偶数parityを足し、syndromeと全体parityから「無誤り・1〜7訂正・位置8訂正・二重誤り拒否」を分けます。16 messageの0/1/2bit条件を手書き状態表と独立8bit符号語距離へ照合します。予想は二重誤りを訂正せず拒否することです。Chapter 6章末問題2が距離の入口です。3bit以上や実hardware ECCの保証は別条件で、既存7bit教材を変更する案ではありません。

3. **小さなCRCの検出限界を列挙する。** 独自規約でMSB順、初期値0、反転・最終XORなし、g(x)=x³+x+1と4bit messageを固定します。多項式長除算と独立の倍数集合を照合し、全7bit誤りmaskの剰余を記録します。予想は非零でもgの倍数なら未検出になることです。単一bitと短いburstも分け、CRC合格を訂正成功・送信者認証にしません。原典はChapter 6 §6.6。製品CRC profileへの適合は未実証です。

4. **分布とprefix符号の平均長を比べる。** 架空4記号の一様分布と確率1/2,1/4,1/8,1/8を使い、固定2bitとHuffman符号を比較します。手書きtree・prefix性・往復復号・確率加重平均長・entropyを別照合し、短いmessageの辞書/header費用も分けます。予想は偏った分布で平均長が短くなることです。原典はChapter 2とChapter 3 §3.2。有限文字列の圧縮成功をcapacity達成へ拡張しません。

## 7. 資料取得と検証状況

2026-10-05にMIT Chapter 2/3/6のresource pageとPDF本文を取得しました。Hamming原論文は今回再取得せず、[既存取得記録](observations/source-access.md)の書誌確認・全文取得不能を保持します。既存のYale timeout、CMU取得不可を今回の成功で消しません。第三者本文・図は保存していません。

追加はこの文書だけです。runtime、checker、server、UI、global gateを実行せず、旧原票・画像・QA・digestを更新していません。次実験の予想は新たな実測ではありません。

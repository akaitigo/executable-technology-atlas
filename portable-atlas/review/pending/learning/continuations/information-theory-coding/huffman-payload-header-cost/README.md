# Huffmanの平均payloadとheader込み費用

元[Information theory / coding実験4](../../../subjects/information-theory-coding/LEARNING_PATH.md)を、架空ABCDの有限実験として実装した候補です。分野全体・Atlas全体のcompleteではなく、中央受入待ちです。

予想→JSON条件→実Python encode/decode→図と手表→答え→原典の順に進みます。まずskew-shortで「Huffmanなら小さい」と予想し、payloadだけの短縮をtotalの短縮と取り違えた理由を説明します。「messageを5倍にして比較」で分布を固定したまま長さを変えます。次にuniformとmismatchを比較してください。

## 先に固定した規約

alphabetは順序付きABCD、方式は両側で共有済みです。weightsは正整数1..16を4個、確率は総和で正規化します。messageはABCDだけ0..255記号、未知記号・bool/zero weight・未対応header等はexit2で拒否します。空messageは符号化可能、payload0、実payload平均は未定義です。model平均は空入力でも定義されます。

木は最小weightの2つをmerge。同weightは木内の最小alphabet index、その次はcreation idです。葉の深さをcode長とし、同じ長さを保って長さ→alphabet順にcanonical codeを割り当てます。tree由来の枝bitとcanonical bitが同じとは一般には限りません。canonical化後もprefix性と加重平均長は保持されます。

独自header `canonical-lengths-2bit-plus-u8-count-v1` はHuffmanで **16bit**（u8記号数＋ABCDの各code長−1を2bitずつ）、固定2bit方式で **8bit**（u8記号数）です。4正weightの完全二分木ではcode長1..3のみ、field11（長4）は拒否。固定codebookはA00/B01/C10/D11、Huffmanはheaderからcanonical codebookを再構築します。weightsと原messageは受信側へ送りません。共通alphabet・方式の選択費用、byte padding・container・framingは計上していないbit単位の教材規約で、標準file formatへの適合は主張しません。

receiverの復号APIは **codebook・bitstream・countのみ**。余分なbit、切れたprefix、count不一致、不正book/headerを拒否します。原messageとの一致は送信側harnessの答え合わせであり、receiverが知る正解ではありません。誤り訂正符号や認証機能はありません。

完全性の有限反例は、headerを固定したままpayloadの末尾を反転する `00001010110111 → 00001010110110` です。receiverは後者も8記号 `AAAABBCC` として有効に復号します。送信原文 `AAAABBCD` との不一致はharnessだけが検出できます。prefix性や正しい長さはbit破損の完全性検出保証ではありません。

## 手計算と判断

| model / message | L / H (bit/記号) | Huffman / 固定payload | header込みtotal | 判断 |
|---|---|---|---|---|
| [4,2,1,1] / AAAABBCD | 7/4 / 7/4 | 14 / 16 | 30 / 24 | payload短縮でもtotal増 |
| 同message×4（32記号） | 同上 | 56 / 64 | 72 / 72 | break-even |
| 同message×5（40記号） | 同上 | 70 / 80 | 86 / 88 | total2bit短縮 |
| 一様 / AAAABBCD | 2 / 2 | 16 / 16 | 32 / 24 | header分増 |
| [4,2,1,1] / CDCD | 7/4 / 7/4 | 12 / 8 | 28 / 16 | 実payload平均3、model平均とは別 |
| [4,2,1,1] / 空 | 7/4 / 7/4 | 0 / 0 | 16 / 8 | 実平均未定義 |

skew木はC1+D1→CD2、B2+CD2→BCD4、A4+BCD4→ABCD8。canonical A0/B10/C110/D111です。L=(4×1+2×2+1×3+1×3)/8=7/4。H=1/2×1+1/4×2+1/8×3+1/8×3=7/4。一様木はAB2/CD2からroot4、全code長2。手表をproducerより前に固定したSHAと時刻は`qa/oracle-before-producer.json`です。

同じ8記号blockをk回繰り返すとHuffman total=16+14k、固定=8+16k、差=8−2k。k=4で等しく、k≥5で短縮します。任意messageにn>32という普遍的な閾値を適用しません。別の記号割合では実payload費用が変わります。

故障版はpayloadだけを比べ「短縮」と宣言します。shortの14<16は事実でも30>24を無視するため誤判定、break-evenでもstrictなtotal短縮はありません。UIと独立checkerは数値からこの故障を検出します。

## 実行と証拠

標準Python libraryだけで実行します。外部依存・実データ・製品codecは使いません。

```sh
python3 -B checker.py
python3 -B runner.py
python3 -B route.py
python3 -B server.py
```

`checker.py`はproducerをimportせず、長さ1..3のKraft等号を満たす全13割当を列挙して最小加重費用へ照合します。4葉のfull treeは(2,2,2,2)または(1,2,3,3)の置換だけ。正weightでは単一子を縮めれば平均費用が下がるため、最適な単一記号binary prefix木はfullです。これは有限4記号の平均payloadについてのoracleで、一般圧縮器やheader込みの最適性ではありません。entropyは独立式で許容差1e−12、平均・費用は整数/Fractionで照合します。12故障をrejectします。

通常checker/runnerは全unitファイルのSHA256とmtime_nsを前後比較して書込みがないことを確認します。明示`runner.py --record`だけが新UTCフォルダに原票とcalculate/hand/contracts/expectedを排他保存し、固定pointerを更新します。旧原票は保持します。

serverは127.0.0.1の動的portでmemory-only、GET/POST/start/receipt exportでファイルを書きません。UIは固定結果を再表示する代わりに実JSONをPython childへ渡し、stdout/stderr/exitとsource SHAを持つmemory原票へリンクします。RAMは最大512原票、停止で消えます。QAの600ms遅延はstale-response検査用で、処理速度の測定ではありません。保存はQA担当の明示exportです。再起動は古いmemoryリンクを復活させません。

UIのJSON・予想・scenario・reset変更は図・表・モデル・答え・raw hrefを即時clearし、旧revision応答を無視します。入力拒否と通信失敗には正常の図/答えを残しません。`view/*`は固定allowlistだけをescaped text表示します。

## 原典と次の問い

[MIT Chapter 2 PDF](https://ocw.mit.edu/courses/6-02-introduction-to-eecs-ii-digital-communication-systems-fall-2012/4bcb4b872e8e98459ce71e77d4fe9c42_MIT6_02F12_chap02.pdf) §2.1.3 pp10–11 / §2.2 pp11–13: entropyは分布の期待情報量、可変codeの実長は記号列にも依存します。[MIT Chapter 3 PDF](https://ocw.mit.edu/courses/6-02-introduction-to-eecs-ii-digital-communication-systems-fall-2012/95605227801c1ef2e1b6ddfd8da7a8a2_MIT6_02F12_chap03.pdf) §3.1 pp20–21 / §3.2 pp21–25: prefix木・加重平均・最小weight mergeと、単一記号/既知固定分布の最適性が入口です。2026-10-06 JSTにresource pageとPDF本文を閲覧。第三者本文・図は保存せず、数値・図は本教材独自の合成例です。

次は相関source、block coding、adaptive辞書・arithmetic codingのmodel伝達費用を別条件で問います。[未教材](COVERAGE.md)と[有限Skill](skills/atlas-huffman-payload-header-cost/SKILL.md)を先に読み、標準codec性能、capacity達成、物理通信へ結果を拡張しません。

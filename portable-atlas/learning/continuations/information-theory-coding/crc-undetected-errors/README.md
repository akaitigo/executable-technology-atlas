# 小さいCRC：剰余0でも原文は変わる

元の[Hamming(7,4)教材](../../../subjects/information-theory-coding/README.md)と[学習経路・実験3](../../../subjects/information-theory-coding/LEARNING_PATH.md)を深掘りする有限unit。訂正後の検査式0の限界から、CRCの検出限界へ進みます。元Source/raw/coverage/QAはread-only。入口追加0、全分野網羅0、Subject/Atlasはincompleteです。

## 前提 → 予想 → 実操作

bit、XOR、GF(2)の係数、次数が前提。[contract.json](contract.json)にMSB順、4bit message+3bit CRC、g=x³+x+1（1011）、初期0、input/output反転なし、final XOR0を固定。製品CRCではない独自規約です。左4bitはpayload、右3bitはCRC。

```sh
node serve.mjs
```

既存Nodeのstdlibだけで起動。動的127.0.0.1 URLを開き、所有serverだけCtrl+Cで終了。利用用serverには触れません。

1. 「剰余0でもpayloadが変わる？」を予想し、未検出反例を選ぶ。
2. 新しい実行→次のXOR位置を順に押す。送信と受信のbefore/aligned g/after、codeword/mask/receivedを追う。
3. 最後の受信判定と、元messageを知るharnessの答え合わせを別に読む。
4. 誤りなし、単一payload bit、単一CRC bit、内部0のspan3、shiftしたg倍数を比較。
5. 非binary message、8bit maskは入力契約で拒否。正常例へ戻すと古い結果を消し、新しい実行で回復する。message/maskを直接編集しても再実行まで古い結果を使わない。
6. 原典locator、実装、全原票を読み、答えと実務判断へ進む。

UIは操作時に[実JS符号化と受信検査](crc.mjs)を実行し、全4位置の長除算traceを生成してステップ表示します。実時間の進行モデルではありません。受信器の引数はreceived7bitだけ。原messageもmaskも渡さず、原文一致はharnessだけの比較です。

## 何が検出でき、何が分からないか

codeword0000000へmask0001011をXORするとreceived0001011、受信payload0001、remainder000。検査式に違反はありませんが元0000と不一致です。**CRC passは原文一致・訂正成功・送信者認証ではありません。** 受信器が元messageを知っているような表示をしません。

[独立oracle](oracle.mjs)はproducer長除算をimportせず、GF(2)係数convolutionで4bit商×gの7bit倍数16個を生成。payloadに対応する唯一の符号語、倍数集合と8剰余cosetから期待値を求めます。traceは別のbitごとのXOR式で照合。数学的な有限モデルであり実通信の観測ではありません。

全16message×128mask＝2048条件。各messageについて非零127maskは未検出15・検出112。単一bit7個、span≤3の23個は全検出。span=最上位1−最下位1+1、内部0あり、単一bitのspan1もこの集合に含めます。教材のburst集合は原典の最小burst長2の用語に、単一bitも加えた比較集合です。23=7（span1）+6（span2）+10（span3）。mask0001011は1が3個でもspan4であり、短いburst保証の外です。

```sh
node verify.mjs
node check.mjs
```

通常はread-only。新原票だけ`--record observations/NEW-ID`を明示し、既存directoryは拒否。別原票はcheckerの`--node observations/NEW-NODE/raw.json --browser observations/NEW-BROWSER/raw.json`。全列挙と拒否は区別し、拒否を正常CRC処理件数へ混ぜません。検出/未検出の件数をchannel確率に読み替えず、ランダムsample・実通信・製品profile適合とも呼びません。

[検証記録](VERIFICATION.md)と[module-local Skill](skills/atlas-crc-undetected-errors/SKILL.md)で原票と実画面へ接続。同一agent routingであり独立Forward Evalではありません。旧Goal/Core/Gate、他module、global Skill、公開/Git/課金/Docker/OS設定は扱いません。

## 原典と次の4実験

MIT6.02 [Chapter6 PDF §6.6.1–6.6.4、冊子pp.75–78 / PDF pp.11–14](https://ocw.mit.edu/courses/6-02-introduction-to-eecs-ii-digital-communication-systems-fall-2012/34b7d78e0b90235095ef81542f6aa2dc_MIT6_02F12_chap06.pdf#page=11)の符号化、受信検査、長除算、g倍数の未検出、burstの本文を2026-10-05に確認。例/図/codeは独自制作、既存Apache-2.0方針に従い、第三者本文やPDF画像を転載しません。原典の歴史的暗号方式への言及を現行推奨とは扱いません。

[scope.json](scope.json)に増分と未教材を対応付けます。

- E1 製品profile：全fieldとknown vectorを固定する別fixture。[RFC9260 Appendix A CRC32c](https://www.rfc-editor.org/rfc/rfc9260.html#appendix-A)。今回の3bit値を転用しない。
- E2 長いblock/burst/interleaving：block長と誤りmodelを変えて比較。[MIT Chapter6 §6.4–6.5 / §6.6.4](https://ocw.mit.edu/courses/6-02-introduction-to-eecs-ii-digital-communication-systems-fall-2012/34b7d78e0b90235095ef81542f6aa2dc_MIT6_02F12_chap06.pdf#page=8)。未制作。
- E3 認証：鍵付きMACと非鍵CRCの改変拒否を別実験。[RFC2104 §2](https://www.rfc-editor.org/rfc/rfc2104.html#section-2)は歴史的定義の入口、algorithm選定は別review。未制作、鍵を用意しない。
- E4 実通信：実送受信frame/loss/retryと人工故障を別観測。[MIT Chapter6 §6.5–6.6](https://ocw.mit.edu/courses/6-02-introduction-to-eecs-ii-digital-communication-systems-fall-2012/34b7d78e0b90235095ef81542f6aa2dc_MIT6_02F12_chap06.pdf#page=8)。物理channelは別機器/許可、未制作。

長いblock、任意生成多項式、複数製品profile、実通信、暗号認証、訂正、性能、多Browser/AT/実機、学習者理解度は未評価です。

# ADD/ADDIのRAWを5段pipelineで観察する

同じ3命令でも、無対策は古いoperandを使って結果を間違える。chainの逐次結果はx1=5,x2=10,x3=9。無対策は5,0,4294967295、stallは4回待って11cycle、forwardingは7cycleで正しい結果を得る。この教材独自のIF/ID/EX/MEM/WBモデルで、その違いを追う。

```sh
python3 -B serve.py
```

表示された`http://127.0.0.1:<port>`を開く。Python標準libraryだけを使い、依存追加・ログイン・外部通信は不要。終了はCtrl-C。隔離された実行環境ではlocalhostのbind/connectが拒否されることがある。今回もsandbox内bindは失敗し、失敗記録を残した上でOS承認された同じ一時serverで表示を検証した。

programと対策を選び、oracleとの一致を予測して「実行」。cycle表のID-latch、MEM、WBを比べる。「3対策を比較」で同programのcycle数と一致状態を比較できる。条件変更は古い結果を消し、「初期条件に戻す」はchain/無対策/未回答へ戻す。raw JSONは画面のdetailsにある。

## 学習順序

1. chainを無対策で実行し、EXが読む値と正しい逐次結果の差を説明する。
2. stallに変え、EX/MEM待ちとWB→IDの読出し順序を数える。
3. forwardingで同じ値がMEMから両sourceへ流れる様子を確認する。
4. priorityで古いWBと新しいMEMが同registerに一致するときの優先順位を確認する。
5. two-source、wb-gap、x0-write、imm-boundary、wrap、emptyで境界を区別する。

[CONTRACT.md](CONTRACT.md)に実装前の手書きcycle表、演算規則、latched/next-state契約を固定した。[model.py](model.py)はpipeline、[oracle.py](oracle.py)は独立したinstruction順の逐次演算。source viewerは実ファイルをallowlistから読む。

```sh
python3 -B verify.py
python3 -B route.py
```

有限検証は9fixture×3対策=27比較、18入力拒否、8実際に実行した故障変種。逐次oracleは全32registerを照合し、chainの全cycle stageを手書き表と照合する。初回rawは`observations/attempt-01.json`、core先行成功は`observations/core-first-success.json`、実ブラウザの転記と範囲は`observations/browser.json`、hash receiptとread-only proofは同directoryに保存する。観測の分類は[COVERAGE.md](COVERAGE.md)を参照。

## 限界と出典

これはADD/ADDIの構造化命令だけを受ける教材で、機械語decoder、全RV32I、LOAD/STORE、branch、例外、HDL、実CPUは検証していない。MEMはresultを運ぶ空の段である。cycle数はモデル内の比較であり、実CPUの速度を保証しない。独立oracleも同じ限定されたADD/ADDIだけを扱う。

[公式RISC-V RV32I 2.1](https://docs.riscv.org/reference/isa/v20260120/unpriv/rv32.html)はx0、32-bit、ADD/ADDIの即値とoverflow規則を参照。[Cornell CS3410](https://www.cs.cornell.edu/courses/cs3410/2025fa/notes/pipelining.html#hazards)はpipelineとhazardの導入を参照するが、RAW対策の詳細は同ページの範囲外。WB順序・stall・forwardingの優先順位は本教材の独自契約。

このmodule内の実測だけを報告する。repository全体のCore `atlas audit` / `npm run gate`は依頼範囲外で未実行。commit、push、公開は行っていない。

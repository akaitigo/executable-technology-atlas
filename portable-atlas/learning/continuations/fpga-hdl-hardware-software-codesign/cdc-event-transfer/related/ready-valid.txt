# ready/valid stalled payload

元[FPGA入口](../../../subjects/fpga-hdl-hardware-software-codesign/README.md)のcounterとは異なる、ready/valid backpressureの有限教材です。[元coverage](../../../subjects/fpga-hdl-hardware-software-codesign/COVERAGE.md)の次4から1offerのstallだけを扱います。

valid=1、data17、ready[0,0,1]で、正常はstall中17を保持し最後に1回17を捕捉します。advance-on-stall故障は17→18→19と更新し19を捕捉。ready無視故障は[17,17,17]の3回捕捉です。既存counterの逐次代入故障とは異なります。

## 捕捉時点とsubset

各tickは立上りedge。すべての入力はedge前に安定済みです。edge前valid/ready/dataを読む→正常受信はvalid&&readyだけ捕捉→同じedgeの後に送信状態を更新します。1offerで、最初の実handshake後valid=0、それ以降はdataを保持し再offerしません。normal sourceはstallでもvalid/dataを保持。advance sourceだけstall毎にdata=(data+1)%256。ready無視は正常sourceを使い、receiverだけvalidで捕捉する故障です。ready列はどの版でも同じ外部入力で、故障receiverがreadyを変更する模型ではありません。valid=0初期値ではofferしません。

入力はexact keys data/ready/validのみ、dataはexact int 0..255、validとready各bitはexact int0/1、readyは0..8edge。bool/float/余分field/範囲外/非有限/重複JSON keyを拒否。空readyは実行済み0edgeで未transferです。物理時刻・信号立上り間の遅延・reset・burst・queueはありません。

[ARM IHI 0022H原典](https://developer.arm.com/-/media/Arm%20Developer%20Community/PDF/IHI0022H_amba_axi_protocol_spec.pdf)のA3.1.1（PDF p40）とA3.2.1（p41–42）を2026-10-06 JSTに確認。立上りedgeでsignalをsample、両VALID/READYでtransfer、transferまで情報保持、VALIDをREADY待ちにしない契約に結合します。初期valid=1、1offerの退役、8bit wrapは教材定義で、AXI全体の適合試験ではありません。

## 事前表・独立oracle・実行

[literal tick表](expected-table.json)はproducerより先に固定した15ケースです。各行はtick/pre-valid/pre-ready/pre-data/capture/captured/post-valid/post-data。期待値にproducerをimportしません。[oracle.py](oracle.py)は最初のready=1位置のclosed-formで各tickを算出し、逐次state evaluatorと独立です。全256 data×valid0/1×0..4edge全ready列の15872入力で照合し、捕捉時点・stall故障・ready無視の最小mutant3つを検出します。全長8の全列の形式的証明ではありません。

```sh
python3 -B checker.py
python3 -B runner.py
python3 -B runner.py --record
python3 -B server.py --record
python3 -B qa/check-ui.py
```

checker/runner/QA通常実行は全unit SHA256/mtimeを維持し、tmpを書きません。明示recordだけfresh UTC原票を新規作成し旧原票・失敗を保存します。Python version/source hash/stdin/stdout/exit/resultを結合。所有loopback動的portのserverだけ起動/停止し、600ms遅延はstale QA用です。

UIは予想→操作→正常/2故障・次のedge・信号図→原典/source/raw→答え。可変JSONを毎回実Pythonへ送り、actual捕捉列から答えを生成。次のedgeは保存actual tickのprefixを表示し、RTL波形と称しません。全例/予想/JSON変更と比較開始は本文・trace・信号図・step・rawを空にしてdetailsを閉じ、新入力保持。入力拒否/通信実行失敗は正常答えなし。revisionで古い応答を破棄します。[実IAB QA](qa/README.md)で実captureと表示制限、cleanupを確認します。

## 未実証

PATHのiverilog/verilator/ghdl不在を[棚卸し](qa/tool-inventory.json)に保存しinstallはしていません。RTL/HDL simulator、合成、STA/timing、setup/hold、CDC/metastability、reset、AXI burst/channel依存、MMIO/driver、実FPGA/device成功は未実証です。Core/共有/旧unitは変更せず、全体audit/gateは中央統合範囲。この有限unitだけをfreezeします。

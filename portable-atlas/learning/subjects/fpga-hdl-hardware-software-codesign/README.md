# FPGA・HDL・協調設計を学ぶ入口 — クロック付き2bit counter

有限1教材。今回このMacで実行したのはPython標準libraryのclocked state transition model。iverilog/verilatorはPATH上に見つからず、RTLツール実行未実証。合成・timing closure・実機・HW/SW bus連携は未実行。[UI](index.html)は保存された実行出力を読む。

**前提 → 仕組み:** 2進数00,01,10,11とmod4、条件分岐を知ってから、q（counter）とprev（前edgeのq）の2組のFFを考える。組合せnext-stateをedge前の状態から計算し、edgeで全registerを同時更新する。ソフトウェアの逐次代入としてqを先に変更してprevへコピーすると、1cycleの遅延が消える。

**予想 → 操作 → 比較:** [UI](index.html)で「qが3から0へwrapしたedgeのprevは？」を予想し、正常・wrap/hold、clock間reset pulse、reset優先、空trace、最大境界、拒否caseを選ぶ。「次のevent」で波形と表を見て、正常/next-state-bug/asyncの3列を[独立oracle](oracle.py)と比較する。予想はブラウザ内だけ。「答えを表示」へ進む前に[RTL](rtl/counter.v)、[モデル](model.py)、[一次資料](SOURCES.md)を開ける。

**契約:** 初期q=0,prev=0は教材の定義（RTLのpower-on保証ではない）。入力は`{"events":[{"t":0,"edge":1,"en":1,"rst":0}]}`だけ。eventは0..64件、tは0..10000の厳密増加integer、edge/en/rstはinteger 0/1のみ（bool/float拒否）、extra key拒否。edge=1は立上り事象、edge=0は立上りなしの入力変更。clock levelの周期波形ではない。入力はedge直前に安定済み。出力は理想同時更新後の値。

| 条件 | sync正常のq′ | sync正常のprev′ |
|---|---|---|
| edge=0 | q | prev |
| edge=1,rst=1 | 0 | 0 |
| edge=1,rst=0,en=0 | q | q |
| edge=1,rst=0,en=1 | 00→01→10→11→00 | edge前のq |

async版はrst=1ならedgeなしでもq/prevを0にする。reset優先はenableより強い。意図異常`prev <= q_next`はNB記法でも誤った仕様となる。`q = q+1; prev = q;`と同様に遅延が消えるが、blockingの全raceをこのモデルで再現した訳ではない。

**今回の実装・正常異常:** [runner](runner.py)は通常read-only、[checker](checker.py)は独立表oracleに対し全128の1step状態/入力を検査し、保存rawの再計算、artifact digest、文書local links/source binding、skill routingを確認する。正常wrapのt=40はq=0,prev=3、異常prev=0。clock間pulseのt=12はsync q=1,async q=0、次edge t=20はsync q=2,async q=1。enable=0でもprevが毎edge更新される点をt=50で確認する。[raw](evidence/raw.json)と[モデル波形](evidence/waveform.svg)は同じ保存入力に結びつく。

このdirectoryで実行:

```sh
python3 -B runner.py
python3 -B runner.py --input-json '{"events":[{"t":0,"edge":1,"en":1,"rst":0}]}'
python3 -B checker.py
python3 -B route.py counter
python3 -B route.py synthesis # 未対応、exit 2
python3 -B preview.py # dynamic 127.0.0.1。表示URLを開き、終了はCtrl-C
```

原票を再観測する明示依頼のときだけ`python3 -B observe.py --write-evidence`。artifact bindingの更新は`python3 -B checker.py --seal-evidence`の明示option。通常checker/runnerは原票や時刻を更新しない。CLI input拒否はexit2、検査失敗はexit1。再観測とhashの再封印は別操作。[run](evidence/run.json)の時刻・環境・input/source digestが保存観測の由来。[UI QA](evidence/ui-qa.json)は実IAB操作とcapture保存可否・専用server cleanupを記録する。

将来既存iverilog環境でRTLを実行する場合はmodule内で`iverilog -g2012 -o evidence/counter-sim rtl/counter.v rtl/tb.v`後、evidence内で`vvp counter-sim`。今回はこのコマンド未実行。[testbench](rtl/tb.v)は期待値を直書きしNBA更新後に観測するが、未コンパイルなので正しさは未確認。

**実務判断 → 限界 → 次へ:** この結果からreset/enable優先順位、1cycleのlatency、clock間pulseの見逃しを仕様として判定できる。clock停止中のsync reset、async deassertion安全性、FPGA速度/資源/PPA、software連携は判断できない。[全Subjectのcoverageと次の4実験](COVERAGE.md)でHDL→合成/STA→CDC→AXI/HLSへ進む。広い分野の完成宣言ではなく、実行済みと未教材を辿れる入口に育てる。

[専用skill](skills/atlas-fpga-hdl-hardware-software-codesign/SKILL.md)はこのrunner/checker/UIへ限定route。Portal/Core/Graph/GitHub/OS設定・global Skill登録は変更しない。

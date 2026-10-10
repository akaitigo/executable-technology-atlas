# Cache Lines: 空きがあるのにmissする

Python stdlibの有限・読み出し専用direct-mapped cache simulatorです。問いは「全体に空きがあればhitするのか」。block/index/tag/offset、before/after、eviction、返却byteをraw traceへ残し、UIでstep比較します。論理modelの実行であり、Mac実CPU cacheやcycle/latency/energyの測定ではありません。

## 観測した反例

学習の道筋：**byte address・2進数・商/剰余**を前提に、**block/offset → index/tag → valid照合 → fill/eviction**を理解し、下の正常/意図異常を比較します。その後「同じ容量・同じtrace・同じcold startか」「dataは正しいか」を実務判断に使い、[限界](COVERAGE.md)を読んでから[原典](#検査と根拠)へ戻ります。2進数がまだ不慣れならUIの10進block/index/tagと8bit表示を並べて確認できます。

容量16B（data容量、metadata除外）、line4B、4行。初期状態はinvalid、memoryは256Bのsynthetic read-only data `byte(a)=(17*a+3)%256`。

`0 → 16 → 0 → 16`はblock0/4、両方index0、tag0/1です。正常は**0 hit / 4 miss / 3 eviction**で、3行は空のまま。最初のblock4読出しは未読miss、再訪0/16がmissする部分が同index競合の反例です。tag-mismatchすべてを一般的な3C分類のconflict missとは呼びません。

意図異常版はtag比較を省略。3 hit / 1 missと見えますがaddress16へbyte3を返し、期待19との不一致が2回。判定だけを壊した実行であり、正しい別cache方式や高速化ではありません。

| 保存input | 正常 hit/miss/eviction | 意図異常 hit/miss/wrong byte |
| --- | --- | --- |
| conflict `[0,16,0,16]` | 0 / 4 / 3 | 3 / 1 / 2 |
| spatial `[0,1,2,3,4,5,4,15]` | 5 / 3 / 0 | 5 / 3 / 0 |
| offset conflict `[0,1,16,17,0,1]` | 3 / 3 / 2 | 5 / 1 / 2 |
| 最小geometry 1B/line1 `[0,255,255,0]` | 1 / 3 / 2 | 3 / 1 / 2 |
| 最大geometry 64B/line16 `[0,15,16,31,48,63,255,240]` | 4 / 4 / 1 | 5 / 3 / 2 |
| 空trace | 0 / 0 / 0（hit率未定義） | 0 / 0 / 0 |

capacity12、line3、line>capacity、address256はread前に拒否。無効inputを正常0 missとは扱いません。[原票](evidence/run.json)に時刻・環境・input・source/raw/diagram digest、[生trace](evidence/stdout.json)に全状態を記録しています。

## 通常checkerはread-only

Repository rootから:

```bash
cd learning/subjects/computer-architecture-digital-systems
python3 -B check.py
python3 -B check.py --input-json '{"capacity_bytes":16,"line_bytes":4,"address_bits":8,"addresses":[0,16,0,16]}'
python3 -B verify.py
```

stdoutのみ。customの拒否はstructured errorとexit2。固定10case batchは拒否例も教材観測として含みexit0。optionなし`observe.py`もread-onlyです。stdlib Python3.9以上、install/Docker/外部サービス不要。

**原票を更新する明示操作だけ**:

```bash
python3 -B observe.py --write-evidence
python3 -B verify.py
```

checker subprocessを実行しraw stdout/stderr、観測時刻/環境、input/source/hash、trace再描画SVG、`data.js`を更新します。検証に合わせて原票を自動変更するoptionではありません。書込は各fileのtemp→replaceで、世代全体の原子的swapを保証する設計ではありません。

## UIと再現

```bash
python3 -B -m http.server 0 --bind 127.0.0.1
```

表示された割当portの`http://127.0.0.1:PORT/`を開きます。port0は他担当のlistenerを停止せず空きportを割り当てます。教材titleが`Cache Lines — 空きがあるのに、missする。`、mainの`data-field-id`が`computer-architecture-digital-systems`であることを確認。終了はこのterminalのCtrl-C。`index.html`の直接表示でも保存`data.js`を読みます。

予想→next read→bit分割/配置図/正常と異常の比較→trace jump→実装・一次資料→答えの順。UIは保存10 inputだけの再生で、Pythonの新規実行や実機CPUアクセスではありません。diagramが8行を超えるgeometryは先頭8行のみ、table/rawは全行を表示します。

## 検査と根拠

- [cache.py](cache.py)：独自実装。全inputを先に検証し、正常valid+tagと意図異常valid-onlyを実行。
- [verify.py](verify.py)：手計算の4read traceと集計、独立memory-byte recurrence＋block range/slot enumerationでbefore/after/dataを照合。25 geometry/6400 address mapping、4-symbol長さ4の全256trace、seeded200trace、拒否19入力、Evidence mutation8＋Oracle mutation4を確認。default checker/optionなしobserve/custom拒否の3processで全module byte不変を検査。有限試験であり全64read input列の網羅や形式証明ではありません。
- [初回検査失敗と修復](evidence/validation-history.json)：最小geometryの手計算wrong byte誤記を修正した履歴。実装・独立enumerationの一致は保持。
- [実trace図](evidence/conflict-trace.svg)：raw traceの再描画で、captureではありません。[実IAB QA](evidence/visual-qa.json)は画面操作とcapture保存可否を別記録。
- [Cornell CS 3410 / Caches](https://www.cs.cornell.edu/courses/cs3410/2025fa/notes/caches.html)：valid/tag、fill、larger blocks、3C分類の一次course資料。
- [CMU 15-213 / Caches](https://www.cs.cmu.edu/afs/cs/academic/class/15213-s00/lectures/class18.pdf)：slide12–14、17。第三者本文・コード・図は保存せず[sources.json](sources.json)へURL/locatorのみ。

## 状態と次の範囲

問い／成功条件／経路／観測は上記の有限比較。次は自分でCLIのaddress列を変え、正常の返却byteと配置を照合できます。未教材は[COVERAGE.md](COVERAGE.md)に列挙。このmoduleだけの成果で、Subject全体・Portalの完成、実CPU仕様・performance・学習者理解度は証明しません。[module内Skill routing](evidence/skill-routing-check.json)はmain-agentの軽量確認で、独立Agent Evalとは別です。Skillは既存CLI/UIへrouteし、global installなし。旧repo/Core/Graph、commit/push/公開は行っていません。

## 今回から判断できること／次の4実験

今回の観測から、direct-mappedの競合を総容量の不足と区別し、block単位の配置を手で追い、hit/missだけでなく返却dataを検査できます。cache性能の結論には実機構成・timingが別途必要です。UIの観測時刻もcycle値ではありません。

下記は**未実施の学習候補**です。1のline-size比較は既存checkerのinputで試せますが、比較結果は今回の原票へまだ保存していません。2–4は別の有限実装が必要で、今回のScopeを自動拡張しません。

| 主要未教材の概念 → 問い | 次の有限実験と比較条件 | 一次資料locator |
| --- | --- | --- |
| locality・associativity・hierarchy → lineを大きくすれば常に良い？ | 1. 同16B/cold start/同traceでline2/4/8を比べ、行数変化とhit・fetch byteを追う。associative/多段cacheはその後の別model。 | [Cornell: Larger Blocks / Keeping Comparisons Fair](https://www.cs.cornell.edu/courses/cs3410/2025fa/notes/caches.html#larger-blocks) |
| write policy・dirty・recovery → eviction時に更新dataが失われない？ | 2. read/store/readの小traceでwrite-throughとwrite-back＋dirtyを別実装し、eviction後のmemoryと独立oracleを比べる。今回のread-only版では未対応。 | [Cornell: Handling Stores](https://www.cs.cornell.edu/courses/cs3410/2025fa/notes/caches.html#handling-stores) |
| ISA・datapath・pipeline・digital state → dependent instructionを重ねても同じ値になる？ | 3. RV32Iの少数命令をsequential modelと有限pipeline/FSMで追い、stall/forwarding省略の異常とregister結果を比較する。HDL合成・clock実機は別。 | [RISC-V v20260120: RV32I / Integer Computational Instructions](https://docs.riscv.org/reference/isa/v20260120/unpriv/rv32.html)、[Cornell: Hazards](https://www.cs.cornell.edu/courses/cs3410/2025fa/notes/pipelining.html#hazards) |
| memory consistency・atomic・coherence境界 → 各hartの順序だけで他hartの観測を決められる？ | 4. 2hartの小litmusを有限候補列挙し、RVWMOのordering条件に照合する。single-reader cache traceをcoherence/consistencyの証拠に流用しない。 | [RISC-V v20260120: RVWMO 17.1.1](https://docs.riscv.org/reference/isa/v20260120/unpriv/rvwmo.html) |

TLB/仮想記憶は「どのaddress空間でindexするか」、DRAM/I/O/NUMAは「missの先に何があるか」、timing/energyは「正しいhit率から実時間を推定できるか」、ECC/securityは「故障や観測漏えいをどう区別するか」、HDL/CDCは「論理stateが物理clock境界でも安全か」が残る問いです。これらは上記4実験でも閉じません。まず[Coverage](COVERAGE.md)の未教材を確認し、timingの入口は[Cornell: Understanding Cache Performance](https://www.cs.cornell.edu/courses/cs3410/2025fa/notes/caches.html#understanding-cache-performance)のAMAT条件、digitalの入口は[Cornell: Multi-Cycle Processors](https://www.cs.cornell.edu/courses/cs3410/2025fa/notes/pipelining.html#multi-cycle-processors)のstage/register関係です。page/TLB・ECC・CDC・製品securityの一次資料と実装Evidenceは本unitには未整備です。

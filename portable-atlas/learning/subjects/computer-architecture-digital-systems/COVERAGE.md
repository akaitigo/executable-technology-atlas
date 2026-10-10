# 有限範囲と未教材Coverage

今回のunitは読み出し専用direct-mapped cacheの論理simulationです。synthetic256B memory、8-bit byte address、冷えた初期状態から実行します。memoryにwriteはしません。tagを省略するvariantだけが意図異常です。

入力は`capacity_bytes`=1..64の2の冪、`line_bytes`=1..16の2の冪かつcapacity以下、`address_bits`=8、`addresses`=0..64 readのlist、各address=0..255のinteger。bool/floatはinteger扱いせず拒否。extra key（write等）も拒否します。line-size/容量にはtag/valid metadataを含みません。

保存10caseは正常配置・locality・競合・1行/最大geometry・空trace・4種類の拒否。原票更新時刻と環境はrun.jsonに固定され、未再観測を現在の実測とは呼びません。verificationはmapping全6400と限定256trace、生成200trace、19拒否を含みますが、全geometryの全64read列を網羅しません。

未教材・未実証:

- cache拡張：write-through/write-back、write allocate、dirty、set/fully associative、LRU/FIFO/replacement、victim cache、prefetch、multi-level hierarchy、inclusive/exclusive、cache coherence、3C一般自動分類。
- processor architecture：ISA実装、instruction decode、register file、ALU、pipeline/hazard/forwarding、superscalar/out-of-order、branch prediction、SIMD/vector、interrupt、microcode。
- memory/system：virtual address/TLB/page walk、memory ordering/consistency、atomic、DMA/I/O、NUMA、interconnect、DRAM controller/refresh、persistent memory。
- digital systems：Boolean logic、combinational/sequential circuits、flip-flop、FSM、HDL simulation/synthesis、FPGA/ASIC、timing closure、clock/reset/metastability、CDC。
- correctness/resilience/security：formal hardware verification、ECC/parity、fault injection、spectre/side channel、rowhammer、access control、実機障害/回復。
- empirical measurements：Mac等実CPU cache構成、counter/PMU、cycle/latency/bandwidth、AMAT実測、power/energy/thermal、PPA。Python実行の壁時計時刻は観測provenanceで、CPU cacheの性能データではありません。

異常版の高いhit率は正しいdataを返さず性能比較に不適切です。synthetic byte formulaは教材のテストdataで実RAMの内容ではありません。logic simulatorの結果をprocessor製品や実言語Runtime全体の証拠へ転用しません。

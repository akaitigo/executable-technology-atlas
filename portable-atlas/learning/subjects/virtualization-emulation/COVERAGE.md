# Virtualization / emulation分野のroadmapと未教材coverage

今回の有限1unitは作者定義Tiny8のstdlib interpreter。LOAD/ADD/JZ/HALT、guest8bit width、PC/operand wrap、illegal opcode、step budgetを実行した。hypervisor、実VM boot、isolationの証明、実ISA互換、devices全体の完成ではない。

前提はbyte/2進数、配列、PCとregister、fetch/decode/execute。主要概念はhostとguestの仕様を分けること。Pythonの大きなintegerをguest Aへ無制限に入れると、guest branch結果が変わる。[UI](index.html)→[SPEC](SPEC.md)/[README](README.md)→[原典](SOURCES.md)から次の4実験へ。

| Subject主要概念・今回の未教材coverage | 今回から判断できること / 次に解く問い | 次の具体的実験 | 一次資料locator |
|---|---|---|---|
| ISA semantics / interpreter / endian・signedness / flags・exceptions / memory addressing / disassembly / debugging・tracing / instruction compatibility | ADDのwidthがJZ/PC制御へ影響する。operandを跨ぐfetchも仕様の一部。実ISAの全命令、load/store、endianness、flags、interruptは未教材 | **次1:** Tiny8に有限STOREとflagを追加し、self-modifying code/未定義命令を独立trace比較。次に公式実ISAの小subsetでsigned overflowとendianを検査する | [Tiny8 SPEC](SPEC.md)、[QEMU system introduction](https://www.qemu.org/docs/master/system/introduction.html) |
| dynamic binary translation / JIT / translation blocks / cache・invalidation / host codegen / perf / deterministic replay・differential testing | 現在はinstruction毎にPython分岐する。guest状態変更・jumpの正しさが先。speedup、native codegen、TB chaining、timing精度は未検証 | **次2:** 同じTiny8をblock interpreter化し、referenceとの全trace比較。STORE導入後にcode cache invalidation漏れを注入。実JIT性能評価は別scope | [QEMU TCG internals](https://www.qemu.org/docs/master/devel/tcg.html) |
| full system emulation / firmware・boot / MMU・page tables / virtual memory / device model・MMIO・interrupt / timers・I/O / virtio・queues / disks/network / snapshot・migration | register/memoryだけではOSはbootしない。MMU/privilege/device/clock/migration state、guest diskやnetworkは未実装 | **次3:** owned in-memory device register/timer modelを追加し、read/write/interrupt状態をtrace比較。snapshot保存/restoreでPC/A/memory/deviceの欠落を検出し、実bootは対応環境と別scopeで | [QEMU devices/introduction](https://www.qemu.org/docs/master/system/introduction.html)、[VirtIO spec](https://docs.oasis-open.org/virtio/virtio/v1.3/virtio-v1.3.html) |
| hardware-assisted virtualization / hypervisor type / trap・exit / vCPU scheduling / KVM/HVF / nested translation・EPT / passthrough・IOMMU / containersとの境界 / isolation・escape / resource quotas / live migration・orchestration | step budgetでTiny8 loopを有限化できるが、実guest隔離/host安全性、VM exit、device passthroughを証明しない。CPU emulationとhypervisorは何が違うか | **次4:** 既存の対応環境がある将来、最小vCPU programのexit理由とmemory mapを公式APIで比較。今回はその前段としてhost/guest/resource境界の有限モデルを作る候補に留め、権限追加・VM起動はしない | [KVM API](https://docs.kernel.org/virt/kvm/api.html)、[Apple Hypervisor](https://developer.apple.com/documentation/hypervisor)、[QEMU accelerators](https://www.qemu.org/docs/master/system/introduction.html) |

実務判断: guest register/PCの幅、fetch境界、HALT/fault/budgetの優先順位を仕様に書き、host言語の都合をguestの意味に漏らさない。budget拒否はguest programが有限に停止しなかった今回の観測で、一般の停止性判定やreal VM resource isolationの保証ではない。

限界: read-only256byte memory、A/PC8bit、4opcode、1..64step。全256×256ADDとPC/fetch有限境界は検査できるが、任意の全program列・実CPU/VM全状態のproofではない。OS/syscall・I/O・STORE・privilege・MMU・real cycle・JIT・QEMU/KVM/HVF/実VM boot・isolation・migration・Linux/Windows runtimeは未実行。新依存/Docker/host設定/権限追加/外部サービス/公開なし。

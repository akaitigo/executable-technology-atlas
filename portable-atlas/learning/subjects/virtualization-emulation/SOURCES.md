# 一次資料locatorと実装binding

確認日2026-10-05。Tiny8のencoding/width/flags/budgetは[作者定義のSPEC](SPEC.md)が正本。外部原典は分野の仕組み・次の学習・未実証範囲へ結びつけ、実製品互換性の証拠として使わない。

| ID | 一次資料locator・節 | 実装との対応と確認状態 |
|---|---|---|
| ISA | [SPEC](SPEC.md), opcode table / memory / fault / budget | この教材固有の仕様。[emulator](emulator.py)、[独立table oracle](oracle.py)、[handtrace](handtrace.json)が別に追う。 |
| PYINT | [Python built-in types](https://docs.python.org/3/library/stdtypes.html#bitwise-operations-on-integer-types), integer / bitwise operations | Web本文取得確認。host integerの性質をguest8bit widthと混同しない。正常は明示wrap、異常はADD/PCのwidthを忘れる。実行Python3.9.6。 |
| EMU | [QEMU System Emulation Introduction](https://www.qemu.org/docs/master/system/introduction.html), virtualisation accelerators / feature overview | Web本文確認。guest CPU/memory/devicesのmachine modelとhardware acceleratorの区別を読む。今回はCPU-like interpreterだけでguest OSやdevicesを実装していない。 |
| TCG | [QEMU Translator Internals](https://www.qemu.org/docs/master/devel/tcg.html), CPU state / block chaining / code invalidation | Web本文確認。次のinterpreter→dynamic translationの問いへ。今回はJIT、translation block、self-modifying code未実装。 |
| KVM | [Linux KVM API](https://docs.kernel.org/virt/kvm/api.html), VM / vCPU / memory slots / KVM_RUN | Web本文取得確認。hypervisorの別scopeへの入口。今回KVM、実VM boot、guest/host隔離を実行していない。 |
| HVF | [Apple Hypervisor framework](https://developer.apple.com/documentation/hypervisor), virtual machines / virtual CPUs | 公式locatorのみ。Mac向けhardware-assisted virtualizationの次学習候補。権限変更・framework利用・VM bootなし。 |
| VIRTIO | [OASIS Virtual I/O Device specification](https://docs.oasis-open.org/virtio/virtio/v1.3/virtio-v1.3.html), virtqueue / device lifecycle | 公式locatorのみ。CPUだけでOSがbootできない理由、device modelの次学習へ。今回はdevice I/Oなし。 |

[case入力](cases.json)→[raw](evidence/raw.json)→[run](evidence/run.json)の時刻・環境・input/source/raw/SVG SHA-256→[integrity](evidence/integrity.json)が有限実行のbinding。QEMU master文書の記載版は閲覧時のsource版で、このMacに導入したQEMUのversionではない。QEMU/KVM/VMは今回実行していない。

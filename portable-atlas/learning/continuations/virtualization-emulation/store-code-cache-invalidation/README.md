# STOREで変わった命令とdecode cache

[元Tiny8入口](../../../subjects/virtualization-emulation/README.md) → [今回のSTORE仕様](SPEC.md) → [予想して実行原票を読む](index.html) → [write policy / dirty eviction](../../computer-architecture-digital-systems/write-policy-dirty-eviction/README.md)。元COVERAGEの次1–2に対する有限追加で、Subject/Atlas全体のcompleteは主張しない。

memory[9]は確かに1→7になった。ところが事前decodeしたLOADのoperandが1のままなら、guestの最終Aも1になる。毎命令fetchと重なるcode範囲を失効するblock interpreterはA7。UIで予想し、実Pythonの命令trace・書込み・cache失効を比較してから答えを開く。

```sh
PYTHONDONTWRITEBYTECODE=1 python3 checker.py
PYTHONDONTWRITEBYTECODE=1 python3 runner.py
PYTHONDONTWRITEBYTECODE=1 python3 route.py
```

通常checker/runnerはstdoutだけ、単元全fileのhash/mtime不変を検査する。明示的な `python3 runner.py --record` だけがfresh UTC run配下へ原票・stdout/stderr/exit・環境・入力・固定表・digestを作り、UI pointerを更新する。旧原票は上書きしない。UIボタンは保存原票を読む。guestをブラウザ上で再実行するボタンではない。

10ケース×3実装。operand変更、opcode変更でillegal、code外STORE、unrelated block保持、末尾直後への書込み、PC255 operand0のwrapを分離。入力拒否・illegal・budget拒否を別分類し、最後のbudget枠HALTも検証する。故障はcache失効漏れだけで、ADD/PC幅は両block実装とも元仕様どおり。

[実装](experiment.py) / [独立checker](checker.py) / [固定期待表](expected-table.json) / [原典](sources.json) / [coverage](coverage.json) / [入口routing](route.py) / [Skill](skills/atlas-store-code-cache-invalidation/SKILL.md) / [実IAB QA](qa/README.md)。原票URLはUIのrun表示から辿れる。

QEMUの[Translator Internals](https://www.qemu.org/docs/master/devel/tcg.html#self-modifying-code-and-translated-code-invalidation)は、codeの書換えに対応して変換済みblockを失効する原理の一次資料。このPython教材のISAや命令結果の正本はSPECと固定表であり、QEMUを実行した証拠ではない。

未実証: flag、実ISA、native JIT、QEMU実行、TB chaining、速度改善、VM boot、MMU/device、hypervisor isolation。今回はPython decoded blockの整合性だけ。追加STORE仕様は元read-only Tiny8を置換しない。ローカル単元serverでは親Subjectや関連単元リンクは配信外になる。存在確認と実表示は区別する。

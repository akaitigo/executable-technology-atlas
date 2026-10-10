# mappingへBを書いた。fileにもBが見える？

[第1単元](../../../subjects/operating-system-kernel-engineering/README.md)のpipe/FD参照寿命から、既存COVERAGE次3のfile mmap可視性へ進む追加単元。Macの実OS syscallをPython stdlib経由で観測する。原単元や他continuationを変更せず、全Subject/Atlas完成を主張しない。

前提はbytes、file offset/length、FD、process、仮想memory。仕組みはACCESS_WRITE(shared)、ACCESS_COPY(private copy-on-write)、ACCESS_READ。各別の所有fileをAAAA（4byte）で初期化し、length4/offset0でmmap。index1のAへbyte66(B)をassignmentする。副ACCESS_READ mappingを先に開き、同じprocess内の別Path.read_bytesとも比較する。[事前literal期待](EXPECTATIONS.md)を先に固定。

| mode | 実write | mapping | 副readonly mapping / 別file read | close後file |
|---|---|---|---|---|
| ACCESS_WRITE | 成功 | ABAA | ABAA | ABAA |
| ACCESS_COPY | 成功 | ABAA | AAAA | AAAA |
| ACCESS_READ | TypeError拒否 | AAAA | AAAA | AAAA |

[UI](index.html)で **予想→event操作→3mode比較→原典/実装/raw→答え**。file write buffer→file flush before map→mappings open→write→mapping flush→mapping close→observer close→file closeを追う。sharedのBはmapping flush**前**の別readでも見えたという同一process内のruntime観測。private flush成功後もfileはAAAA。readonlyのflush成功はreadonly write成功を意味しない。

mapping.close直後は元file objectがopen、副mappingもopenと実観測。これらは別resource。closed mappingのbytesは観測できないためUIで「closed / 未read」とし、残るbytesを捏造しない。最後に全所有mapping/file/tempを回収。

安全なPython APIの別4case: offset1/length1の非aligned mmap→OSError、file4byteにlength5→ValueError、length4のindex4 read→IndexError、close後read→ValueError。実exception type/message/errno、offset/length/modeをrawに残す。拒否はAPI例外で、signal実験ではない。mapped中にtruncate/resize、unsafe pointer、実SIGBUS/SIGSEGVを起こす操作はしない。

```sh
python3 -B record.py                  # current保存原票を読む、read-only
python3 -B checker.py                 # literal期待/source/raw/artifactを照合
python3 -B route.py visibility
python3 -B route.py pagefaults        # unsupported exit2
python3 -B preview.py                 # 自分のdynamic127.0.0.1 preview
```

新原票のみ `python3 -B record.py --record` を明示。UTC/UUID新fileで旧runを上書きせず、unexpected execution failureもpartial eventとcleanupをfailed rawへ保全。通常checkerは再実行/修復をしない。binding更新だけ `python3 -B checker.py --record-binding`。rawは実write成功2、readonly拒否1、安全API拒否4を別に数え、拒否を成功writeへ混ぜない。

実務判断: fileを変更したいかmappingだけを変えたいかでaccessを選ぶ。初期bufferをflushしてからmmapし、mapping・副mapping・fileの所有/close順を明記する。runtime可視性、flush APIの成功、電源断後durabilityは別の証拠。private mappingの局所変更を永続file更新と誤解しない。

今回coverage増分: virtual memory/file mappingのuser-space実観測、shared/private/readonlyのbytes可視性、file flushとmapping flush/closeの分離、安全API拒否。残る次実験3本:

1. **跨processの協力共有**: owned親子processのhandshakeでshared mappingとprivate差を比較。今回同一processだけの証拠を跨processへ一般化しない。[Python mmap](https://docs.python.org/3.9/library/mmap.html)
2. **pagefault / COWの証拠境界**: 既存OS診断に対応する専用環境がある場合、page単位アクセスとOS計数を比較し、copy数をbytes差から推定しない。[Linux mm docs](https://docs.kernel.org/mm/index.html)（次locator、今回本文未確認）
3. **persistence / lifetime**: 所有fileのunlink後FD/mapping寿命と明示syncを別に観測。process終了と電源断を区別。[Apple mmap](https://developer.apple.com/library/archive/documentation/System/Conceptual/ManPages_iPhoneOS/man2/mmap.2.html)、[POSIX mmap](https://pubs.opengroup.org/onlinepubs/9799919799/functions/mmap.html)（今回本文未取得）

限界: Darwin/実CPython版・4byte・固定index・同一process、file-backed mappingのみ。real COWページ数、pagefault、TLB、allocator、reclaim/OOM、NUMA、kernel内部、crossprocess、power lossは未観測。flush成功でもdurability_proven=false。host設定・新権限・実危険signal・他task資源の操作はない。実IABは保存した実OS観測の再生で、browserからmmapを実行しない。

[原典](SOURCES.md) · [input](fixture.json) · [実装](producer.py) · [独立literal oracle](oracle.json) · [current raw](evidence/current.json) · [binding](evidence/binding.json) · [実IAB QA](evidence/ui-qa.json) · [検証](evidence/verification.json) · [限定Skill](skills/atlas-mmap-visibility/SKILL.md)

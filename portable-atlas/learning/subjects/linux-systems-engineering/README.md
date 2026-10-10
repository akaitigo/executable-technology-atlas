# Linux Systems Engineering

Linux/POSIX file permission 9bitの有限logical checkerを、このMacのPython標準ライブラリで実行する教材。[index.html](index.html) は予想→操作→bits/trace比較→原典/実装→答え。実fileをchmodせず、Linux kernelのpermission checkは未実行。

## 学習の道筋

1. 前提: inodeのowner UID/GID、process credential、octal mode、r/w/x。
2. 主要概念: owner/group/otherから1classを選び、そのclassの必要bit全部を確認する。選択と判定を分離する。
3. 今回の実装: [fixtures.json](fixtures.json) の合成inodeとprincipalを [model.py](model.py) で比較。raw octal、9bit図、class選択理由、selected/request/intersectionをtraceへ記録する。全classのbitをORするbadと比較する。
4. 正常/境界/異常: owner/primary/supplementary/other、owner-group重複、000/777、read/write/file execute/directory search/read+write、root/ACL等拒否を観察する。
5. 実務判断: actorがownerならowner bitが不足していてもotherへfallbackしない。groupとotherのunionで補う実装は誤り。permission denialを調べるときcredential・対象inode・operationを先に固定する。
6. 限界と原典: 以下のsubsetを確認し、path全体、ACL/privileged caseなど次のcoverageへ進む。全Subject完成ではない。

## 実行

このディレクトリで実行する。入力は全て合成値。

```sh
python3 -B run.py
python3 -B run.py --principal other
python3 -B run.py --mode 040 --principal supplementary
python3 -B run.py --mode 001 --principal other --operation search --kind directory
python3 -B run.py --principal root
python3 -B run.py --security acl
python3 -B check.py
python3 -B server.py
```

CLI判定結果はallow/denyともexit0。未対応/不正入力はJSON rejected/exit2。専用APIはmode/principal/operation/kind/security各1つ、論理拒否もHTTP200の実験結果、未知principalやqueryはHTTP400。UIは実行開始時に前回結果を消す。serverのtemporary127.0.0.1 URLで比較し、所有serverをCtrl-Cで終了。通常checkerはread-only。原票更新を指示されたときだけ `python3 -B check.py --record`。

## 対象subsetとbit図

| modeの3桁 | owner | group | other |
|---|---|---|---|
| 各桁の意味 | r=4 / w=2 / x=1 | r=4 / w=2 / x=1 | r=4 / w=2 / x=1 |
| 004 | 000 | 000 | 100 |
| actorがowner | **この000を選ぶ** | 見ない | fallbackしない |

[Linux path_resolution(7) · Permissions](https://man7.org/linux/man-pages/man7/path_resolution.7.html) のclass選択とsupplementary group、execute/searchの説明に対応するsubset。合成uid/gidは通常のeffective IDに相当し、Linux fsuid/fsgidと一致するケースだけを前提にする。fsuid overrideは未対応。actual credentialを読み取らない。

actor UIDがinode owner UIDと一致ならownerを選択。そうでなければprimary GIDまたはsupplementaryの一致でgroup。両方不一致ならother。selected bit maskへrequestをANDし、必要bitが全部ある場合だけallow。これをPythonで実計算するが、kernel実装やPOSIX全体の適合試験ではない。

[Linux inode(7) · File type and mode](https://man7.org/linux/man-pages/man7/inode.7.html) にあるpermission 9bitだけを扱う。modeは厳密な3桁000..777。special bits、type bitsは入力拒否。inode kindは別入力。file executeとdirectory searchはx=1を確認するが、実execute成功やdirectory tree全体の到達は保証しない。directoryでexecute、fileでsearchは本教材のoperation語彙として拒否する。read+writeは両bitが必要。read/writeをdirectoryへ指定した場合も1inodeのbit判定だけで、list/create/delete等の操作を再現しない。

[Linux capabilities(7)](https://man7.org/linux/man-pages/man7/capabilities.7.html) などのprivileged caseは別に学ぶ。actor uid0、ACL、capabilities、LSM、fsuid overrideは未対応拒否し、allowed=nullとする。「rootなら常にallow」を実装しない。absenceを前提にした通常9bit判定だけ。mountのread-only/noexec、immutable、network filesystem、user namespace、symlink、path walk、TOCTOU、already-open FD等も未モデル化。

inode owner UID/GID・actor UID/GIDは0..65535整数（bool不可）、actor uid0は未対応、supplementaryは0–3整数ID。この上限は教材の有限境界でLinuxの上限ではない。supplementary重複はmembership判定に影響しない。real fileの権限やOS設定は変更しない。Mac chmodをLinux証拠へ読み替えない。

## 独立matrixと手計算

[oracle.py](oracle.py) はmodelをimportせず、octal各桁0..7を手でr/w/x集合へ対応付ける。principal→classも別の手表。必要文字がすべて集合にあるかを判定し、test対象のshift/ANDを再利用しない。512 modes × 5 principals × 5 operations = 12,800条件を照合する。

| 入力 | selected / protected | bad | 判断 |
|---|---|---|---|
| 004 owner read | owner0 / deny | allow | otherのrへfallbackしない |
| 004 other read | other4 / allow | allow | 適用classが違えば結果が違う |
| 040 group read | group4 / allow | allow | primary group一致 |
| 040 supplementary read | group4 / allow | allow | 補助groupも対象 |
| 400 other read | other0 / deny | allow | ownerのrを他人へ渡さない |
| 044 owner-group read | owner0 / deny | allow | ownerをgroupより優先 |
| 400 owner read-write | owner4 / deny | deny | readだけでは両方requestを満たさない |
| 001 other directory search | other1 / allow | allow | xをsearchとして判定 |

badのany-class unionに加え、requested bitのどれか1つだけでallow、supplementary無視、group先行の意図故障4例を検出する。ordinary denyは意図異常入力ではなく正常な判定結果。未対応root/ACL等の拒否とは分ける。

## 原票と検証

[evidence/run.json](evidence/run.json) は実行時刻、Python/OS環境、全gridのraw octal/principal/operation、input/trace digest、独立期待、手計算8例のfull raw trace、拒否入力と故障例。[bindings](evidence/bindings.json) はsource/artifact SHA256と公式locatorを結ぶ。fixtureが合成credentialを固定するので全gridのinput digestを再構成できる。[UI QA](evidence/ui-qa.json) は実IAB操作・観測、capture保存可否、所有server/tabの終了。[routing smoke](evidence/routing-smoke.json) と [Skill](skills/atlas-linux-systems-engineering/SKILL.md) は既存コマンドへのrouteを確認する。主agentのsmokeで独立forwardAgentEvalではない。

checkerは原票・README/indexのroadmap・公式locator・README local linksも確認。初回原票生成時だけ未生成evidence linkをbootstrapとして許容する。Core `atlas audit` / `npm run gate` は専用module scope外で未実行。全Subject完成は主張しない。新Goalは作成しない。

## 未教材coverageと次の実験

| 主要概念・問い | 次の有限実験 | 公式locator |
|---|---|---|
| process/memory/syscall: fork/exec/wait、signal、FD共有、virtual memoryは | 合成親子processとFD tableで共有/独立、exit/wait状態を比較 | [clone(2)](https://man7.org/linux/man-pages/man2/clone.2.html) |
| storage/security: pathname search、symlink、mount、umask、ACL/capabilities、永続化は | 合成pathの各directory gateとACL/privilege layer、書込み/commit故障を比較 | [path resolution](https://man7.org/linux/man-pages/man7/path_resolution.7.html) / [capabilities](https://man7.org/linux/man-pages/man7/capabilities.7.html) |
| network/isolation: socket、namespace、resource隔離とpermissionの関係は | 合成network namespaceとendpoint tableでvisibility/authorizationを比較 | [namespaces(7)](https://man7.org/linux/man-pages/man7/namespaces.7.html) |
| operations/observability: service障害、process状態、CPU/memory/FD、観測値の限界は | 合成/proc snapshotとservice lifecycleで待ち/終了/資源不足を区別 | [Kernel /proc documentation](https://docs.kernel.org/filesystems/proc.html) |

以上は未教材。次は「単一inodeが許可でも、どのpath/credential/namespaceでsyscallが失敗するか」を追う。Linux runtime、root/ACL/capabilities/LSM、実pathname、container、service管理、actual chmod/accessは未検証。

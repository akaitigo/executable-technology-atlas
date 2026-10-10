# Pathname：末端readの前にdirectory searchを通れるか

固定非特権principalと合成inode表をPythonで実計算する有限教材。[元Linux Subject](../../../subjects/linux-systems-engineering/README.md)のREADME storage/security coverage（行77）のpath各directory gateを具体化します。Mac chmod、host credential、実ファイルのpermissionは変更しません。Linux kernel実測ではありません。

## 前提・読む順

uid/gid、owner/group/other、octal r/w/x、fileとdirectoryの違いが前提です。元Subjectの1inode class選択→今回のpath gate→[SecurityのID取得と認可の境界](../../../subjects/security-engineering/README.md)へ進む。Securityのobject policyとfilesystem searchは別の契約です。

1. [合成入力](requests.json)と[事前手表](oracle.json)を読み、終端結果・最初の停止node/stage・最終可否を予想する。
2. [画面](index.html)で条件選択→予想→保存実測と比較→答えを開く。
3. directory-read-no-searchとleaf-only-faultを比べ、gate図・selected class/3bits/requiredを確認。
4. [Linux path_resolution(7)](https://man7.org/linux/man-pages/man7/path_resolution.7.html)のStep 2、Step 3、Permissions→[walker](walker.py)→[独立checker](checker.py)へ戻る。
5. [未実証範囲](COVERAGE.md)へ進む。

## 固定契約と手計算

principal uid1000/gid10/supplementary[20]。root inodeはuid2000/gid30/mode0001、owner一致なしgroup一致なしのother001でsearch可。標準vaultはuid1000/gid10/mode0100：owner001でsearch可。reportはuid1000/gid10/mode0400：owner100でread可。modeは4桁0xxx、special bitsは拒否。合成IDはfsuid/fsgidが通常IDと同じケースを仮定し、overrideは扱いません。

| 手表 | root search | vault lookup/search | report lookup/read | first stop / 結果 |
|---|---|---|---|---|
| vault0100＋report0400 | other001 x可 | directory / owner001 x可 | file / owner100 r可 | none / ALLOW |
| vault0400＋report0400 | 可 | directory / owner100 x不可 | 未到達 | /vault SEARCH / EACCES |
| 同条件 leaf-only故障 | 省略 | 省略 | file / owner100 r可 | none / 誤ALLOW |
| file0000 | 可 | 可 | owner000 r不可 | /vault/report READ / EACCES |
| root0000 | other000 x不可 | 未到達 | 未到達 | / SEARCH / EACCES |
| /missing/report | 可 | 存在しない | 未到達 | /missing LOOKUP / ENOENT |
| /vault/missing | 可 | 可 | 存在しない | /vault/missing LOOKUP / ENOENT |
| vaultがfile | 可 | kind file、非directory | 未到達 | /vault LOOKUP / ENOTDIR |
| supplementary group | other001 x可 | group001 x可（GID20） | group100 r可（GID10） | none / ALLOW |
| other class | other001 x可 | other001 x可 | other100 r可 | none / ALLOW |

SEARCHは現在directoryで次の名前をlookupする前に必要。directory read bitだけでは名前のsearchを許可しない。既知名のreadではdirectory listingを要求しないためvault0100で足ります。LOOKUPで存在/kindを確認し、最後にfile READを判定。最初の失敗で停止し、その後のnodeは未到達です。EACCES/ENOENT/ENOTDIRはモデルの結果ラベルで、host syscall errnoではありません。

leaf-onlyは意図故障：末端inboxではなく末端inodeだけを参照し、path directory gateを省略します。事前oracleはこの故障の実結果ALLOWと、同条件正しいwalkのEACCESを分けます。原典への完全適合とは扱いません。

~~~sh
python3 -B runner.py --record
python3 -B checker.py
python3 -B test_negative.py
python3 -B route.py inspect
python3 -B route.py lesson
python3 -B preview.py
~~~

recordのみ新UTC runへsource/input/command/exit/stdout/stderr/hashを保存。旧rawを上書きしません。[CURRENT](CURRENT)が原票を指す。通常runner/checker/routeはread-only。checkerは固定class・各gate・firstStop・最終可否のliteralと比較し、producerwalkerも元Subject matcherもimportしません。[QA](QA.json)に実IAB、各予想変更の本文消去/閉鎖、condition reset、captureと所有資源終了を記録します。

root、ACL、symlink、capability、mount、namespaceは実行前REFUSED/exit2/allowed=null。malformed JSONは実子processのexit3/stdout空でEXECUTION_FAILURE。正常denyはOBSERVED/exit0/allowed=falseです。拒否・実行失敗へ正常answerを補完しません。

## 比較 → 答え → 残範囲

答えはpath上の各directoryで選ばれたclassのxを順に確かめること。末端r許可だけでは取得権限になりません。directory rとsearch x、存在確認と認可、通常denyと範囲外拒否を分けて調べます。

原典のStep 2はdirectory searchと存在/kindの停止、Permissionsはowner/group/otherとdirectory xの意味を確認するlocator。Step 3の最終entryの扱いはsyscallごとに異なるため、ここでは既存file readだけです。

ACL/capability/LSM、mount/namespace、symlink、relative/. /..、作成/削除、directory listing、TOCTOU、already-open FD、実Linux syscallとの適合、永続化は未実証。全Subject完成は主張しません。

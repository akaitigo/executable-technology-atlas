# template更新で手編集を保持する

[元の生成とcontract教材](../../../subjects/platform-engineering-developer-experience/README.md)のGolden path lifecycle次案を、小さな独自flat JSON 3-wayへ進める部分教材。既存projectには触れず、毎回専有TemporaryDirectoryのproject.jsonだけを実write→readする。

前提はbase/local/newとbyte差分。予想を選び「tmpで更新して再read」、初期localと更新後bytes・apply書込数を比較する。原典・実装・手表・rawへ戻り、答えを開く。可変local/pathの答えは実結果から作る。

|条件|base→local / base→new|実結果|
|---|---|---|
|手編集保持|1/team-a/base→1/team-b/user / →2/team-a/base|2/team-b/user、apply1|
|templateのみ|local=base / new=2/team-a/new|newそのまま、apply1|
|description衝突|local desc=user / new desc=new|CONFLICT、description、apply0、localbytes保持|
|同じ変更|local,newともdesc=new|衝突なし、2/team-a/new|
|無条件new故障|手編集保持と同じinput|2/team-a/base、手編集を失う|
|owner衝突|base team-c、local team-b、new team-a|owner CONFLICT、apply0|
|version衝突|base1、local2、new3|templateVersion CONFLICT、apply0|

各fieldでlocal=baseならnewを採用、new=baseまたはlocal=newならlocalを保持、それ以外は衝突。衝突fieldを一つでも含むと、この単一descriptorのapplyを全て行わない。byte形式はsorted keys・compact JSON・末尾newlineの独自canonical形式。衝突時の再serializeはせず、実localfileをそのまま再readしてbyte保持を確認する。

入力は3fieldだけ。templateVersionはboolを除くint1..3、ownerは架空team-a/b/c、descriptionはbase/user/newの有限文字列。未知/欠落field、不正version/owner、任意pathをtmp tree作成前に拒否。pathはproject.jsonの完全一致だけ。設定の一般性やTOCTOU対策を証明したvalidatorではない。

setup書込1はfixtureの準備。apply書込0とは既存userproject全体のwrite0ではなく、このtmpの更新phaseが書かなかったこと。実失敗はfile project.jsonをdirectoryとして扱うchild writeでNotADirectoryErrorを起こす。apply成功0、local bytes保持を確認する。OS permissionや自然障害を模した保証ではない。

[Backstage Software Templates](https://backstage.io/docs/features/software-templates/)は生成のinput/steps/resultのcontextとして読む。今回のmergeは独自契約で、Backstageの標準更新動作、標準migration機能と呼ばない。Backstageや外部repo生成を実行しない。

```sh
python3 -B verify.py --record attempt-01  # 未使用attemptのみ
python3 -B verify.py --seal-record       # QA後current binding
python3 -B verify.py                     # 実tmp再計算、module保存なし
python3 -B route.py
python3 -B serve.py                      # 動的localhost、終了Ctrl-C
```

実装前にliteral最終JSON/exactbytes/conflictfieldsの手表を固定。独立oracleはmergeを共有せず別literal bytesとartifact再readで比較する。9条件、拒否8入力、改変拒否6種。初回raw/receiptとbefore/after artifactを保全、QA後のcurrent bindingをsealする。通常checker/routeの全file hash/mtime不変を確認する。

一般text、rename/delete、multi-file atomic更新、並行編集、実Backstage運用、generated source実行、DX効果は未実証。次の実験はformat/コメント保持、rename/delete衝突、多file staged適用の失敗回復（未実行）。元Subject・旧unit・Portalは変更しない。install・設定・公開・commit/push・Core gateは専有制作の範囲外。

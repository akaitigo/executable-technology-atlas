# Argo CD：確認が必要な削除は、どこで止まる？

[前単元のPruneLast reader](../argocd-prune-last-boundary/index.html)で「どこへ配置するか」を学んだ後の課題です。この単元では、選択済みの現在waveについて、削除確認のゲートを通るか、prune処理の手前でpendingを返すかを比べます。

入口は [index.html](index.html) です。固定4ケースを「現在の組→確認走査→ゲート」の3段階で読むGUI、手追跡、Python模型、学習CLIを用意しています。1280/390pxの実操作・保存画像QAを確認済みで、独立受入は引継ぎ中です。**LIVE Argo CD/Kubernetes・Docker・Goコード・確認判定helper・APIは実行していません。** `pass` はこのゲートを通るという教材上の名前で、同期成功・削除成功を意味しません。

## 分野ゴールとの対応

既存 `atlas-97-field-goals-ja.md` 第62項「Argo CD」のprune判断に沿い、前単元で未対応とした削除確認を一段進めます。

|到達目標|この単元で進めること|
|---|---|
|説明する|確認待ちで止まる箇所と、prune実行結果を区別する。|
|操作する|現在wave・確認済みflag・確認必要資源の4ケースをCLIで対照する。|
|検証する|実装前の手追跡と、固定版の条件・ループ・return位置を照合する。|
|実務で判断する|確認が必要な資源が現在waveに含まれるかを確認する。|
|前提を使う|phase/wave選択、prune/createの分割、前単元の計画と到達条件の違いを使う。|
|限界を分ける|確認の生成経路、削除保護、権限、API、Healthは別の検証とする。|

## 1. 予想する

現在はSyncの有効wave 0が選択済みです。その組には、pruneのold-a/old-bと、applyのnew-configが入っています。後続の有効wave 1にはold-laterがあります。

|資源|属する組|処理|基本例で確認が必要か|
|---|---|---|---|
|old-a|現在wave 0|prune|不要|
|old-b|現在wave 0|prune|必要|
|new-config|現在wave 0|apply|このprune確認判定の対象外|
|old-later|後続wave 1|prune|不要|

確認済みflagはfalseです。次を予想してください。

- old-aだけ先にpruneしてから、old-bで止まるのか。
- old-bで止まるとき、同waveのnew-configをapplyできるのか。
- 確認済みflagがtrueなら、同じ資源の確認必要判定を走査するのか。
- 確認が必要なのがold-laterだけなら、現在waveのゲートも止まるのか。

`requires_confirmation` は、確認判定helperの結果を与えた仮定です。annotationの文字列やdefault設定を解析した値ではありません。`prune_confirmed` も入力状態であり、これをtrueにする操作や許可の仕組みは模型外です。

## 2. 操作して対照する

[index.html](index.html) を直接ブラウザーで開きます。ケースを選び、ゲート結果と最初の確認待ち資源を予想して、「対照を1段階進める」を3回押します。原典を読んでから答え合わせを表示します。予想変更・reset・ケース変更で前の結果は消えます。未選択エラーや予想不一致は学習上の応答で、Argoの実行失敗ではありません。

CLIはこのディレクトリで実行します。Python標準ライブラリだけを使い、通信・書込み・サービス起動はありません。

```sh
# 入力を見て予想する
python3 -B model.py --case needs-confirmation --view input

# 現在waveのold-bが確認待ちとなる予想を照合する
python3 -B model.py --case needs-confirmation --predict pending --predict-blocker old-b

# 確認不要、確認済み、後続waveだけの確認要求を比較する
python3 -B model.py --case no-confirmation-needed
python3 -B model.py --case already-confirmed
python3 -B model.py --case later-wave-only --predict pass --predict-blocker none
```

`--json` を付けると、走査した現在prune、最初の確認待ち資源、ゲート結果を取得できます。任意のmanifestや実clusterに対する判定器ではなく、[fixtures.json](fixtures.json)の固定4ケースを読む入口です。

## 3. 原典と実装を読む

Argo CD v3.5.2、commit `e258ee23c3e52266d407572f4bcdfe7d9ed36cb5` の固定版本文を使います。前単元群で正式取得した表示本文の読取を再利用し、今回は追加取得していません。

|固定版の箇所|この模型で扱う境界|
|---|---|
|[sync_context.go 612–621行](https://github.com/argoproj/argo-cd/blob/e258ee23c3e52266d407572f4bcdfe7d9ed36cb5/gitops-engine/pkg/sync/sync_context.go#L612)|現在phase/waveの組を選ぶ。本模型はその選択済み集合を受け取る。|
|[1469行](https://github.com/argoproj/argo-cd/blob/e258ee23c3e52266d407572f4bcdfe7d9ed36cb5/gitops-engine/pkg/sync/sync_context.go#L1469)|現在の組をprune側とcreate側へ分ける。|
|[1495–1502行](https://github.com/argoproj/argo-cd/blob/e258ee23c3e52266d407572f4bcdfe7d9ed36cb5/gitops-engine/pkg/sync/sync_context.go#L1495)|未確認ならprune側を走査し、確認必要と判定した資源でpendingを返す。確認済みならこの走査を省く。|
|[1503行以降](https://github.com/argoproj/argo-cd/blob/e258ee23c3e52266d407572f4bcdfe7d9ed36cb5/gitops-engine/pkg/sync/sync_context.go#L1503)|ゲートの後にpruneループがある。本模型はここへ進めるかまでで終了。|

[model.py](model.py)は条件と走査だけを実装しています。[source-review.json](source-review.json)に未読helper・原典の取得範囲を明記しています。raw byte列を保存しておらず、そのSHA-256は未取得です。Go実行やsource byte契約検査の証拠ではありません。

## 4. 答え合わせ

[手追跡oracle](hand-oracle.json)と[固定時点の記録](hand-oracle-lock.json)は、模型・validatorの実装前に保存しました。

|ケース|確認済みflag|現在waveの確認必要資源|ゲート判定で走査する資源|結果|
|---|---|---|---|---|
|no-confirmation-needed|false|なし|old-a → old-b|pass。prune処理へ進める境界。|
|needs-confirmation|false|old-b|old-a → old-b|old-bでpending。pruneループ前に戻る。|
|already-confirmed|true|old-b|走査なし|pass。確認必要かの走査を省く。|
|later-wave-only|false|なし。後続old-laterだけ必要。|old-a → old-b|現在ゲートはpass。後続資源を混ぜない。|

2例目ではold-aもpruneを始めていません。確認ゲート全体がpruneループより前にあるためです。同waveのnew-configのapplyへも進まず戻ります。これは「old-aの削除に成功してからold-bを待つ」という例ではありません。

4例目のpassは、後続の確認要求を無視して削除できるという意味ではありません。後続waveへ到達したときの集合や確認状態は、この例では実行・観測していません。

すべての例で模型はゲート境界までです。出力のprune/apply開始数とAPI呼出し数は0。passの後に削除が成功するか、失敗するか、Healthを待つかは結果として与えていません。

## 5. 検証と実務判断

```sh
python3 -B verify.py
```

通常検査は保存原票を書き換えません。初回保存用の `--record` は既存原票の上書きを拒否します。

4ケース・16入力資源・ゲート判定の走査6件が手追跡と一致しました。入力拒否10件、出力改変検出5件、CLI5件も初回pass。模型0.000844秒、CLI込み0.257366秒です。[実行原票](observations/model-check.json)に実行時hash・結果・CLI出力を保存しています。Argo CDの性能や実削除の待ち時間ではありません。

出力改変検出は、誤った待ち資源、後続要求で現在を止める誤り、確認済みでも走査する誤り、確認前の部分削除、passをOperationSucceededと取り違える誤りを弾く確認です。upstreamコードのmutation testではありません。

実務では、まずどのphase/waveの組を処理中かを確かめ、prune確認状態と、その組に確認必要な資源があるかを分けて見ます。確認flagだけでAPI権限・削除成功・安全な依存解消が保証されるわけではありません。止まっている理由をannotation/defaultの解析、API応答、Healthなどへ広げるには、それぞれの原典と実記録が必要です。

## 6. 未確認の範囲

現在の入力はSync・prune有効・選択済みwave・判定helper結果を準備済み、と固定しています。helper本文、annotation/default優先関係、Prune=false保護、確認済みflagの生成、pruneObject、API、権限、Health、hook、retry、finalizer、propagationは検証していません。一般schedulerやcycle解消も扱いません。

GUIの有限state検査33件・拒否5件、実ブラウザー21確認・39ポインター操作・1キーボード操作が通過しました。4ケースの実DOM全8項目を固定手追跡へ照合し、1280/390pxの保存実画像7枚を目視しています。[GUI-QA.md](GUI-QA.md) と [操作原票](observations/reader-browser-2026-10-06T071236352Z/report.json) が根拠です。独立受入は引継ぎ中で、LIVEは未実施です。

API 0 は模型の境界で、runTasks全体やゲート前hookがAPIを呼ばないという保証ではありません。旧模型原票は保持し、QA後の説明文だけを別metadataへ記録しています。次の不足は、確認判定helperと削除保護の固定版全分岐を確認することです。[COVERAGE.md](COVERAGE.md)、[Skill](SKILL.md)、[制作状態](observations/status.json)も参照してください。

この新専用pathだけへ保存しています。旧受入reader・統合repo・共有台帳・累計は変更しておらず、分野全体の完成や公開を宣言するものではありません。

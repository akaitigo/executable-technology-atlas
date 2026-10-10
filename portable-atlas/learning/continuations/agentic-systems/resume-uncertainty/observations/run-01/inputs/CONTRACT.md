# Atlas｜再開時に、承認と効果をどこまで知れるか

実装前の契約です。既存の型付き参照とcall別承認を前提に、承認消費の記録と効果完了の知識を分けます。外部API・実ユーザー承認・OS権限・実プロセス停止は使いません。対象計算・GUIは未実施です。

## 固定する境界

actor=alice、固定planのcall=increment-1、tool=counter.increment、args={counter_id:toy, delta:1}、承認期限10を使います。planとcallのSHA-256はASCII JSON・キー順・空白なしの固定bytesに対する同一性です。hashが権限を生むとは扱いません。

復旧関数 `resume(checkpoint, now)` に渡すのは4つの保存JSONの内容だけです。`cases.json` のcase名・中断位置・効果counterは渡しません。中央2条件は同じ `inputs/pending-shared.json` を読み、byte同一です。独立した教材側observerだけが効果0と1を知ります。

checkpointにはphase、call、外から固定したapproval、completionを置きます。phaseはREADY/PENDING/COMPLETED。READYは未消費かつcompletionなし、PENDINGは消費済みかつcompletionなし、COMPLETEDは消費済みかつcall hash/operation IDに一致する保存結果ありです。保存checkpointと承認元は信頼する有限模型です。実認証・署名・改ざん耐性を実装しません。

新規dispatchの前にはactor・plan hash・call ID・tool・argsの一致、external-fixedという出所、now<10、未消費を照合します。READYでは照合後に消費記録を保持してからdispatchする、逐次の模型遷移を仮定します。この順序が保持される前に効果は起こらないという契約であり、disk耐久性・並行の原子性を確認したことにはしません。

PENDINGは消費記録から効果0/1を推定せずHOLD_UNKNOWNとし、新規dispatchも自動での承認再発行も行いません。COMPLETEDは同じcallに結び付いた保存結果を返し、新しい効果を起こしません。この読取は新規dispatchの許可ではないため、時刻11でも保存結果を消しません。再照会・人への引継ぎ・補償の実装は次の範囲です。

## 5対照と故障2対照

|条件|再開時刻|復旧判断|新規dispatch|効果の前→後|返す結果|
|---|---:|---|---:|---|---|
|未消費・期限内|9|DISPATCH|1|0→1|1|
|消費後・効果前で中断|9|HOLD_UNKNOWN|0|0→0|null|
|効果後・結果保存前で中断|9|HOLD_UNKNOWN|0|1→1|null|
|未消費・期限切れ|10|REJECT_EXPIRED|0|0→0|null|
|完了結果保存済み|11|RETURN_SAVED|0|1→1|1|

故障版は中央2条件だけ、消費済みを未消費へ戻し、他の照合を通して同じcallを再dispatchします。新規dispatchは双方1、効果は0→1／1→2。双方を承認再利用の違反として記録し、効果が1件だった側も正常成功に数えません。中央2条件の復旧判断は両方の方式で同一でなければなりません。違っていたらobserver情報の混入を疑います。

復旧関数はdispatch指示を返し、別のdriverが合成counterへ1加算して応答と完了checkpointを保存します。効果counterはこのdriverだけが持ち、復旧判断の引数やclosureへ渡しません。未到達の効果値・外部観測値を0で埋めず、復旧側の知識はUNKNOWNとして保存します。

## 受入と限界

手表を先に固定し、別担当が独立表へ7結果と履歴を照合します。中央入力bytesと復旧関数出力の一致、具体call照合、承認使用前後、新規dispatch数、observerの効果前後、結果、故障の承認再利用を別項目として確認します。入力schemaの全境界・全クラッシュ位置は網羅しません。

UIは予想→保存結果→同じ再開記録の比較→原典/実装→答え→限界の順です。observer情報と復旧側が読めた記録を別領域に置き、取得失敗・条件/予想変更・resetで古い答えを消します。未計算時は期待表を実測として表示しません。

Python標準libraryの小さい模型を準備しますが、今回の静的制作では実行しません。実行・GUIは独立レビューと別途の枠を経ます。実HTTP、永続化、実再起動、同時実行、業務ledger、外部照会、一般exactly-onceを保証しません。

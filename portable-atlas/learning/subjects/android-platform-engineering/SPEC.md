# 有限モデル契約とAndroidの保証範囲

正本は作者定義のこの有限契約。Android SDK/APIの実装ではない。公式contractの対応は[SOURCES](SOURCES.md)。単一Activity相当・counter0..9・最大32イベント、並行処理/他componentなし。rotationはdefaultのdestroy/recreateを選んだ一例で、configChanges対応や全callback順序を再現しない。

入力は `{"saved":null,"events":["create","start","resume"]}` の2keyだけ。savedはnullまたはJSON text、eventsは1..32個の下表の文字列。bool/unknownevent/余分key/外部device path拒否。保存textはUTF-8で128byte以内、exact object `{"version":1,"counter":N}`、versionはinteger1、counterはinteger0..9。float/bool/重複key/extra key/壊れたJSON/UTF-8化できないtext拒否。保存decoderはcreate時に検査。これは独自の小さなcodecで、Android Bundle/Parcel binaryではない。

| event | 許される直前stage | 次stage / 操作 | callback表示 |
|---|---|---|---|
| create | ABSENT, DESTROYED, DEAD, FINISHED | CREATED、instance+1、serializedはsavedがあればrestore、nullなら0。ephemeralは検査後0に初期化。DEAD後はprocess+1/alive=true | onCreate(saved-or-null) |
| start | CREATED | STARTED | onStart |
| resume | STARTED, PAUSED | RESUMED | onResume |
| tap | RESUMED | counter+1、9からはcounter_limit拒否 | callbackなし |
| pause | RESUMED | PAUSED | onPause |
| stop | PAUSED | STOPPED | onStop |
| save | PAUSED, STOPPED | stage不変、serializedはversion/counterをcanonical JSON化、ephemeralは保存漏れでnull | onSaveInstanceState (explicit model event) |
| destroy_rotate | STOPPED | DESTROYED、counter消去、process生存、savedは保持 | onDestroy |
| process_death | STOPPED | DEAD、counter消去、alive=false、**saveもonDestroyも追加しない** | callbackなし |
| restart | STOPPED | CREATED（このmodelのonRestart後の中間点）、既存counter/instance/process維持。続くstart/resumeは別event | onRestart |
| finish | STOPPED | FINISHED、counterとsaved消去。次createは別のcold launch | onDestroy |
| drop_saved | STOPPED, DEAD, DESTROYED | saved=null。利用可能なsnapshotが無い分岐を入力で選ぶ | callbackなし |

ABSENTはActivity未生成、counter=null、instance0/process1/alive=trueから開始。initial savedは入力として外から渡す。数字はmodel IDで実PIDではない。DEAD/DESTROYED/FINISHEDではcounter=null。saved tokenは直近の明示saveを維持し、createで消費/変更しない。明示saveなしでは最新counterが反映されず、古いsnapshotへ戻る。実frameworkの内部保存実装/最適化を模倣したものではない。

無効な遷移/codec/counter limitはそのeventをcommitせずruntime拒否し、直前までのtraceとstateを残す。input拒否はtraceなし。serializedとephemeralは同じevent/input validation、ephemeralだけsave/restoreを省く意図異常。MAX32なので両方有限。

**重要な仮定:** saveは呼ばれたと入力に明記した時だけ成功する。資料のViews flowを参考にpause→stop→saveを選んだ例と、pause→save→stopを選んだ例を用意した。callback順序はAPI/targetで異なり、この表は全versionのAndroid合法遷移判定器ではない。process death後は「systemからsnapshotが渡された場合」を条件にrestoreする。必ず渡される/最新/永続とは保証しない。finish/task dismissal、force-stop/rebootの一般的復元は主張しない。

[手記](handtrace.json): counter3→pause→stop→save→destroy→createでinstance2のcounter3（保存漏れ版0）、同process1。process deathではonDestroyなし、新process2でsnapshotがあればcounter2、無ければ0。snapshot freshnessとdurable persistenceは別問題。

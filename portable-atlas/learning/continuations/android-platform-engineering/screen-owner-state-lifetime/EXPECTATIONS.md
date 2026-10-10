# producer実行前に固定したowner表

初期process1 alive、A owner p1:A:1/view generation1/state2、B owner p1:B:2/view1/state1。screen名はowner identityではない。createのserialはprocess内単調増加、次は3。rotateは同owner/state保持でview generationだけ+1。finishはowner/stateを消す。B finish→createはp1:B:3/view1/state0。

deathは全in-memory owner/state/故障cacheを消去しalive=false。restartは死後だけprocess番号+1、空のprocess模型を作る。new Bはp2:B:1/view1/state0。これは明示Python操作で実OS再開ではない。snapshot/tokenの保存・復元は実装しない。

故障global-leakはrotate targetのstateを全生存ownerへコピー。B回転でA=2が1へ漏れる。故障dead-owner-reuseはfinishしたownerをcacheへ残しcreateで再利用。再Bは旧p1:B:2/state1/view2となり正常契約違反。故障もdeath時はcache消去。

[固定literal](oracle.json)は11正常/故障caseの26状態行、別9拒否＋実RuntimeErrorの21case。各行はprocess/alive/AとBのowner・view_generation・state。独立oracleはproducer/transition関数を共有せず、生観測をこのtupleへ投影して厳密照合。

入力event list0..8件、厳密field op/target、op=create/rotate/finish/tap/death/restart。screen対象はA/Bのみ、death/restartはtarget null。mode scoped/global-leak/dead-owner-reuse。tapはstate0..9内。既存create、非存在rotate/finish/tap、dead processのscreen操作、生存processのrestart、不正JSON/field/type/op/targetをINPUT_REFUSEDで返す。拒否と実Errorはtimeline/final null、正常答えを出さない。

全入力（2予想とevent JSON）は、成功→答えを開く→一欄だけ変更を最初から実IAB確認。新値/他欄保持、旧raw/table/final/答え本文空、details閉鎖/非表示。条件resetは予想/JSONを消去。古い受信済HTTP payloadは描画を保留してversion違いを拒否、sleepなし。通信遅延測定とは呼ばない。

通常runner/checker/routeはread-only。明示recordだけ新UTC/UUID rawと実子process exit/stdout/stderr/source SHAを保存。想定外失敗はcurrent昇格せず旧rawを保持。

実Android/Compose/ViewModel/SavedStateHandle/Bundle/OS process再開、保存保証、real device callback順、全Subject/Atlasの完成は未実証。

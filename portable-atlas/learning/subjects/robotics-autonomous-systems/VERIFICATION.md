# 検証記録

問い：初期mapの最短pathと線分衝突、観測更新後の停止・再計画を別々に検証できるか。Mac直接Python stdlib→固定grid→raw trace→一時HTTP→実IABで確認する。実ロボット・実センサー・ROS・物理制御・安全保証は未実行。

10case×3policy、手動geometry5件、固定seed400geometry/100grid、不正input14件/option2件。手書き結果、独立layer-BFSとinteger orientation閉cell交差、各MOVE/停止/versionを照合。通常checkerはread-only、原票更新は明示 --record。作者Skill smokeは独立AgentEvalではない。

時刻・環境・input/source/artifact hashはobservations/receipt.json。実IAB/capture保存可否/ownedresource終了はobservations/ui-qa.json。指定path外、Portal/Core/Goal/commit/pushは変更しない。全体gate/full verifyは今回未実行、全Subject完成とはしない。

## 実行と実UIの結果

`python3 verify.py --record` / 通常 `python3 verify.py` はpassed。10case×3policy、100random grid、手動geometry5件＋400random geometry、不正input14件/option2件。独立layer-BFSと整数orientation幾何、手書きstatus/MOVE/位置予測に一致。rawにはrandomの全input/resultも保存。Python3.9.6、Darwin arm64、seed20261005。

実IABはactual HTTP port57423/tab6。[30行の観測原票](observations/ui-matrix.json)をrawと比較し、終端/位置/MOVE/直線判定/初期距離/plan数/map versionが一致。wall迂回と直線contact、STOP_BEFOREの位置[2,2]/contact[2.5,2]、REPLANの残り6edge、badのknown v0/world v1と命令edge接触、corner-touch[.5,.5]を実画面で確認。slider・前後・終端ボタン、入力/全plan・不正入力・receipt disclosure、10領域/4次実験を確認した。

実capture6枚をCUA出力で取得したがファイル保存なし。capture hashや代替描画は主張しない。[QA](observations/ui-qa.json)はraw/UI/sources/coverage SHA-256と結合。

通常sandboxではloopback bindがEPERMで終了。[失敗](observations/default-bind.txt)を保持。これは自動承認レビュー拒否ではない。一回の指定レビューで既存serve.pyのtemporary dynamic loopbackを許可され、[HTTP log](observations/preview-http.log)の教材資源200/fav icon404を保持。owned tab6 close、server session56195 Ctrl-C→exit0/finally server_close。

Skillのquick_validateとcollision対応/real-robot未対応smokeはpassed、独立AgentEvalではない。最終read-onlyの全既存moduleファイルhash前後一致はobservations/read-only-proof.json。証拠記録のwriteはcheckerと分離。全体gate/full verify、実robot/sensor/ROS/physics、安全保証は未実行。

# 検証範囲と証拠

既存MacのPython3.9.6標準ライブラリのみ。12条件、各17/33sample点の全state・全intervalを実行し、独立Decimal70の別式 y_next=a*y+(1-a)*u と照合します。Decimal oracleはcontroller/model/metricsをimportしません。初期手表3step×12と限界/等値/内向き/e0の9probeを別に検査。15設定拒否、8結果変異検出、Ki0の飽和/条件付き停止y/u同一も確認します。

plantの指数更新は保持入力区間のモデル厳密解をfloatで評価したものです。controller積分は旧eの矩形離散更新。高精度oracle照合は両モデルの一致検査で、実plant測定でも一般安定性証明でもありません。整定判定は4..8秒、±.05帯、以降全sample保持・残り1秒、未整定null。終端要求u/実uは未実行nullです。

UIは選択条件、同じh/Kiの3方式、選択方式のP対照を実Pythonへ要求します。実IAB検査の全12条件・対照投影・表示point数をCLIへ照合し、5変数図の軸/終端null、条件/予想/reset、古い応答、通信失敗、source読み戻しを別に記録します。保存browser投影は手動転記したコンパクト投影で完全raw downloadではありません。実tool画面captureはinline、保存path不明はsaved=falseとします。

attempt-01は上書きしません。source SHAと初回receiptを残しUI後seal。最終read-only-proofはverify/route/Skill/private-path検査の前後SHA・mtime不変を示し最後に作成。旧教材・global入口・manifest・保護server/tabは変更しません。Core gate、commit、push、公開は未実行です。

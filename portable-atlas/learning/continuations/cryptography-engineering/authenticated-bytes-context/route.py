ROUTES={'key順の比較':'raw-order','空白の比較':'raw-whitespace','canonicalの比較':'canonical-equal','operationの境界':'context-operation','resourceの境界':'context-resource','用途の境界':'context-purpose','拒否契約':'refuse-duplicate','原票検算':'checker.py'}
UNSUPPORTED=('本番鍵を作る','暗号を破る','認可を実装する','RFC8785準拠を証明する')
def route(request):return {'supported':request in ROUTES,'target':ROUTES.get(request),'executed':False,'reason':None if request in ROUTES else '有限教材の対象外。READMEの未実行coverageへ。'}

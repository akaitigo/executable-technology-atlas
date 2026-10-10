ROUTES={'1回答分布':'single','独立2回答分布':'double','bound3の流用':'double','全event比較':'double','契約外入力':'refuse-correlated','原票検算':'checker.py'}
UNSUPPORTED=('既存tableをDP化','実人物を再識別','一般DBのaccountant','実サービス安全保証')
def route(request):return {'supported':request in ROUTES,'target':ROUTES.get(request),'executed':False,'reason':None if request in ROUTES else '未対応。READMEの次coverageへ。'}

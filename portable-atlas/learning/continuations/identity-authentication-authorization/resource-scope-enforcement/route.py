ROUTES={'alpha正常読取':'a-reader-alpha-doc-alpha-read','alpha申告beta対象':'a-reader-alpha-doc-beta-read','beta申告alpha対象':'b-reader-beta-doc-alpha-read','read権限なし':'a-no-read-alpha-doc-alpha-read','未知resource':'refuse-unknown-resource','属性欠損':'refuse-missing-owner','原票検算':'checker.py'}
UNSUPPORTED=('IdPで認証する','OS権限を変更','TOCTOUを保証','ABAC全体に適合')
def route(request):return {'supported':request in ROUTES,'target':ROUTES.get(request),'executed':False,'reason':None if request in ROUTES else '有限教材の対象外。READMEの次coverageへ。'}

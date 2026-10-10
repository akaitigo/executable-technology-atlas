ROUTES={'同じcontract':'unchanged','最大99へ変更':'max99','versionだけ変更':'version-only','空白と順序だけ変更':'format-only','契約外入力':'refuse-contract-bool','原票検算':'checker.py'}
UNSUPPORTED=('CSVW準拠を認定','実データ承認','cache真正性を保証','全schema migration')
def route(request):return {'supported':request in ROUTES,'target':ROUTES.get(request),'executed':False,'reason':None if request in ROUTES else '未対応。READMEの次coverageへ。'}

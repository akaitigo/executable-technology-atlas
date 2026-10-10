ROUTES={'同世代versionの拒否':'same-version','同世代generationの拒否':'same-generation-version','再作成versionだけ':'recreated-version','再作成generation付き':'recreated-generation-version','入力拒否':'refuse-bool-version','SQL失敗との違い':'sql-error','原票検算':'checker.py'}
UNSUPPORTED=('分散CASを保証','backup世代重複を防ぐ','電源断を試す','並列lock性能を測る')
def route(request):return {'supported':request in ROUTES,'target':ROUTES.get(request),'executed':False,'reason':None if request in ROUTES else '未対応。READMEの次coverageへ。'}

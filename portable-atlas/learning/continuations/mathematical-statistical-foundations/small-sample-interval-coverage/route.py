ROUTES={'coverage比較':'all-p','k0の幅':'k0','k8の幅':'k8','外へ出る区間':'unclipped','単一観測の解釈':'single-interval','原票検算':'checker.py'}
UNSUPPORTED=('医療の個別推奨','実データ精度保証','Wilson区間を計算','random samplingを実行')
def route(request):return {'supported':request in ROUTES,'target':ROUTES.get(request),'executed':False,'reason':None if request in ROUTES else '未対応。READMEの次実験へ。別の明示割当が必要。'}

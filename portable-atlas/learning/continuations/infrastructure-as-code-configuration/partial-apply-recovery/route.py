ROUTES={'正常apply':'normal','変更前failure':'before-second','変更後failure':'after-second','盲目replay':'blind-replay','再観測と復旧':'refresh-replan','原票検算':'checker.py'}
UNSUPPORTED=('実Terraformを適用','cloud resource変更','rollback保証','分散transaction検証')
def route(request):
    return {'supported':request in ROUTES,'target':ROUTES.get(request),'executed':False,'reason':None if request in ROUTES else '未対応。READMEの次実験へ。別の明示割当が必要。'}
if __name__=='__main__':
    import json,sys
    print(json.dumps(route(sys.argv[1] if len(sys.argv)>1 else ''),ensure_ascii=False))

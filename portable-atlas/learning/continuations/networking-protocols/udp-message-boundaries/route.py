"""Finite lesson routing; reads evidence, never executes network or finance actions."""
ROUTES={
 'datagram境界':'two-datagrams',
 '空payloadとEOF':'empty-datagram',
 '残りを次recvで読む':'small-buffer',
 '幅ぴったりの検出':'exact-fit',
 '原票検算':'checker.py',
 '明示再採取':'runner.py --record',
}
UNSUPPORTED=('WAN配送保証','再送protocol実装','DNS設定変更','本番UDP負荷試験')
def route(request):
    if request in ROUTES:
        return {'supported':True,'target':ROUTES[request],'network_executed':False}
    return {'supported':False,'reason':'未対応。READMEの残る実験を確認し、別の明示割当が必要。','network_executed':False}

if __name__=='__main__':
    import json,sys
    print(json.dumps(route(sys.argv[1] if len(sys.argv)>1 else ''),ensure_ascii=False))

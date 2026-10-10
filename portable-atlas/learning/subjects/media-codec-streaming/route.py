# SPDX-License-Identifier: Apache-2.0
import json,sys

def route(topic):
    if topic in ('pcm','wav','pts','jitter-buffer','underflow','startup-delay','trace'):
        return dict(status='supported',runner='python3 verify.py',ui='index.html',reference='README.md')
    return dict(status='unsupported',reference='coverage.json',reason='PCM WAV and finite arrival toy only; H264/AAC/product codecs, live streaming and actual network not run')
if __name__=='__main__':print(json.dumps(route(sys.argv[1] if len(sys.argv)>1 else ''),ensure_ascii=False))

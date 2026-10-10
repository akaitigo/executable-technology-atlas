# SPDX-License-Identifier: Apache-2.0
import json,sys

def route(topic):
    if topic in ('grid','shortest-path','collision','stale-map','stop','replan','trace'):
        return dict(status='supported',runner='python3 verify.py',ui='index.html',reference='README.md')
    return dict(status='unsupported',reference='coverage.json',reason='Finite point-grid toy only; no real robot, sensor, ROS, dynamics or safety certification')
if __name__=='__main__':print(json.dumps(route(sys.argv[1] if len(sys.argv)>1 else ''),ensure_ascii=False))

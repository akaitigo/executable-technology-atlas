#!/usr/bin/env python3
import json,sys
print(json.dumps({'kind':'synthetic-health-failure','reason':'fixed fixture: canary alarm; no service/provider probe','healthy':False}))
sys.exit(42)

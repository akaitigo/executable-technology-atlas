#!/usr/bin/env python3
import pathlib,subprocess,sys
ROOT=pathlib.Path(__file__).resolve().parent
if len(sys.argv)!=2 or sys.argv[1] not in ['inspect','lesson','record']:
    print('unsupported route',file=sys.stderr);sys.exit(2)
if sys.argv[1]=='lesson':print('index.html; evidence '+(ROOT/'CURRENT').read_text().strip())
else:sys.exit(subprocess.call([sys.executable,'-B',str(ROOT/'runner.py')]+(['--record'] if sys.argv[1]=='record' else []),cwd=str(ROOT)))

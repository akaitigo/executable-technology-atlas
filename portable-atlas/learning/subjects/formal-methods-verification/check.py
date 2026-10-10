#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
import json
from model import MODEL_VERSION, explore


if __name__ == "__main__":
    print(json.dumps({"model_version": MODEL_VERSION, "models": {name: explore(name) for name in ("atomic", "split-guard")}}, ensure_ascii=False, indent=2))

# SPDX-License-Identifier: Apache-2.0
import json
from simulator import experiment

if __name__ == "__main__":
    print(json.dumps(experiment(), ensure_ascii=False, indent=2, allow_nan=False))

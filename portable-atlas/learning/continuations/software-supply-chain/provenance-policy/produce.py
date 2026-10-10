"""Atlas: 固定の小入力を読み、独立policyと同梱policy故障を別に保存。"""
import copy
import hashlib
import json
from pathlib import Path
from policy import compare

ROOT = Path(__file__).resolve().parent


def collect():
    cases = json.loads((ROOT / 'cases.json').read_text())
    consumer = json.loads((ROOT / cases['consumerPolicy']).read_text())
    artifact = (ROOT / cases['artifact']).read_bytes()
    rows = []
    for case in cases['cases']:
        raw = (ROOT / case['fixture']).read_bytes()
        bundle = json.loads(raw)
        if set(bundle) != {'artifact_file', 'artifact_sha256', 'claims', 'proposed_policy'} or bundle['artifact_file'] != 'artifact.bin':
            raise ValueError('fixed bundle schema')
        before = copy.deepcopy(bundle)
        consumer_before = copy.deepcopy(consumer)
        strict = compare(artifact, bundle['artifact_sha256'], bundle['claims'], consumer)
        # Deliberately wrong trust boundary: received policy is used as the expectation.
        faulty = compare(artifact, bundle['artifact_sha256'], bundle['claims'], bundle['proposed_policy'])
        rows.append({'id': case['id'], 'fixtureSha256': hashlib.sha256(raw).hexdigest(),
                     'bundle_before': before, 'bundle_after': copy.deepcopy(bundle),
                     'consumer_policy_before': consumer_before, 'consumer_policy_after': copy.deepcopy(consumer),
                     'artifact': {'hex': artifact.hex(), 'size': len(artifact), 'sha256': hashlib.sha256(artifact).hexdigest()},
                     'independent_policy': strict, 'bundle_policy_fault': faulty})
    return {'Atlas': '別保持policyと受信policyの有限比較', 'kind': 'synthetic_unsigned_claim_comparison', 'cases': rows}

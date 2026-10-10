"""Atlas: 署名を検証しない、独自来歴fieldの有限policy比較。"""
import hashlib

FIELDS = {'builder_id', 'source_id', 'build_type', 'parameters'}


def valid_record(value):
    if type(value) is not dict or set(value) != FIELDS:
        return False
    if any(type(value[k]) is not str or not value[k] for k in FIELDS - {'parameters'}):
        return False
    parameters = value['parameters']
    return (type(parameters) is dict and
            all(type(k) is str and type(v) is str for k, v in parameters.items()))


def compare(artifact_bytes, claimed_digest, claims, expected_policy):
    """No bundle object, signature result, or builder credential is accepted here."""
    if (type(artifact_bytes) is not bytes or type(claimed_digest) is not str or
        not valid_record(claims) or not valid_record(expected_policy)):
        return {'kind': 'input-refused', 'payload': None}
    checks = {
        'artifact_digest': hashlib.sha256(artifact_bytes).hexdigest() == claimed_digest,
        'builder_id': claims['builder_id'] == expected_policy['builder_id'],
        'source_id': claims['source_id'] == expected_policy['source_id'],
        'build_type': claims['build_type'] == expected_policy['build_type'],
        'parameter_keys': set(claims['parameters']) == set(expected_policy['parameters']),
        'parameter_values': all(k in claims['parameters'] and claims['parameters'][k] == v
                                for k, v in expected_policy['parameters'].items()),
    }
    return {'checks': checks, 'claimsMatchPolicy': all(checks.values()),
            'signatureCheck': 'not-run', 'authenticatedBuilder': None,
            'releaseDecision': 'out-of-scope'}

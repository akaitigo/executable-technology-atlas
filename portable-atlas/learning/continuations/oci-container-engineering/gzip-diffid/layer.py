"""Atlas: bounded single-member gzip validation, no extraction or runtime."""
import hashlib
import re
import zlib

MEDIA = 'application/vnd.oci.image.layer.v1.tar+gzip'
DIGEST = re.compile(r'sha256:[a-f0-9]{64}\Z')

def digest(data):
    return 'sha256:' + hashlib.sha256(data).hexdigest()

def verify_layer(blob, descriptor, expected_diff_id, output_cap, mode='strict'):
    diagnostic = {'compressedBytes': len(blob) if isinstance(blob, bytes) else None,
                  'compressedDigest': None, 'gzipStarted': False, 'inflateCalls': 0,
                  'stagedBytes': 0, 'observedDiffId': None, 'gzipEof': False,
                  'trailingBytes': None}
    trace = []
    def finish(reason, payload=None):
        trace.append({'stage': reason, 'accepted': reason == 'ok'})
        return {'accepted': reason == 'ok', 'reason': reason, 'payload': payload,
                'diagnostics': diagnostic, 'trace': trace}
    if type(blob) is not bytes or type(descriptor) is not dict or set(descriptor) != {'mediaType', 'digest', 'size'}:
        return finish('input-invalid')
    if descriptor['mediaType'] != MEDIA or type(descriptor['digest']) is not str or not DIGEST.fullmatch(descriptor['digest']):
        return finish('input-invalid')
    if type(descriptor['size']) is not int or descriptor['size'] < 0 or type(output_cap) is not int or not 1 <= output_cap <= 4096:
        return finish('input-invalid')
    if type(expected_diff_id) is not str or not DIGEST.fullmatch(expected_diff_id) or mode not in ('strict', 'conflated'):
        return finish('input-invalid')
    if len(blob) > 4096:
        return finish('input-limit')
    trace.append({'stage': 'input', 'accepted': True})
    if len(blob) != descriptor['size']:
        return finish('size-mismatch')
    trace.append({'stage': 'size', 'accepted': True})
    diagnostic['compressedDigest'] = digest(blob)
    if diagnostic['compressedDigest'] != descriptor['digest']:
        return finish('digest-mismatch')
    trace.append({'stage': 'compressed-digest', 'accepted': True})
    if mode == 'conflated':
        # Deliberate error: these two hashes identify different byte sequences.
        if diagnostic['compressedDigest'] != expected_diff_id:
            return finish('conflated-digest')
    decoder = zlib.decompressobj(wbits=31)
    output, pending, cursor = bytearray(), b'', 0
    diagnostic['gzipStarted'] = True
    while diagnostic['inflateCalls'] < 128:
        if not pending:
            if cursor == len(blob):
                return finish('gzip-incomplete')
            pending = blob[cursor:cursor + 64]
            cursor += len(pending)
        diagnostic['inflateCalls'] += 1
        try:
            part = decoder.decompress(pending, output_cap + 1 - len(output))
        except zlib.error as exc:
            diagnostic['zlibError'] = str(exc)
            return finish('gzip-invalid')
        output.extend(part)
        diagnostic['stagedBytes'] = len(output)
        diagnostic['gzipEof'] = decoder.eof
        trace.append({'stage': 'inflate', 'call': diagnostic['inflateCalls'], 'inputCursor': cursor,
                      'stagedBytes': len(output), 'eof': decoder.eof})
        if len(output) > output_cap:
            return finish('output-limit')
        if decoder.eof:
            diagnostic['trailingBytes'] = len(decoder.unused_data) + len(blob) - cursor
            if diagnostic['trailingBytes']:
                return finish('gzip-trailing-data')
            diagnostic['observedDiffId'] = digest(bytes(output))
            if diagnostic['observedDiffId'] != expected_diff_id:
                return finish('diffid-mismatch')
            # Only successful output is saved as bytes for independent verification.
            diagnostic['acceptedTarHex'] = output.hex()
            return finish('ok', {'tarBytes': len(output), 'diffId': diagnostic['observedDiffId']})
        pending = decoder.unconsumed_tail
    return finish('iteration-limit')

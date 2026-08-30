const SHA256_PATTERN = /^sha256:[a-f0-9]{64}$/;

function hex(bytes) {
  return [...new Uint8Array(bytes)].map((value) => value.toString(16).padStart(2, '0')).join('');
}

export async function parseDigestVerifiedJson(response, expectedDigest) {
  if (!response?.ok) throw new Error(`detail HTTP ${response?.status ?? 'unknown'}`);
  if (!SHA256_PATTERN.test(expectedDigest)) throw new Error('detail expected digest is invalid');
  const bytes = await response.arrayBuffer();
  const observedDigest = `sha256:${hex(await globalThis.crypto.subtle.digest('SHA-256', bytes))}`;
  if (observedDigest !== expectedDigest) throw new Error('detail artifact digest mismatch');
  try {
    return JSON.parse(new TextDecoder().decode(bytes));
  } catch {
    throw new Error('detail JSON is invalid');
  }
}


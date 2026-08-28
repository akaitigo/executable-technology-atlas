import { createHash, createPrivateKey, createPublicKey, sign, verify } from 'node:crypto';

export function canonicalJson(value) {
  if (Array.isArray(value)) return `[${value.map(canonicalJson).join(',')}]`;
  if (value && typeof value === 'object') {
    return `{${Object.keys(value).sort().map((key) => `${JSON.stringify(key)}:${canonicalJson(value[key])}`).join(',')}}`;
  }
  return JSON.stringify(value);
}

export function sha256(value) {
  const bytes = Buffer.isBuffer(value) ? value : Buffer.from(typeof value === 'string' ? value : canonicalJson(value));
  return `sha256:${createHash('sha256').update(bytes).digest('hex')}`;
}

const FIXTURE_SEED = createHash('sha256').update('executable-technology-atlas-fixture-key-v1').digest();
const PKCS8_PREFIX = Buffer.from('302e020100300506032b657004220420', 'hex');

export function fixtureKeyPair() {
  const privateKey = createPrivateKey({ key: Buffer.concat([PKCS8_PREFIX, FIXTURE_SEED]), format: 'der', type: 'pkcs8' });
  const publicKey = createPublicKey(privateKey);
  return {
    privateKey,
    publicKey,
    publicKeyPem: publicKey.export({ format: 'pem', type: 'spki' }).toString(),
  };
}

export function signDigest(digest, privateKey) {
  return sign(null, Buffer.from(digest), privateKey).toString('base64');
}

export function verifyDigest(digest, signature, publicKey) {
  return verify(null, Buffer.from(digest), publicKey, Buffer.from(signature, 'base64'));
}

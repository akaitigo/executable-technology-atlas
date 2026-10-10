// Independent mathematical oracle: no WebAssembly, bitwise operators or binary generator.
export function signed32(x){const modulus=4294967296n,v=BigInt(Math.trunc(x)),u=((v%modulus)+modulus)%modulus;return Number(u>=2147483648n?u-modulus:u);}
export function expected(c){
  const error={'bad-magic':'CompileError','bad-type':'CompileError','missing-import':'LinkError','bigint-call':'TypeError'}[c.kind]??null;
  return {validated:!['bad-magic','bad-type'].includes(c.kind),stage:c.kind==='bigint-call'?'invoke':error?'instantiate':'complete',errorName:error,result:error?null:signed32(signed32(c.a)+signed32(c.b)),jsNumberSum:c.kind==='bigint-call'?null:c.a+c.b};
}
export function stackModel(c){if(c.kind!=='add')return null;const a=signed32(c.a),b=signed32(c.b);return {kind:'explanatory-stack-model-not-engine-trace',converted:[a,b],steps:[{instruction:'local.get 0',stack:[a]},{instruction:'local.get 1',stack:[a,b]},{instruction:'i32.add',stack:[signed32(a+b)]},{instruction:'end → JS Number',stack:[signed32(a+b)]}]};}
// Exact independently transcribed encodings establish fixture identity, not generator correctness alone.
export const validHex='0061736d0100000001070160027f7f017f030201000707010361646400000a09010700200020016a0b';
export const importedHex='0061736d0100000001070160027f7f017f020b0103656e76036164640000070701036164640000';
export function expectedHex(kind){if(kind==='missing-import')return importedHex;if(kind==='bad-magic')return '01'+validHex.slice(2);if(kind==='bad-type')return validHex.slice(0,32)+'7e'+validHex.slice(34);return validHex;}

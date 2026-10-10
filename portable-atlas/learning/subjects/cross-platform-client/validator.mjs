// Shared contract: scalar-valid string, 1..4 code points. Bytes are another policy.
export function validate(input) {
  if(typeof input!=='string') return invalid('not-string');
  const points=[...input];
  if(points.some(c=>{const p=c.codePointAt(0);return p>=0xd800&&p<=0xdfff;})) return invalid('unpaired-surrogate');
  const codePoints=points.length,utf16Units=input.length,utf8Bytes=new TextEncoder().encode(input).length;
  return {error:null,codePoints,utf16Units,utf8Bytes,legacyAccepted:utf16Units>=1&&utf16Units<=4,codePointAccepted:codePoints>=1&&codePoints<=4,byteAccepted:utf8Bytes>=1&&utf8Bytes<=8};
}
function invalid(error){return {error,codePoints:null,utf16Units:null,utf8Bytes:null,legacyAccepted:false,codePointAccepted:false,byteAccepted:false};}

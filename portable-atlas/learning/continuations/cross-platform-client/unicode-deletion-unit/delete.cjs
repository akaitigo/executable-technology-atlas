'use strict';
// Atlas: normalize once, then remove one explicitly selected trailing unit.
const segmenter=new Intl.Segmenter('en',{granularity:'grapheme'});
const units=text=>Array.from({length:text.length},(_,i)=>text.charCodeAt(i));
function scalarValues(text){
 const values=[];
 for(let i=0;i<text.length;i++){
  const n=text.charCodeAt(i);
  if(n>=0xd800&&n<=0xdbff){
   const low=text.charCodeAt(i+1);if(!(low>=0xdc00&&low<=0xdfff))return null;
   values.push(0x10000+((n-0xd800)<<10)+(low-0xdc00));i++;
  }else if(n>=0xdc00&&n<=0xdfff)return null;
  else values.push(n);
 }
 return values;
}
function measure(text){
 const scalars=scalarValues(text),valid=scalars!==null;
 return {text:valid?text:null,escapedText:JSON.stringify(text),utf16Units:units(text),scalarValid:valid,scalars,
  utf8:valid?Array.from(Buffer.from(text,'utf8')):null,
  segments:valid?Array.from(segmenter.segment(text),part=>({text:part.segment,index:part.index,end:part.index+part.segment.length,scalars:scalarValues(part.segment),utf16Units:units(part.segment)})):null};
}
function validate(request){
 if(request===null||typeof request!=='object'||Array.isArray(request)||Object.keys(request).length!==2||!Object.hasOwn(request,'text')||!Object.hasOwn(request,'normalization'))return 'request-invalid';
 if(typeof request.text!=='string')return 'text-invalid';
 if(request.text.length>32)return 'text-too-long';
 if(scalarValues(request.text)===null)return 'unpaired-surrogate';
 if(!['none','NFC','NFD'].includes(request.normalization))return 'normalization-invalid';
 return null;
}
function removeLast(request){
 const reason=validate(request);if(reason)return {accepted:false,reason,payload:null};
 const text=request.normalization==='none'?request.text:request.text.normalize(request.normalization);
 const normalized=measure(text),parts=normalized.segments;
 const policyCut=parts.length?parts[parts.length-1].index:0;
 const lastScalar=Array.from(text).pop();
 const offsets={utf16:Math.max(0,text.length-1),scalar:lastScalar?text.length-lastScalar.length:0,grapheme:policyCut};
 return {accepted:true,reason:null,payload:{source:measure(request.text),normalization:request.normalization,
  normalizationCalls:request.normalization==='none'?0:1,normalized,
  methods:Object.entries(offsets).map(([method,cutOffset])=>({method,cutOffset,removedUnitCount:text.length?1:0,
   removedUtf16Units:units(text.slice(cutOffset)),after:measure(text.slice(0,cutOffset)),
   matchesAppPolicy:text.slice(0,cutOffset)===text.slice(0,policyCut)}))}};
}
module.exports={removeLast};

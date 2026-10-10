"""Focused receiver boundary tests; original is only expected test answer."""
import inspect,itertools,json,sys
sys.dont_write_bytecode=True
from calculate import decode,receive_huffman,receive_fixed,Refusal
from runner import snapshot

def main():
 before=snapshot();book=dict(zip('ABCD',['0','10','110','111']));fixed=dict(zip('ABCD',['00','01','10','11']));assert list(inspect.signature(decode).parameters)==['codebook','bitstream','count']
 count=0
 for n in range(5):
  for chars in itertools.product('ABCD',repeat=n):
   original=''.join(chars);payload=''.join(book[c] for c in original);fp=''.join(fixed[c] for c in original);header=format(n,'08b')+'00011010'
   assert receive_huffman(header+payload)['decoded']==original and receive_fixed(format(n,'08b')+fp)['decoded']==original;count+=1
 rejected=[]
 cases=[('cut-codeword',lambda:decode(book,'11',1)),('extra-bits',lambda:decode(book,'00',1)),('count-too-large',lambda:decode(book,'0',2)),('empty-wrong-count',lambda:decode(book,'',1)),('nonbinary',lambda:decode(book,'2',1)),('bool-count',lambda:decode(book,'0',True)),('prefix-book',lambda:decode({'A':'0','B':'01','C':'10','D':'11'},'0',1)),('duplicate-book',lambda:decode({'A':'0','B':'0','C':'10','D':'11'},'0',1)),('length-four',lambda:receive_huffman('0000000011011010')),('kraft-bad',lambda:receive_huffman('0000000000000000')),('nonbinary-header',lambda:receive_huffman('x000000000011010')),('short-header',lambda:receive_huffman('0')),('fixed-extra',lambda:receive_fixed('0000000000'))]
 for name,call in cases:
  try:call()
  except Refusal as e:rejected.append({'case':name,'code':str(e)})
  else:raise AssertionError('accepted '+name)
 flipped=receive_huffman('0000100000011010'+'00001010110110');assert flipped['decoded']=='AAAABBCC'
 assert before==snapshot();print(json.dumps({'messages_all_ABCD_length_0_to_4':count,'roundtrips_both':count*2,'decoder_parameters':list(inspect.signature(decode).parameters),'boundary_rejected':rejected,'valid_bitflip_counterexample':{'original':'AAAABBCD','original_payload':'00001010110111','flipped_payload':'00001010110110','decoded':flipped['decoded'],'receiver_accepts':True},'unit_sha_mtime_unchanged':True}));return 0
if __name__=='__main__':sys.exit(main())

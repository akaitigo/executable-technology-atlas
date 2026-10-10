"""Atlas: finite sample-boundary conversion; integer rounding and exact rational differences."""
from fractions import Fraction
import re
class InputError(ValueError):
 def __init__(self,code):super().__init__(code);self.code=code
def need(ok,code):
 if not ok:raise InputError(code)
def validate(d):
 need(type(d) is dict and set(d)=={'title','schema','nominal_rate_hz','time_unit','origin_ms','rounding','cases'},'input_keys')
 need(type(d['schema']) is int and d['schema']==1,'schema')
 rate=d['nominal_rate_hz'];need(type(rate) is int,'sample_rate_type');need(rate>0,'sample_rate_range');need(rate==48000,'fixed_rate')
 need(d['time_unit']=='ms','time_unit');need(type(d['origin_ms']) is int and d['origin_ms']==0,'time_origin');need(d['rounding']=='nearest_half_up_nonnegative','rounding_rule')
 need(type(d['cases']) is list and len(d['cases'])==8,'case_count');seen=set()
 for c in d['cases']:
  need(type(c) is dict and set(c)=={'id','block_samples','blocks','clock_ppm'},'case_keys');need(type(c['id']) is str and re.fullmatch(r'[a-z-]{1,32}',c['id']) is not None,'case_id');need(c['id'] not in seen,'duplicate_case');seen.add(c['id'])
  need(type(c['block_samples']) is int and 1<=c['block_samples']<=1024,'block_samples');need(type(c['blocks']) is int and 0<=c['blocks']<=300,'blocks');need(type(c['clock_ppm']) is int and c['clock_ppm'] in [0,100],'clock_ppm')
 return d
def round_sample_ms(samples,rate):
 quotient,remainder=divmod(samples*1000,rate)
 return quotient+int(2*remainder>=rate)
def calculate(d,case_id):
 validate(d);found=[c for c in d['cases'] if c['id']==case_id];need(len(found)==1,'unknown_case');c=found[0];rate=d['nominal_rate_hz'];B=c['block_samples'];ppm=c['clock_ppm'];step=round_sample_ms(B,rate);accumulated=0;rows=[]
 for k in range(c['blocks']+1):
  if k:accumulated+=step
  N=k*B;nominal=Fraction(N*1000,rate);reference=Fraction(N*1000*1000000,rate*(1000000+ppm));absolute=round_sample_ms(N,rate)
  rows.append({'boundary_index':k,'sample_position':N,'nominal_ms':str(nominal),'reference_ms':str(reference),'absolute_rounded_ms':absolute,'interval_sum_ms':accumulated,'absolute_round_error_ms':str(absolute-nominal),'interval_round_error_ms':str(accumulated-nominal),'clock_error_ms':str(nominal-reference),'absolute_total_error_ms':str(absolute-reference),'interval_total_error_ms':str(accumulated-reference)})
 return {'case_id':case_id,'status':'calculated','nominal_rate_hz':rate,'time_unit':'ms','origin_ms':0,'rounding':d['rounding'],'block_samples':B,'blocks':c['blocks'],'clock_ppm':ppm,'assumed_rate_hz':str(Fraction(rate*(1000000+ppm),1000000)),'exact_interval_ms':str(Fraction(B*1000,rate)),'rounded_interval_ms':step,'rows':rows,'final':rows[-1],'device_clock_measured':False,'audio_rendered':False,'RTP_executed':False}

"""Atlas: one short calculation batch, not an audio device or clock measurement."""
import copy,datetime,hashlib,json,os,platform,time
from pathlib import Path
from model import calculate,InputError
ROOT=Path(__file__).resolve().parent
def main():
 priority=os.getpriority(os.PRIO_PROCESS,0)
 if priority!=10:raise RuntimeError('Atlas actual nice 10 required')
 d=json.loads((ROOT/'fixtures.json').read_text());start=time.monotonic();cases=[calculate(d,c['id']) for c in d['cases']];refusals=[]
 tests=[('extra_key',lambda d:d.update(extra=True),'empty','input_keys'),('bool_rate',lambda d:d.update(nominal_rate_hz=True),'empty','sample_rate_type'),('zero_rate',lambda d:d.update(nominal_rate_hz=0),'empty','sample_rate_range'),('different_rate',lambda d:d.update(nominal_rate_hz=44100),'empty','fixed_rate'),('negative_samples',lambda d:d['cases'][0].update(block_samples=-1),'empty','block_samples'),('bool_blocks',lambda d:d['cases'][0].update(blocks=True),'empty','blocks'),('negative_blocks',lambda d:d['cases'][0].update(blocks=-1),'empty','blocks'),('fractional_samples',lambda d:d['cases'][0].update(block_samples=1.5),'empty','block_samples'),('too_many_blocks',lambda d:d['cases'][0].update(blocks=301),'empty','blocks'),('too_large_block',lambda d:d['cases'][0].update(block_samples=1025),'empty','block_samples'),('unsupported_clock',lambda d:d['cases'][0].update(clock_ppm=-100),'empty','clock_ppm'),('wrong_rounding',lambda d:d.update(rounding='ties_to_even'),'empty','rounding_rule'),('wrong_units',lambda d:d.update(time_unit='seconds'),'empty','time_unit'),('nonzero_origin',lambda d:d.update(origin_ms=1),'empty','time_origin'),('unknown_case',lambda d:None,'unknown','unknown_case'),('no_cases',lambda d:d.update(cases=[]),'empty','case_count'),('duplicate_case',lambda d:d['cases'][1].update(id='empty'),'empty','duplicate_case')]
 for name,mutate,case_id,code in tests:
  changed=copy.deepcopy(d);mutate(changed)
  try:calculate(changed,case_id)
  except InputError as e:
   if e.code!=code:raise RuntimeError(name+': unexpected refusal '+e.code)
   refusals.append({'case':name,'code':e.code,'classification':'expected_input_refusal','timeline_returned':False})
  else:raise RuntimeError(name+': unexpectedly accepted')
 return {'title':'Atlas sample timebase saved calculation','schema':1,'status':'observed','observed_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'runtime':{'python':platform.python_version(),'implementation':platform.python_implementation(),'system':platform.system(),'machine':platform.machine()},'priority_observed':priority,'fixture_sha256':hashlib.sha256((ROOT/'fixtures.json').read_bytes()).hexdigest(),'cases':cases,'input_refusals':refusals,'calculation_elapsed_seconds':time.monotonic()-start,'device_clock_measured':False,'audio_rendered':False,'RTP_executed':False}
if __name__=='__main__':print(json.dumps(main(),ensure_ascii=False,indent=2))

"""Atlas: compare saved integer producer output with Fraction and the fixed preimplementation hand table."""
import argparse,copy,hashlib,json
from fractions import Fraction as F
from pathlib import Path
ROOT=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def need(ok,label):
 if not ok:raise ValueError(label)
def rounded(x):
 lower=x.numerator//x.denominator
 # Independent nearest-value comparison; the upper integer wins an exact tie.
 return lower if x-lower<F(1,2) else lower+1
def check(data):
 fixture=json.loads((ROOT/'fixtures.json').read_text());hand=json.loads((ROOT/'hand-oracle.json').read_text());need(data['status']=='observed' and data['priority_observed']==10 and data['fixture_sha256']==sha(ROOT/'fixtures.json'),'header/input binding');need(not data['device_clock_measured'] and not data['audio_rendered'] and not data['RTP_executed'],'scope');need([c['case_id'] for c in data['cases']]==[c['id'] for c in fixture['cases']],'case identities')
 count=0;checkpoints=0
 for actual,inp,literal in zip(data['cases'],fixture['cases'],hand['cases']):
  B=inp['block_samples'];n=inp['blocks'];ppm=inp['clock_ppm'];interval=F(B,48);multiplier=F(1000000+ppm,1000000)
  need(actual['case_id']==literal['id'] and actual['status']=='calculated' and actual['nominal_rate_hz']==48000 and actual['origin_ms']==0 and actual['time_unit']=='ms' and actual['rounding']=='nearest_half_up_nonnegative','case conventions');need(actual['block_samples']==B and actual['blocks']==n and actual['clock_ppm']==ppm,'input values');need(actual['assumed_rate_hz']==str(48000*multiplier) and actual['exact_interval_ms']==str(interval) and actual['rounded_interval_ms']==rounded(interval),'interval/rate');need(not actual['device_clock_measured'] and not actual['audio_rendered'] and not actual['RTP_executed'],'case scope')
  need(len(actual['rows'])==n+1,'boundary count');need(actual['final']==actual['rows'][-1],'final row binding')
  for k,row in enumerate(actual['rows']):
   t=k*interval;ref=t/multiplier;A=rounded(t);C=k*rounded(interval);expected={'boundary_index':k,'sample_position':k*B,'nominal_ms':str(t),'reference_ms':str(ref),'absolute_rounded_ms':A,'interval_sum_ms':C,'absolute_round_error_ms':str(A-t),'interval_round_error_ms':str(C-t),'clock_error_ms':str(t-ref),'absolute_total_error_ms':str(A-ref),'interval_total_error_ms':str(C-ref)};need(row==expected,'boundary exact Fraction comparison');need(abs(F(row['absolute_round_error_ms']))<=F(1,2),'absolute rounding bound');need(F(row['interval_total_error_ms'])==F(row['interval_round_error_ms'])+F(row['clock_error_ms']),'error decomposition');count+=1
  need({k:actual['final'][k] for k in literal['final']}==literal['final'],'fixed final hand values')
  for point in literal['checkpoints']:
   row=actual['rows'][point[0]];need([row[k] for k in hand['checkpoint_fields']]==point,'fixed hand checkpoint');checkpoints+=1
 need(count==hand['expected_total_boundaries']==618 and checkpoints==hand['expected_checkpoints']==29,'total counts')
 expected_codes={'extra_key':'input_keys','bool_rate':'sample_rate_type','zero_rate':'sample_rate_range','different_rate':'fixed_rate','negative_samples':'block_samples','bool_blocks':'blocks','negative_blocks':'blocks','fractional_samples':'block_samples','too_many_blocks':'blocks','too_large_block':'block_samples','unsupported_clock':'clock_ppm','wrong_rounding':'rounding_rule','wrong_units':'time_unit','nonzero_origin':'time_origin','unknown_case':'unknown_case','no_cases':'case_count','duplicate_case':'duplicate_case'}
 need(len(data['input_refusals'])==17 and {r['case']:r['code'] for r in data['input_refusals']}==expected_codes,'refusal matrix');need(all(r['classification']=='expected_input_refusal' and r['timeline_returned'] is False for r in data['input_refusals']),'refusal is not a timeline')
 return {'cases':8,'boundaries':count,'fixed_checkpoints':checkpoints,'input_refusals':17}
def verify(run):
 run=run.resolve();need(run.parent==ROOT/'observations','owned run');r=json.loads((run/'report.json').read_text());need(r['status']=='observed' and r['child_reaped'] and r['output_complete'] and r['exit_code']==0 and not r['timed_out'],'child completion');need(r['priority_guard']['ready'] and r['priority_guard']['observed_nice']==10,'actual nice');need(sha(ROOT/r['resource_gate_file'])==r['resource_gate_sha256'] and 0<=r['resource_gate_age_seconds']<=60,'fresh resource binding')
 for name,h in r['sources'].items():need(sha(ROOT/name)==h,'source '+name)
 for stem in ['stdout','stderr','result']:need(sha(run/r[stem+'_file'])==r[stem+'_sha256'],'saved '+stem)
 d=json.loads((run/'result.json').read_text());need(d==json.loads((run/'stdout.txt').read_text()),'stdout/result');counts=check(d)
 edits=[('missing_case',lambda d:d['cases'].pop()),('missing_empty_origin',lambda d:d['cases'][0]['rows'].clear()),('half_even_error',lambda d:d['cases'][2]['rows'][1].update(absolute_rounded_ms=0)),('sample_as_millisecond',lambda d:d['cases'][1]['rows'][1].update(nominal_ms='23')),('wrong_cumulative_time',lambda d:d['cases'][5]['rows'][3].update(interval_sum_ms=64)),('wrong_clock_sign',lambda d:d['cases'][7]['rows'][-1].update(clock_error_ms='-6400/10001')),('clock_counted_as_rounding',lambda d:d['cases'][7]['rows'][-1].update(absolute_round_error_ms='6400/10001')),('wrong_origin',lambda d:d['cases'][0].update(origin_ms=1)),('wrong_time_unit',lambda d:d['cases'][4].update(time_unit='seconds')),('stale_condition',lambda d:d['cases'][7].update(case_id='thirds-long')),('false_device_measurement',lambda d:d.update(device_clock_measured=True)),('refusal_returns_timeline',lambda d:d['input_refusals'][0].update(timeline_returned=True))];detected=[]
 for name,edit in edits:
  x=copy.deepcopy(d);edit(x)
  try:check(x)
  except (ValueError,KeyError,IndexError,TypeError):detected.append(name)
  else:raise ValueError('undetected mutation '+name)
 return {'title':'Atlas saved sample-timebase verification','passed':True,**counts,'alterations_detected':detected,'producer_imported':False,'producer_executed':False,'device_clock_measured':False,'run':str(run.relative_to(ROOT))}
if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--run',required=True);a=p.parse_args();print(json.dumps(verify(ROOT/a.run),ensure_ascii=False,indent=2))

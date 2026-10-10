# SPDX-License-Identifier: Apache-2.0
def measure(rows,h):
 post=[x for x in rows if x['t']>=4.];inside=[abs(x['y']-.5)<=.05 for x in post]
 first=next((x['t'] for x,b in zip(post,inside) if b),None)
 settled=next((x['t'] for i,x in enumerate(post) if inside[i] and all(inside[i:]) and 8.-x['t']>=1.),None)
 reexits=[post[i]['t'] for i in range(1,len(post)) if inside[i-1] and not inside[i]]
 high=[x for x in rows[:-1] if x['t']<4.];low=[x for x in rows[:-1] if x['t']>=4.]
 return dict(first_entry_time=first,settled_time=settled,settling_status='SETTLED_IN_OBSERVATION_WINDOW' if settled is not None else 'NOT_SETTLED_IN_WINDOW',reexit_times=reexits,peak_excess_after_drop=max(0.,max(x['y']-.5 for x in post)),high_clipped_steps=sum(x['clipped'] for x in high),low_clipped_steps=sum(x['clipped'] for x in low),stopped_steps=sum(x['integral_stopped'] for x in rows[:-1]),y_at_drop=post[0]['y'],z_at_drop=post[0]['z'],y_final=rows[-1]['y'],z_final=rows[-1]['z'],observation_window=[4.,8.],band=.05,minimum_remaining_duration=1.,classification='sample points only')

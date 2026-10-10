# SPDX-License-Identifier: Apache-2.0
import math
def step(y,z,reference,h,mode,ki):
 error=reference-y;requested=error+ki*z
 actual=requested if mode=='free' else max(-1.,min(1.,requested))
 stop=mode=='conditional' and ((requested>=1. and error>0.) or (requested<=-1. and error<0.))
 # Both next states use the same old y/z/error and the held actual input.
 y_next=actual+(y-actual)*math.exp(-h)
 z_next=z if stop else z+h*error
 return dict(y=y,z=z,r=reference,e=error,u_requested=requested,u_actual=actual,clipped=actual!=requested,integral_stopped=stop,y_next=y_next,z_next=z_next)

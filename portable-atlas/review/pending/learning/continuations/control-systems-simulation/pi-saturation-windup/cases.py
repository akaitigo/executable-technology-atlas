# SPDX-License-Identifier: Apache-2.0
def configs():return [dict(h=h,mode=m,ki=k) for h in [.25,.5] for m in ['free','saturated','conditional'] for k in [0,1]]
def valid(c):return type(c) is dict and set(c)=={'h','mode','ki'} and type(c['h']) in [int,float] and c['h'] in [.25,.5] and type(c['mode']) is str and c['mode'] in ['free','saturated','conditional'] and type(c['ki']) is int and c['ki'] in [0,1]

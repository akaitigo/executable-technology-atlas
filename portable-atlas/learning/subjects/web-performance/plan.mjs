export const CONFIG={cells:16,columns:4,iterations:8,warmupRounds:2,measuredRounds:5,timerCases:[{id:'idle',delayMs:20,blockMs:0},{id:'long-timer',delayMs:100,blockMs:0},{id:'blocking',delayMs:20,blockMs:120}]};
export function validateIterations(value){return Number.isInteger(value)&&[0,8].includes(value);}
export const widthFor=(cell,iteration)=>96+(cell%4)*8+(iteration%2)*4;
export function widths(iterations){if(!validateIterations(iterations))throw new RangeError('iterations must be 0 or 8');return Array.from({length:16},(_,i)=>iterations?widthFor(i,iterations-1):80);}
export function orderFor(round){return round%2?['batched','interleaved']:['interleaved','batched'];}

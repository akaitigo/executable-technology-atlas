import {evaluated,record} from './journal.mjs';
export const evaluationOrdinal=evaluated('counter');
export let count=0;
export function increment(delta=1){
  if(!Number.isInteger(delta)||Math.abs(delta)>2)throw new RangeError('delta must be integer -2..2');
  const before=count;count+=delta;record('counter-mutation',{before,delta,after:count});return count;
}

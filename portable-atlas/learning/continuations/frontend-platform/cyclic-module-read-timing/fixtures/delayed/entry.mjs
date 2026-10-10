import { read } from './a.mjs';
console.log(JSON.stringify({ event: 'entry:eval' }));
export const final = read();
console.log(JSON.stringify({ event: 'entry:final', value: final }));

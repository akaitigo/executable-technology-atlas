import { read, setValue } from './a.mjs';
console.log(JSON.stringify({ event: 'entry:eval' }));
const snapshot = read();
console.log(JSON.stringify({ event: 'entry:snapshot', value: snapshot }));
setValue(2);
export const final = read();
console.log(JSON.stringify({ event: 'entry:snapshot-after', value: snapshot }));
console.log(JSON.stringify({ event: 'entry:final', value: final }));

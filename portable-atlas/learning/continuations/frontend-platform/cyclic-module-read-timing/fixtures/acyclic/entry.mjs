import { eager } from './b.mjs';
console.log(JSON.stringify({ event: 'entry:eval' }));
export const final = eager;
console.log(JSON.stringify({ event: 'entry:final', value: final }));

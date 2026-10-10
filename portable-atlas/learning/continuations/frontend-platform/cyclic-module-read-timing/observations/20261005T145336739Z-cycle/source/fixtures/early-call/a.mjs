import { read } from './b.mjs';
console.log(JSON.stringify({ event: 'A:eval' }));
export let value = 1;
console.log(JSON.stringify({ event: 'A:init', value: value }));
export { read };
export function setValue(next) { value = next; console.log(JSON.stringify({ event: 'A:update', value: value })); }

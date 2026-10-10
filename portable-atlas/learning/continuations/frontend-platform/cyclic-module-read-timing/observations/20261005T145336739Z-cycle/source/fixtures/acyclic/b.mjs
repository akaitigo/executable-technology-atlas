import { value } from './a.mjs';
console.log(JSON.stringify({ event: 'B:eval' }));
console.log(JSON.stringify({ event: 'B:before-read' }));
export const eager = value;
console.log(JSON.stringify({ event: 'B:read', value: eager }));
export function read() { return value; }

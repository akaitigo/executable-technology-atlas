import { value } from './a.mjs';
console.log(JSON.stringify({ event: 'B:eval' }));
export function read() {
  console.log(JSON.stringify({ event: 'B:before-read' }));
  const result = value;
  console.log(JSON.stringify({ event: 'B:read', value: result }));
  return result;
}
console.log(JSON.stringify({ event: 'B:ready' }));
export const eager = read();

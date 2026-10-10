import * as counter from './counter.mjs';
import {evaluated,record} from './journal.mjs';
evaluated('importer-b');
const {count:snapshot}=counter;
export function read(){return {live:counter.count,snapshot};}
export function mutate(delta=1){return counter.increment(delta);}
export function namespace(){return counter;}
export function assignNamespace(){
  try{counter.count=99;return {rejected:false};}
  catch(error){const result={rejected:true,name:error.name,message:error.message};record('namespace-assignment-rejected',result);return result;}
}

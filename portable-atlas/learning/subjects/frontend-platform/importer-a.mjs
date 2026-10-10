import {count,increment} from './counter.mjs';
import * as counterNamespace from './counter.mjs';
import {evaluated,record} from './journal.mjs';
evaluated('importer-a');
const snapshot=count;
export function read(){return {live:count,snapshot};}
export function mutate(delta=1){return increment(delta);}
export function namespace(){return counterNamespace;}
export function assignImportedBinding(){
  try{count=99;return {rejected:false};}
  catch(error){const result={rejected:true,name:error.name,message:error.message};record('import-binding-assignment-rejected',result);return result;}
}

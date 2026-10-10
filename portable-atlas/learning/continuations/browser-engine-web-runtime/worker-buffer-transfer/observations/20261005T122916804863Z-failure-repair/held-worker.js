// Dedicated Worker, authored fixed protocol. Data messages counted, probes excluded.
let receivedData=0,receivedIDs=[];
self.onmessage=event=>{
  const m=event.data;
  if(m.kind==='probe'){self.postMessage({id:m.id,kind:'probe-ack',received_data:receivedData,received_ids:[...receivedIDs]});return}
  if(m.kind!=='data'){self.postMessage({id:m.id,kind:'unsupported'});return}
  receivedData++;receivedIDs.push(m.id);
  const view=new Uint8Array(m.buffer),before=Array.from(view);
  let sum=0;for(const byte of view)sum+=byte;
  view[0]=m.mutate_first_to;
  self.postMessage({id:m.id,kind:'data-ack',received_data:receivedData,received_ids:[...receivedIDs],byte_length:m.buffer.byteLength,before,after:Array.from(view),sum});
};

const actualHandler=self.onmessage;let held=false;self.onmessage=async event=>{if(!held&&event.data.kind==='probe'){held=true;await fetch('/qa-release')}actualHandler(event)};

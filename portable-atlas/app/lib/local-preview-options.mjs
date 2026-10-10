// Local preview only. Binding always stays 127.0.0.1; this is not deployment configuration.
export function previewPort(args){
  if(args.length===0)return 0;
  if(args.length!==2||args[0]!=='--port'||!/^(0|[1-9][0-9]*)$/.test(args[1]))throw Error('usage: node scripts/local-learning-preview.mjs [--port 0..65535]');
  const port=Number(args[1]);
  if(!Number.isSafeInteger(port)||port>65535)throw Error('port must be an integer 0..65535');
  return port;
}

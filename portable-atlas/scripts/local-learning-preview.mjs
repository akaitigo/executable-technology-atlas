import http from 'node:http';
import { localReaderHandler } from '../app/lib/local-reader-http.mjs';
import { previewPort } from '../app/lib/local-preview-options.mjs';
const port=previewPort(process.argv.slice(2));
const server=http.createServer(localReaderHandler);
server.listen(port,'127.0.0.1',()=>console.log(`Mac local learning: http://127.0.0.1:${server.address().port}/`));
for(const signal of ['SIGINT','SIGTERM'])process.on(signal,()=>server.close(()=>process.exit(0)));

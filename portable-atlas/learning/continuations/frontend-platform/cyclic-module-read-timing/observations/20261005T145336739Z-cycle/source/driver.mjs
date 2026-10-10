// This process owns one module graph. No top-level await or internal engine trace.
const allowed = ['immediate','delayed','early-call','acyclic','live-update'];
const id = process.argv[2];
if (!allowed.includes(id)) { console.error(JSON.stringify({class:'InputRefusal',message:'case id outside finite fixture'})); process.exitCode=2; }
else {
  console.log(JSON.stringify({process:{pid:process.pid,node:process.version}}));
  console.log(JSON.stringify({event:'driver:import'}));
  import(new URL(`./fixtures/${id}/entry.mjs`, import.meta.url)).then(module => {
    console.log(JSON.stringify({event:'driver:done',value:module.final}));
  }).catch(error => {
    console.log(JSON.stringify({event:'driver:failed'}));
    // Keep the actual exception name/message, without a stack containing host paths.
    console.error(JSON.stringify({class:error.name,message:error.message}));
    process.exitCode=1;
  });
}

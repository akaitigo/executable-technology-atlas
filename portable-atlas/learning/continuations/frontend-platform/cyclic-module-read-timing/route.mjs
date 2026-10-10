const routes={'循環即時read':'immediate','初期化後の関数read':'delayed','関数だが早くcall':'early-call','循環なし':'acyclic','live binding更新':'live-update','予想入力/古い答え':'UI controls'};
console.log(JSON.stringify({routes,excluded:['TLA','bundler','browser realm','URL cache','full spec'],status:'finite-unit-only'}));

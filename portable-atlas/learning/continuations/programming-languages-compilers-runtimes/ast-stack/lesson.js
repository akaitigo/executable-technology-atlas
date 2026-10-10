/* Atlas: display saved observations only; never execute the producer or VM. */
"use strict";
(() => {
  const PUBLIC_DATA_SHA = "2a2ed6f99f0d59a30b23f4a902927938e35829120eebc5abb3d6c831f6863590";
  const $ = id => document.getElementById(id);
  const conditions = [
    ["precedence", "2 + 3 * 4", "正常対照。加算と乗算のどちらが先に完了するか。"],
    ["parentheses", "(2 + 3) * 4", "括弧が AST と命令順をどう変えるか。"],
    ["two-products", "2 * 3 + 4 * 5", "二つの積を加える途中に何を保持するか。"],
    ["zero", "0", "正常な値 0 と、値なしの拒否を分ける。"],
    ["reuse-constant", "2 + 2 * 2", "定数の個数と CONST 命令の個数を分ける。"],
    ["index-upper", "上限外の index", "定数表 [2]、命令 CONST 1。"],
    ["index-negative", "負の index", "定数表 [2]、命令 CONST -1。"],
    ["add-empty", "ADD の値不足", "空の stack に ADD。"],
    ["mul-one", "MUL の値不足", "定数表 [2]、CONST 0 の次に MUL。"],
    ["final-empty", "空の終端", "定数表も命令列も空。"],
    ["final-extra", "余分な値の終端", "定数表 [2,3]、CONST 0、CONST 1 で終わる。"],
    ["unknown-opcode", "未知の命令", "この VM にない SUB。減算を追加したケースではない。"]
  ];
  let selected = conditions[0][0], generation = 0, busy = false, loaded = null, stage = 0;
  const json = x => JSON.stringify(x, null, 2);
  function clearResult() {
    loaded = null; stage = 0;
    $("result").hidden = true; $("answer").hidden = true; $("answer").textContent = "";
    for (const id of ["measurement","phase-title","phase-note","diagram","current-step","ast","constants","code-table","mapping","comparison","raw"]) $(id).replaceChildren();
    $("raw-details").open = false; $("mapping-details").open = false;
    $("previous").disabled = $("next").disabled = $("answer-button").disabled = true;
  }
  function invalidate(clearPrediction = false) {
    generation++; busy = false; clearResult();
    if (clearPrediction) $("prediction").value = "";
    $("read").disabled = !$("prediction").value.trim();
    $("load-state").className = "";
    $("load-state").textContent = "予想を書いてから保存結果を読めます。条件・予想の変更で前の結果を消します。";
  }
  function choose(id) {
    selected = id; invalidate(true);
    for (const button of $("choices").children) button.setAttribute("aria-pressed", String(button.dataset.case === id));
    $("case-description").textContent = conditions.find(c => c[0] === id).slice(1).join(" — ");
  }
  async function hash(text) {
    if (!globalThis.crypto?.subtle) throw new Error("この環境では SHA-256 の照合を利用できません");
    const bytes = await crypto.subtle.digest("SHA-256", new TextEncoder().encode(text));
    return Array.from(new Uint8Array(bytes), b => b.toString(16).padStart(2,"0")).join("");
  }
  async function readSaved() {
    if (busy || !$("prediction").value.trim()) return;
    invalidate(); const token = generation, caseId = selected;
    busy = true; $("read").disabled = true; $("load-state").textContent = "保存した記録の SHA-256 と形を確認しています…";
    try {
      const text = globalThis.ATLAS_DATA_TEXT;
      if (typeof text !== "string") throw new Error("data.js の保存データが見つかりません");
      if (await hash(text) !== PUBLIC_DATA_SHA) throw new Error("同梱データのダイジェストが一致しません");
      const bundle = JSON.parse(text);
      if(bundle.schemaVersion!==2||bundle.kind!=="atlas-selected-historical-observation")throw Error("配布データの契約が違います");
      if (await hash(bundle.run_text) !== bundle.public_run_sha256 || await hash(bundle.expected_text) !== bundle.public_expected_sha256) throw new Error("配布用の観測データまたは固定期待値の照合が不一致です");
      const run = JSON.parse(bundle.run_text), expected = JSON.parse(bundle.expected_text);
      const cases = run.records.filter(c => c.kind === "case");
      if (!run.collection_complete || !run.input_unchanged || run.target_count !== 1 || cases.length !== 12 || cases.some((c,i) => c.id !== conditions[i][0])) throw new Error("完成した固定 12 条件の記録ではありません");
      const c = cases.find(c => c.id === caseId);
      const wanted = [...expected.normal,...expected.rejections].find(c => c.id === caseId);
      if (!c || !wanted || !Array.isArray(c.vm.trace) || !c.vm.trace.length || !["normal","expected-rejection"].includes(c.classification)) throw new Error("選んだ条件の記録を解釈できません");
      if (token !== generation) return;
      loaded = {c, wanted, runAt: run.started_at, environment: run.records[0]}; stage = 0;
      $("load-state").textContent = "選別した保存結果です。原票全文とは別の配布用データを照合しました。新しい Python 実行は行っていません。";
      render();
    } catch (error) {
      if (token !== generation) return;
      clearResult(); $("load-state").className = "error";
      $("load-state").textContent = "資料を読めませんでした：" + error.message + "。これは VM の意図した拒否とは別です。README と保存ファイルを確認し、ファイルを復元した後にページを読み直してください。";
    } finally {
      if (token === generation) { busy = false; $("read").disabled = !$("prediction").value.trim(); }
    }
  }
  function textElement(tag, text, cls) { const e = document.createElement(tag); e.textContent = text; if(cls)e.className=cls; return e; }
  function drawFlow(texts) {
    $("diagram").replaceChildren();
    texts.forEach((text,i) => { if(i)$("diagram").append(textElement("span","→","arrow")); $("diagram").append(textElement("span",text,"box")); });
  }
  function astText(node, depth = 0) {
    const own = "  ".repeat(depth) + node.id + " " + node.kind + (node.kind === "Integer" ? " " + node.value : "") + " [" + node.span.join(",") + ")";
    const children = node.child ? [node.child] : node.left ? [node.left,node.right] : [];
    return [own,...children.map(n => astText(n,depth+1))].join("\n");
  }
  function render() {
    const {c, runAt, environment} = loaded, terminal = c.vm.trace.length + 1;
    const compiled = c.compiled || {constants:c.constants,code:c.code,origins:[],node_mapping:[]};
    const step = stage > 0 && stage < terminal ? c.vm.trace[stage-1] : null;
    $("result").hidden = false; $("answer").hidden = true; $("answer").textContent = "";
    $("raw-details").open = false;
    $("measurement").textContent = "実行日時 " + runAt + " / " + environment.platform + " / Python " + environment.python_version.split(" ")[0];
    $("phase-title").textContent = stage === 0 ? "開始前：stack は空" : stage === terminal ? "終端の対照" : "時点 " + stage + "：pc " + step.pc + (step.phase === "finish" ? " の終端検査" : " の命令");
    $("phase-note").textContent = stage === 0 ? "AST、定数表、命令列を先に対応させ、次の時点で最初の命令を追います。" : stage === terminal ? "保存した実測と、実装前の固定期待を答えで照合できます。" : step.status === "rejected" ? "VM がここで拒否しました。この操作では stack を減らさず、後続命令へ進みません。" : "この命令の直前と直後です。右端が stack の頂点です。";
    $("previous").disabled = stage === 0; $("next").disabled = stage === terminal;
    $("answer-button").disabled = stage !== terminal;
    $("ast").textContent = c.ast ? astText(c.ast) : "この条件は VM に不正な命令列を直接渡す対照です。対応する式や AST はありません。";
    $("constants").textContent = "定数表（index → 値）：" + (compiled.constants.map((v,i) => i + " → " + v).join("、") || "空");
    $("code-table").replaceChildren();
    compiled.code.forEach((op,pc) => { const origin = compiled.origins[pc], row = document.createElement("tr");
      if(step && pc === step.pc)row.className = "current";
      [pc,op.join(" "),origin?.node_id || "直接入力",origin ? "[" + origin.span.join(",") + ")" : "—"].forEach(t => row.append(textElement("td",String(t)))); $("code-table").append(row); });
    $("mapping").textContent = c.ast ? json(compiled.node_mapping) : "AST 対応なし";
    $("current-step").replaceChildren(); $("comparison").replaceChildren();
    let visible;
    if(stage === 0) { drawFlow(["AST / 直接入力", "定数表・命令列", "stack []"]); visible = {id:c.id,stage:"before",constants:compiled.constants,code:compiled.code,ast:c.ast || null,node_mapping:compiled.node_mapping,stack:[]}; }
    else if(step) { drawFlow([step.phase === "finish" ? "終端検査" : "pc " + step.pc + " " + step.instruction.join(" "), "前 " + JSON.stringify(step.before), "後 " + JSON.stringify(step.after)]);
      const detail = step.diagnostic ? "診断 " + step.diagnostic : step.constant_index !== null ? "定数 index " + step.constant_index + " → 値 " + step.constant_value : "演算に使う値：right " + step.operands.right + "、left " + step.operands.left;
      $("current-step").append(textElement("p",detail)); visible = {id:c.id,stage,step}; }
    else { const returned = c.vm.status === "returned";
      drawFlow([returned ? "全命令を実行" : "意図した拒否で停止", "終端 stack " + JSON.stringify(c.vm.final_stack), returned ? "VM の値 " + c.vm.value : "値なし"]);
      $("comparison").append(textElement("p", returned ? "木評価器の値 " + c.tree_value + " / VM の値 " + c.vm.value + " / 一致 " + c.tree_vm_equal + " / 最大 stack 高 " + c.vm.max_height : "診断 " + c.vm.diagnostic.code + " / pc " + c.vm.diagnostic.pc + " / 実行済み命令 " + c.vm.executed_instructions + "。値 0 を返したわけではありません。")); visible = c; }
    $("raw").textContent = json(visible);
  }
  for (const [id,label] of conditions) { const button = textElement("button",label); button.dataset.case = id; button.type = "button"; button.addEventListener("click",() => choose(id)); $("choices").append(button); }
  $("prediction").addEventListener("input",() => invalidate());
  $("reset").addEventListener("click",() => choose(conditions[0][0]));
  $("read").addEventListener("click",readSaved);
  $("previous").addEventListener("click",() => { if(loaded && stage > 0){stage--;render();} });
  $("next").addEventListener("click",() => { if(loaded && stage < loaded.c.vm.trace.length+1){stage++;render();} });
  $("answer-button").addEventListener("click",() => {
    if(!loaded || stage !== loaded.c.vm.trace.length+1) return;
    const {c,wanted} = loaded; $("answer").replaceChildren(textElement("p","あなたの予想：" + $("prediction").value));
    $("answer").append(textElement("p",c.classification === "normal" ? "固定期待の値 " + wanted.value + " と実測の値 " + c.vm.value + " を対照しました。命令順・出所・各 stack の一致は保存値検査で別に確認しています。" : "固定期待の診断 " + wanted.diagnostic + "・pc " + wanted.pc + "・stack " + JSON.stringify(wanted.stack) + " と保存した拒否を対照します。"));
    $("answer").append(textElement("pre",json(wanted))); $("answer").hidden = false;
  });
  choose(selected);
})();

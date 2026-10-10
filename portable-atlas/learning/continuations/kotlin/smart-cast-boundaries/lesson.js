"use strict";
(() => {
  const reportPath = "observations/operational-revision-20261006T054006019240Z/run.json";
  const reportDigest = "0020335de226b162219c9a2ada5a944b35b85ee033f887e813cc8fc6aae6072b";
  const expectedDigest = "dbf866edb1797dbd856c4c8612216540388087848c8cc0e05347d2729f6d6181";
  const el = id => document.getElementById(id);
  const operations = ["mutable-snapshot", "getter-snapshot", "getter-repeated-assertion", "mutable-property-rejected", "custom-getter-rejected"];
  const labels = {"mutable-snapshot":"var → snapshot", "getter-snapshot":"getter → snapshot", "getter-repeated-assertion":"getter再読取り＋!!", "mutable-property-rejected":"varを直接smart cast", "custom-getter-rejected":"getterを直接smart cast"};
  const snippets = {
    "mutable-snapshot":"val snapshot: String? = source.value\nsource.value = if (initial == null) \"Ada\" else null\nif (snapshot != null) println(snapshot.length)",
    "getter-snapshot":"val snapshot: String? = source.value\nif (snapshot != null) println(snapshot.length)\n// 使い終えた後に、比較のためもう一度getterを読む",
    "getter-repeated-assertion":"if (source.value != null) {\n    println(source.value!!.length)\n}",
    "mutable-property-rejected":"class MutableBox(var value: String?)\nif (box.value != null) {\n    return box.value.length\n}",
    "custom-getter-rejected":"// val value: String? に独自getterがある\nif (box.value != null) {\n    return box.value.length\n}"
  };
  const flows = {
    "mutable-snapshot":["1. propertyの値を受け取る","2. 元propertyを逐次変更","3. 保存値を検査・利用"],
    "getter-snapshot":["1. getterを1回読む","2. 保存値を検査・利用","3. 利用後に比較用の別読取り"],
    "getter-repeated-assertion":["1. getterを読みguardで検査","2. guard内でもう一度読む","3. 2回目の値へ!!を適用"],
    "mutable-property-rejected":["1. var propertyを検査","2. 同じpropertyを再読取り","3. smart castできるかcompileで確認"],
    "custom-getter-rejected":["1. 独自getterを検査","2. 同じgetterを再読取り","3. smart castできるかcompileで確認"]
  };
  let operation = operations[0], generation = 0, controller = null, observation = null;
  const input = () => document.querySelector('input[name="input"]:checked').value;
  const prediction = () => document.querySelector('input[name="prediction"]:checked')?.value || "";
  const rejected = op => op.endsWith("-rejected");

  function invalidate(message, clearPrediction) {
    generation += 1;
    controller?.abort(); controller = null; observation = null;
    if (clearPrediction) document.querySelectorAll('input[name="prediction"]').forEach(r => {r.checked = false;});
    el("result").hidden = true; el("answer").hidden = true; el("load-error").hidden = true;
    el("load-error").textContent = ""; el("raw-details").open = false;
    ["provenance", "compile-result", "artifact-result", "runtime-result", "runtime-detail", "output", "raw", "verdict", "explanation"].forEach(id => {el(id).textContent = "";});
    el("comparison").replaceChildren();
    el("load").disabled = !prediction(); el("answer-button").disabled = true;
    el("status").textContent = message;
  }
  function showCase() {
    document.querySelectorAll("[data-case]").forEach(b => b.setAttribute("aria-pressed", String(b.dataset.case === operation)));
    el("input-fieldset").disabled = rejected(operation);
    el("case-note").textContent = rejected(operation)
      ? "この2条件はcompile拒否を比べます。Ada / nullを渡すruntimeはありません。"
      : "同じコードへAda / nullを与えた、保存済みの2条件を比べます。";
    el("snippet").textContent = snippets[operation];
    ["flow-one", "flow-two", "flow-three"].forEach((id, i) => {el(id).textContent = flows[operation][i];});
  }
  document.querySelectorAll("[data-case]").forEach(button => button.addEventListener("click", () => {
    operation = button.dataset.case; showCase(); invalidate("条件が変わりました。予想を選んでください。", true);
  }));
  document.querySelectorAll('input[name="input"]').forEach(radio => radio.addEventListener("change", () => invalidate("入力が変わりました。予想を選んでください。", true)));
  document.querySelectorAll('input[name="prediction"]').forEach(radio => radio.addEventListener("change", () => invalidate("予想を保存しました。選んだ条件の原票を読めます。", false)));
  el("reset").addEventListener("click", () => {
    operation = operations[0]; document.querySelector('input[name="input"][value="ada"]').checked = true;
    showCase(); invalidate("初期状態へ戻しました。予想を選んでください。", true);
  });
  async function verifiedJSON(url, digest, signal) {
    const response = await fetch(url, {signal, cache:"no-store", credentials:"same-origin"});
    if (!response.ok) throw new Error("HTTP " + response.status + "：資料を取得できません。");
    const bytes = await response.arrayBuffer();
    const actual = [...new Uint8Array(await crypto.subtle.digest("SHA-256", bytes))].map(n => n.toString(16).padStart(2,"0")).join("");
    if (actual !== digest) throw new Error("保存原票のSHA-256が固定記録と一致しません。");
    return JSON.parse(new TextDecoder().decode(bytes));
  }
  const compileFor = (report, op) => report.compiles.find(row => row.id === (rejected(op) ? op : "snapshot-and-contrast"));
  const runtimeFor = (report, op, value) => rejected(op) ? null : report.runs.find(row => row.mode === op && row.input === value);
  const kindFor = (compile, run) => compile.exit_code !== 0 ? "compile-rejection" : run.exit_code === 0 ? "runtime-normal" : "runtime-npe";
  const kindLabel = kind => ({"compile-rejection":"compile拒否・runtimeなし", "runtime-normal":"正常終了", "runtime-npe":"意図したruntime NPE"})[kind];

  function explain(op, value) {
    if (rejected(op)) return "null検査後にpropertyを再読取りする箇所でSMARTCAST_IMPOSSIBLEが記録されました。JARは生成されず、runtimeには進んでいません。独自getterのval propertyと安定したローカルvalも区別してください。";
    if (op === "mutable-snapshot") return value === "ada"
      ? "元propertyはnullへ変わりましたが、先に保存したsnapshotはAdaです。その同じ値のnull検査後に長さ3を得ました。最新のpropertyを読み直した結果ではありません。"
      : "元propertyをAdaへ変えても、先に保存したsnapshotはnullです。null分岐でlengthの利用を省略しました。";
    if (op === "getter-snapshot") return value === "ada"
      ? "最初のgetter読取りをsnapshotへ保存し、長さ3を利用しました。GET#2は利用後の比較用読取りです。判断と利用のためにgetterを2回読む経路ではありません。"
      : "最初のgetter読取りはnullなので利用を省略しました。比較用の2回目もnullですが、最初の保存値による判断は変わりません。";
    return value === "ada"
      ? "guardの1回目はAda、2回目はnullでした。2回目の値に対する!!でNPEが起きました。これはsmart castの成立ではなく、compile受理後に別の操作で失敗した記録です。"
      : "最初のgetter読取りがnullなのでguard内へ進まず、2回目の読取りも!!も行っていません。";
  }
  function render(report, expected, op, value) {
    const compile = compileFor(report, op), run = runtimeFor(report, op, value);
    if (!compile || (!rejected(op) && !run)) throw new Error("選択条件の保存記録がありません。");
    const fixedCompile = expected.compiles.find(row => row.id === compile.id);
    const fixedRun = run && expected.runs.find(row => row.mode === op && row.input === value);
    if (!fixedCompile || fixedCompile.exit_code !== compile.exit_code || fixedCompile.artifact_created !== compile.artifact_created ||
        (fixedCompile.diagnostic && !compile.stderr.includes("[" + fixedCompile.diagnostic + "]")) ||
        (run && (!fixedRun || fixedRun.exit_code !== run.exit_code || fixedRun.stdout !== run.stdout ||
          (fixedRun.stderr_contains === null ? run.stderr !== "" : !run.stderr.includes(fixedRun.stderr_contains))))) {
      throw new Error("選択条件の記録が固定期待値と一致しません。");
    }
    const kind = kindFor(compile, run);
    el("compile-result").textContent = compile.exit_code === 0 ? "受理 / exit 0" : "SMARTCAST_IMPOSSIBLE / exit 1";
    el("compile-result").className = "outcome " + (compile.exit_code === 0 ? "normal" : "failure");
    el("artifact-result").textContent = compile.artifact_created ? "JAR生成あり" : "JAR生成なし";
    el("runtime-result").textContent = run ? kindLabel(kind) : "実行していない";
    el("runtime-result").className = "outcome " + (kind === "runtime-npe" ? "failure" : "");
    el("runtime-detail").textContent = run ? "保存されたexit = " + run.exit_code : "compileで拒否されたため、入力を渡した実行はありません。";
    const raw = run || compile;
    el("output").textContent = (run ? "JVM" : "compiler") + " stdout:\n" + (raw.stdout || "（空）\n") + "\nstderr:\n" + (raw.stderr || "（空）");
    el("raw").textContent = JSON.stringify({compile, runtime:run}, null, 2);
    el("provenance").textContent = new Date(report.started_at).toLocaleString("ja-JP", {timeZone:"Asia/Tokyo",hour12:false}) +
      " JSTに実行 / Kotlin 2.4.10・JDK 17.0.17 / run.json SHA-256 " + reportDigest.slice(0,16) + "… を照合済み";
    el("comparison").replaceChildren();
    for (const other of operations) {
      const otherCompile = compileFor(report, other), otherRun = runtimeFor(report, other, value);
      const row = document.createElement("tr");
      for (const text of [labels[other] + (rejected(other) ? "" : " / " + (value === "ada" ? "Ada" : "null")), kindLabel(kindFor(otherCompile,otherRun))]) {
        const cell = document.createElement("td"); cell.textContent = text; row.appendChild(cell);
      }
      el("comparison").appendChild(row);
    }
    observation = {op, value, kind};
    el("result").hidden = false; el("answer-button").disabled = false;
    el("status").textContent = "保存原票の取得・照合が完了しました。原典と実装を読んでから予想と照合できます。新規実行はしていません。";
  }
  el("load").addEventListener("click", async () => {
    if (!prediction()) return;
    invalidate("保存原票を取得・照合しています。KotlinやJVMは起動しません。", false);
    const token = generation, op = operation, value = input();
    controller = new AbortController(); const signal = controller.signal;
    el("load").disabled = true;
    try {
      const [report, expected] = await Promise.all([verifiedJSON(reportPath,reportDigest,signal), verifiedJSON("expected.json",expectedDigest,signal)]);
      if (token !== generation) return;
      if (report.schema !== "atlas.kotlin-smart-cast-boundaries.observation.v1" || !report.collection_complete ||
          report.errors.length || report.compiles.length !== 3 || report.runs.length !== 6 || !report.source_unchanged) throw new Error("原票の実観測形式を確認できません。");
      render(report,expected,op,value);
    } catch(error) {
      if (token !== generation) return;
      invalidate("保存原票を表示できませんでした。取得を再試行できます。", false);
      el("load-error").textContent = "資料の取得・照合失敗です。compile拒否やruntime NPEの観測ではありません。 " +
        (location.protocol === "file:" ? "READMEの手順で127.0.0.1のHTTPサーバーから開いてください。" : error.message);
      el("load-error").hidden = false;
    } finally {
      if (token === generation) {controller = null; el("load").disabled = !prediction();}
    }
  });
  el("answer-button").addEventListener("click", () => {
    if (!observation || !prediction()) return;
    el("verdict").textContent = prediction() === observation.kind ? "予想と保存観測は一致しました。" : "予想と保存観測は異なりました。起きた段階を見直しましょう。";
    el("explanation").textContent = explain(observation.op,observation.value);
    el("answer").hidden = false;
  });
  showCase(); invalidate("予想を選んでください。",true);
})();

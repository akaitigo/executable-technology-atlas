"use strict";
(() => {
  const reportPath = "observations/20261006T062456931814Z/run.json";
  const reportDigest = "2d7b5ed2d0cec714ce6b31d50bbb1428c903f50508b853d278ee257a2df76f75";
  const expectedDigest = "5ed67aa248ee88706be0179738b921921c0507deb2ddabe8d9944dc78378ed1b";
  const el = id => document.getElementById(id);
  const operations = ["local-control", "captured-snapshot", "captured-write-rejected"];
  const labels = {"local-control":"変更のないlocal var", "captured-snapshot":"書換前のval snapshot", "captured-write-rejected":"書換後のlocalを直接利用"};
  const snippets = {
    "local-control":"var local: String? = initial\nif (local != null) {\n    println(local.length)\n}",
    "captured-snapshot":"val snapshot: String? = local\nmutate() // 捕捉したlocalを書き換える\nif (snapshot != null) {\n    println(snapshot.length)\n}",
    "captured-write-rejected":"var local: String? = initial\nval mutate: () -> Unit = {\n    local = if (local == null) \"Ada\" else null\n}\nif (local != null) {\n    mutate()\n    return local.length\n}"
  };
  const flows = {
    "local-control":["1. localをnull検査","2. 検査から利用まで変更なし","3. 同じlocalから長さを得る"],
    "captured-snapshot":["1. 書換前にlocal valへ受け取る","2. 捕捉したlocalをラムダで書換","3. 保存値を検査・利用"],
    "captured-write-rejected":["1. localをnull検査","2. 捕捉したlocalをラムダで書換","3. local.lengthをcompileで確認"]
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
      ? "この条件はcompile拒否を比べます。Ada / nullを渡すruntimeはありません。"
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
  const compileFor = (report, op) => report.compiles.find(row => row.id === (rejected(op) ? op : "local-control-and-snapshot"));
  const runtimeFor = (report, op, value) => rejected(op) ? null : report.runs.find(row => row.mode === op && row.input === value);
  const kindFor = (compile, run) => compile.exit_code !== 0 ? "compile-rejection" : run.exit_code === 0 ? "runtime-normal" : "runtime-npe";
  const kindLabel = kind => ({"compile-rejection":"compile拒否・runtimeなし", "runtime-normal":"正常終了", "runtime-npe":"意図したruntime NPE"})[kind];

  function explain(op, value) {
    if (op === "captured-write-rejected") return "書換ラムダに捕捉されたlocalを直接利用する箇所で、SMARTCAST_IMPOSSIBLEが記録されました。JARは生成されず、runtimeには進んでいません。これはNPEの実行記録ではありません。";
    if (op === "local-control") return value === "ada"
      ? "local varは検査から利用まで書き換えられず、今回のコードではsmart castが成立しました。Adaの長さ3を得ています。varという宣言だけで一律に拒否されるわけではありません。"
      : "localはnullなので、lengthを呼ぶ分岐へ進まず利用を省略しました。exit 0の正常な分岐で、NPEではありません。";
    return value === "ada"
      ? "Adaをsnapshotへ保存してから、ラムダがlocalをnullへ変えました。保存値はAdaのままなので、その同じ値を検査して長さ3を得ました。最新のlocalを使った結果ではありません。"
      : "nullをsnapshotへ保存してから、ラムダがlocalをAdaへ変えました。保存値はnullのままなので、lengthの利用を省略しました。以前の値と呼出し後の値を区別してください。";
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
      const values = otherRun ? otherRun.stdout.split("\n").filter(line => /^(RESULT|CONTROL_FINAL|SNAPSHOT|CAPTURED_NOW)=/.test(line)).join(" ／ ") : "";
      for (const text of [labels[other] + (rejected(other) ? "" : " / " + (value === "ada" ? "Ada" : "null")), kindLabel(kindFor(otherCompile,otherRun)) + (values ? " ／ " + values : "")]) {
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
      if (report.schema !== "atlas.kotlin-captured-local-var.observation.v1" || !report.collection_complete ||
          report.errors.length || report.compiles.length !== 2 || report.runs.length !== 4 || !report.source_unchanged) throw new Error("原票の実観測形式を確認できません。");
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

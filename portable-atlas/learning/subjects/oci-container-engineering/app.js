"use strict";
const data = window.OCI_OBSERVATION;
const observation = data.observation;
const $ = (s) => document.querySelector(s);
const cases = {
  normal: ["正常 / OVERWRITE & WHITEOUT", "同名fileは更新。古いfileは消える。", "下位のmessageをversion twoへ上書き。obsoleteを明示whiteoutで削除し、newを追加します。", "上位layerでapp/message.txtはversion twoへ更新。app/obsolete.txtは削除され、.wh.obsolete.txt自体もmapに残りません。etc/stable.txtは変わらず、newが追加されました。"],
  "same-layer": ["境界 / LOWER ONLY", "先に追加したfileも、削除印で消える？", "上位tarでobsoleteのfileを先に置き、その後に同じ対象のwhiteoutを置きます。whiteoutの対象は下位だけです。", "whiteoutは下位のobsoleteを削除しますが、同じ上位layerにあるobsoleteは保持されました。単純なtar順の削除処理ではなく、下位削除と同層追加を分けます。"],
  "absent-whiteout": ["境界 / ABSENT TARGET", "削除対象が、下位にない。", "app/missing.txtを消すwhiteout。下位mapにはそのpathが存在しません。", "対象がない明示whiteoutはこのsubsetでno-op。下位mapは変わらず、削除印も現れません。"],
  traversal: ["拒否 / PATH", "../ は仮想rootの外を指す。", "上位tar member名は../escape.txt。digestが合っていても、canonical relative pathではありません。", "descriptor照合は通りますが、member path検査でnoncanonical-pathとして拒否。上位layer全体を適用せず、ホストには展開しません。"],
  absolute: ["拒否 / PATH", "/から始まるpathを渡す。", "上位tar member名は/escape.txt。ホストの絶対pathとして扱うことを防ぎます。", "absolute-pathで拒否。仮想mapのkeyはrootからの相対pathだけで、ホストの/へ書き込む操作は存在しません。"],
  symlink: ["未対応 / ENTRY TYPE", "リンクは、普通のfileではない。", "app/linkは../../escapeへのsymlink。OCIにはlinkが存在しますが、このfile-only subsetでは未対応です。", "unsupported-entry-typeとして拒否。リンクを追跡せず、解決先を読み書きしません。これは全OCIでsymlinkが禁止という意味ではありません。"],
  opaque: ["未対応 / VALID OCI FEATURE", "directoryの中身を隠す、別の印。", ".wh..wh..opqはopaque whiteout。OCIで有効ですが、今回の明示whiteout subsetには含めません。", "unsupported-opaque-whiteoutとして拒否。有効なOCI機能の未対応境界を隠さず表示します。opaqueの本来の挙動は公式資料に戻って確認してください。"],
  duplicate: ["拒否 / DUPLICATE", "同じpathが、1つのtarに2回。", "app/sameをone、twoの順で重複登録したtarを実生成します。", "duplicate-pathとして拒否。OCI layerの同一path重複制約に従い、このtarをlast-winsとして黙って適用しません。"],
  "metadata-tamper": ["拒否 / METADATA HASH", "manifestを変え、参照digestはそのまま。", "manifest blobへannotationを追記。indexが保持するdescriptorと実metadata bytesが合わなくなります。", "最初のmanifest descriptor照合でdescriptor-mismatch。configやtarを適用する前に停止しました。digest照合は内容の整合であり、署名や作成者の証明ではありません。"],
  "blob-tamper": ["拒否 / LAYER HASH", "tarのfile内容だけを、同じ長さで変える。", "上位tarのversion twoをversion BADへ差替え。descriptorのdigestとsizeは元のままです。", "上位blobのdigest照合でdescriptor-mismatch。長さが同じでもSHA-256は変化し、仮想map適用前に停止しました。"],
  "diffid-mismatch": ["拒否 / CONFIG BINDING", "object hashは合う。DiffIDだけ違う。", "configの2個目diff_idsをzero digestにし、config/manifest/indexの参照は全て再生成します。", "各object descriptorは一致しますが、configのDiffIDと実非圧縮tar digestが合わずdiff-id-mismatch。自己整合したmetadata chainだけでlayer内容との意味的bindingを省略できません。"]
};
let current = "normal", step = 0, prediction = null;
const row = () => observation.scenarios.find(r => r.id === current);
const short = d => d.slice(0, 23) + "…";
function node(tag, text, className) { const n = document.createElement(tag); n.textContent = text; if (className) n.className = className; return n; }
function renderEntries(target, entries) {
  target.replaceChildren();
  for (const item of entries) {
    const box = node("div", "", "entry" + (item.path.includes(".wh.") ? " whiteout" : ""));
    box.append(node("code", item.path), node("span", item.type || "regular file"));
    box.append(node("div", item.type === "symlink" ? "→ " + item.target : (item.text === "" ? "empty bytes" : item.text), "content"));
    target.append(box);
  }
}
function renderMap(target, map, title) {
  target.replaceChildren(node("p", title, "map-title"));
  for (const [path, value] of Object.entries(map)) {
    const box = node("div", "", "file");
    box.append(node("code", path), node("div", value.text, "content"), node("small", `${value.size} bytes / ${short(value.digest)}`));
    target.append(box);
  }
}
function render() {
  const r = row(), info = cases[current];
  $("#case-type").textContent = info[0]; $("#case-title").textContent = info[1]; $("#case-description").textContent = info[2];
  document.querySelectorAll("[data-case]").forEach(b => { b.classList.toggle("selected", b.dataset.case === current); b.setAttribute("aria-pressed", String(b.dataset.case === current)); });
  document.querySelectorAll("[data-predict]").forEach(b => { const selected = prediction !== null && (b.dataset.predict === "true") === prediction; b.classList.toggle("selected", selected); b.setAttribute("aria-pressed", String(selected)); });
  $("#steps").replaceChildren(...["1 object", "2 tar入力", "3 map", "4 答え"].map((s, i) => node("span", s, i < step ? "active" : "")));
  $("#next").disabled = prediction === null || step === 4; $("#finish").disabled = prediction === null || step === 4;
  $("#next").textContent = ["Objectを照合 →", "tar入力を見る →", "仮想mapへ適用 →", "答えを見る →", "再生完了"][step];
  $("#prediction-text").textContent = step === 4 ? (prediction === r.result.accepted ? "予想と実結果は一致。何を検査したか、原票と比較しましょう。" : "予想とは違いました。通った段階と拒否された段階を分けて確認しましょう。") : "予想を選んでから、実結果を1段ずつ確認します。";
  $("#replay-note").textContent = `${observation.execution_id} / ${r.observed_at} の保存済み実結果。操作は再生のみで、tar生成やcontainer起動を行いません。`;
  const descTrace = r.result.trace.filter(t => t.phase === "descriptor");
  $("#index-digest").textContent = step ? "oci-layout 1.0.0\nindex schemaVersion 2" : "操作後に表示";
  $("#manifest-digest").textContent = step ? (descTrace[0] ? short(descTrace[0].actual.digest) : "descriptor mismatch / 読取停止") : "操作後に表示";
  $("#layer-digests").textContent = step ? (descTrace.slice(2).map(t => short(t.actual.digest)).join("\n") || "まだ参照を検証できません") : "操作後に表示";
  $("#integrity-state").textContent = step ? (r.result.integrity ? "Object: digest / DiffID一致" : "Object: 拒否") : "Object: 未検査";
  $("#integrity-state").className = step ? (r.result.integrity ? "passed" : "refused") : "";
  $("#apply-state").textContent = step >= 3 ? (r.result.accepted ? "Layer: subset適用" : "Layer: 拒否 / final mapなし") : "Layer: 未適用";
  $("#apply-state").className = step >= 3 ? (r.result.accepted ? "passed" : "refused") : "";
  if (step >= 2) { renderEntries($("#lower-entries"), r.input[0]); renderEntries($("#upper-entries"), r.input[1]); }
  else { $("#lower-entries").replaceChildren(node("p", "tar入力を見る操作で表示します。", "small")); $("#upper-entries").replaceChildren(); }
  $("#lower-map").replaceChildren(); $("#events").replaceChildren();
  if (step >= 3 && r.result.snapshots.length) renderMap($("#lower-map"), r.result.snapshots[0], "実読取: layer 1後のmap");
  if (step >= 3) {
    if (r.result.accepted) {
      renderMap($("#final-map"), r.result.final_map, "実読取: layer 2後のmap");
      const events = r.result.trace.find(t => t.phase === "virtual-apply" && t.layer === 2).events;
      for (const e of events) $("#events").append(node("div", `${e.action}: ${e.path}${e.target ? " → " + e.target + " / lower removed=" + e.removed.length : ""}`, "event"));
    } else {
      const box = node("div", "", "refusal"); box.append(node("strong", "適用拒否"), node("code", r.result.error), node("p", "final mapを返しません。partial snapshotは原票に保持し、成功mapへ流用しません。"));
      $("#final-map").replaceChildren(box);
    }
  } else $("#final-map").replaceChildren(node("p", "まだ適用していません。"));
  $("#trace").textContent = step ? JSON.stringify({accepted:r.result.accepted, integrity:r.result.integrity, error:r.result.error, trace:r.result.trace, mutations:r.mutations}, null, 2) : "Object照合を進めると原票を表示します。";
  const root = `${data.directory}/${current}/`;
  $("#raw-links").replaceChildren();
  const raw = ["input.json", "result.json", "layout/oci-layout", "layout/index.json", "layout/blobs/sha256/"];
  for (const m of r.mutations) raw.push(m.file);
  for (const t of descTrace) raw.push("layout/blobs/sha256/" + t.expected.digest.slice(7));
  for (const path of [...new Set(raw)]) { const link = node("a", path.length > 50 ? "blob / " + path.slice(-16) : path); link.href = root + path; $("#raw-links").append(link); }
  $("#answer-title").textContent = step === 4 ? info[1] : "最後に、予想と比べる。";
  $("#answer-text").textContent = step === 4 ? info[3] : "digest照合、tar memberの検査、仮想mapへの適用を区別して進めます。";
}
for (const [id, info] of Object.entries(cases)) {
  const labels = {normal:"正常2層", "same-layer":"同層file＋削除印", "absent-whiteout":"対象なしwhiteout", traversal:"../path", absolute:"絶対path", symlink:"symlink", opaque:"opaque", duplicate:"重複path", "metadata-tamper":"metadata改ざん", "blob-tamper":"tar改ざん", "diffid-mismatch":"DiffID不一致"};
  const b = node("button", labels[id]); b.dataset.case = id; b.setAttribute("aria-pressed", "false"); b.addEventListener("click", () => { current = id; step = 0; prediction = null; render(); }); $("#scenarios").append(b);
}
document.querySelectorAll("[data-predict]").forEach(b => b.addEventListener("click", () => { prediction = b.dataset.predict === "true"; render(); }));
$("#next").addEventListener("click", () => { step = Math.min(4, step + 1); render(); });
$("#finish").addEventListener("click", () => { step = 4; render(); });
$("#reset").addEventListener("click", () => { step = 0; prediction = null; render(); });
const records = {"Field ID":observation.field_id,"実行ID":observation.execution_id,"UTC観測":`${observation.started_at} — ${observation.completed_at}`,"実行host":`${observation.runtime.os} ${observation.runtime.release} / ${observation.runtime.machine} / CPython ${observation.runtime.python}`,"合成image": "linux / amd64 / programなし", "入力":"下位3file＋上位changeset / 11条件", "試行/上限": "attempt 1 / retry 0 / outer 20秒", "比較": "同入力再生成の全layout bytes一致", "Source bindings":Object.entries(observation.source_bindings).map(([f,d]) => f + " " + d).join(" / "), "実command exit":"原票を読取中", "範囲": "object / tar読取＋仮想map / container未起動 / 全Subject未完成"};
for (const [key,value] of Object.entries(records)) $("#metadata").append(node("dt", key),node("dd", value));
for (const name of ["observation.json","command.json","artifact-index.json"]) {const a = node("a", name); a.href = data.directory + "/" + name; $("#record-links").append(a);}
fetch(data.directory + "/command.json").then(r=>{if(!r.ok)throw Error("command record unavailable");return r.json();}).then(command=>{ $("#command").textContent=JSON.stringify(command,null,2); const terms=[...$("#metadata").querySelectorAll("dt")]; terms.find(t=>t.textContent==="実command exit").nextElementSibling.textContent=String(command.exit_code); }).catch(e=>{$("#command").textContent=e.message;});
render();

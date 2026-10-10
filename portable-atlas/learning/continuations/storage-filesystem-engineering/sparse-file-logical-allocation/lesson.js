"use strict";
(() => {
  const r = window.SPARSE_OBSERVATION;
  const el = id => document.getElementById(id);
  const names = {seek_only:"seekだけ", sparse_written:"末尾にXを1バイト", dense_written:"先頭から全て書く"};
  const format = n => n === null ? "未提供" : n.toLocaleString("ja-JP") + " バイト";
  let valid = false;
  const shapeValid = r?.schema === "atlas.sparse-file.observation.v1" && r?.contents_equal === true &&
    r?.durability_proven === false && r?.performance_comparison === false && r?.toolchain &&
    Object.keys(names).every(name => r[name]?.stat && Number.isInteger(r[name].stat.logical_bytes));
  let selectedObservation = null;
  function clear(message, clearPrediction) {
    selectedObservation = null;
    el("answer").hidden = true; el("interpretation").hidden = true;
    ["logical","offset","allocation","explanation","read-summary","raw","prediction-copy","lesson-answer"].forEach(id => {el(id).textContent = "";});
    el("track").replaceChildren(); el("comparison").replaceChildren(); el("raw-details").open = false;
    if (clearPrediction) el("prediction").value = "";
    el("reveal").disabled = !valid || !el("prediction").value.trim();
    el("explain-button").disabled = true; el("status").textContent = message;
  }
  function prompt() {
    el("prompt").textContent = el("stage").value === "seek_only"
      ? "まだ書いていないファイルの長さと、先頭の読取り結果を予想してください。"
      : "書込み後の論理長・先頭の内容・割当量を予想してください。";
    const index = Object.keys(names).indexOf(el("stage").value);
    el("previous-stage").disabled = index <= 0;
    el("next-stage").disabled = index >= Object.keys(names).length - 1;
  }
  function conditionChanged() {prompt(); clear("条件が変わりました。新しい予想を書いてください。", true);}
  el("stage").addEventListener("change", conditionChanged);
  function moveCondition(delta) {
    const stages = Object.keys(names), current = stages.indexOf(el("stage").value), next = current + delta;
    if (next < 0 || next >= stages.length) return;
    el("stage").value = stages[next]; conditionChanged();
  }
  el("previous-stage").addEventListener("click", () => moveCondition(-1));
  el("next-stage").addEventListener("click", () => moveCondition(1));
  el("prediction").addEventListener("input", () => clear("予想が変わりました。古い結果と答えを消しました。", false));
  el("reset").addEventListener("click", () => {el("stage").value = "seek_only"; prompt(); clear("最初の状態へ戻しました。予想を書いてください。", true);});
  function unavailable(detail) {
    el("environment").textContent = "保存観測を読み込めませんでした。";
    el("data-error").textContent = "資料の読込み・照合に失敗しました。OS実験の失敗ではありません。" + detail + " READMEと保存した測定結果を確認し、ページを再読込みしてください。";
    el("data-error").hidden = false; clear("保存資料を確認してください。", true);
  }
  if (!shapeValid) {unavailable("保存データの形式を確認できません。"); return;}
  const localTime = new Date(r.started_at).toLocaleString("ja-JP", {timeZone:"Asia/Tokyo", hour12:false});
  const environment = localTime + " JST ／ " + r.toolchain.os + " " + r.toolchain.release + " (" + r.toolchain.machine + ") ／ Python " + r.toolchain.python + " ／ 実験1回";
  el("environment").textContent = "表示データのSHA-256を照合中です。";
  function comparison() { for (const name of Object.keys(names)) {
    const row = document.createElement("tr");
    const data = r[name];
    for (const text of [names[name], format(data.stat.logical_bytes), name === "seek_only" ? "空の結果" : "ゼロ65,535個 + X", format(data.stat.reported_allocated_bytes)]) {
      const cell = document.createElement("td");
      cell.textContent = text;
      row.appendChild(cell);
    }
    el("comparison").appendChild(row);
  } }
  el("reveal").addEventListener("click", () => {
    if (!valid || !el("prediction").value.trim()) return;
    clear("保存観測を表示します。", false);
    const name = el("stage").value, data = r[name], empty = name === "seek_only";
    el("logical").textContent = format(data.stat.logical_bytes);
    el("offset").textContent = format(empty ? data.offset : data.offset_after_write);
    el("allocation").textContent = format(data.stat.reported_allocated_bytes);
    el("track").replaceChildren();
    const body = document.createElement("div");
    body.className = empty ? "empty" : "zeros";
    body.textContent = empty ? "読める範囲はまだない → EOF" : "位置0〜65,534：ゼロ65,535個";
    el("track").appendChild(body);
    if (!empty) {
      const tail = document.createElement("div");
      tail.className = "last";
      tail.textContent = "X";
      el("track").appendChild(tail);
    }
    el("explanation").textContent = empty
      ? "位置は65,535へ移りましたが、長さは0です。先頭も移動先も読取り結果は空でした。書込みを省略すると、意図した内容はまだ作られていません。"
      : name === "sparse_written"
        ? "書いたのは末尾のXだけです。間の未書込み範囲はゼロとして読め、全体の長さは65,536になりました。"
        : "先頭から全てのバイトを書いた対照です。疎な書込みと、全65,536バイトの読取り内容が一致しました。";
    el("read-summary").textContent = empty
      ? "先頭の読取り：b'' ／ 位置65,535の読取り：b''（どちらも空）"
      : "先頭16バイトの16進表記：" + data.read_first_16_hex + " ／ 末尾2バイト：" + data.read_tail_2_hex + " ／ 位置65,536：b''（EOF）";
    el("raw").textContent = JSON.stringify(data, null, 2);
    comparison(); selectedObservation = name;
    el("answer").hidden = false;
    el("explain-button").disabled = false;
    el("status").textContent = names[name] + "の保存観測を表示しました。原典・実装を読んでから答えを確認できます。新しいOS実験はしていません。";
  });
  el("explain-button").addEventListener("click", () => {
    if (!selectedObservation) return;
    el("prediction-copy").textContent = el("prediction").value;
    el("lesson-answer").textContent = selectedObservation === "seek_only"
      ? "seekは位置を変え、まだ長さを増やしませんでした。長さ0のため、先頭も移動先もEOFで空です。ゼロ1バイトを読んだ結果ではありません。"
      : selectedObservation === "sparse_written"
        ? "位置65,535への1バイト書込みで論理長は65,536になり、間はゼロとして読めました。OS報告の割当量は論理長と別の量です。"
        : "全バイトを先頭から書いても、読み出す内容は疎な書込みと一致しました。今回の割当量の差から、物理配置・性能・耐久性まで判断することはできません。";
    el("interpretation").hidden = false;
  });
  clear("表示データの照合を待っています。OS実験は行いません。", true);
  Promise.resolve().then(async () => {
    // This is the digest of JSON.stringify(parsed run.json), not the original file-byte digest.
    const bytes = new TextEncoder().encode(JSON.stringify(r));
    const hash = [...new Uint8Array(await crypto.subtle.digest("SHA-256", bytes))].map(n => n.toString(16).padStart(2,"0")).join("");
    if (hash !== "320d8ee0610b7ff70f3738843dbef780c8668b8cf3cfde178b064d5dac6a9880") throw new Error("表示データのSHA-256が保存観測に対応しません。");
    valid = true; el("environment").textContent = environment + " ／ 表示データdigest照合済み";
    clear("予想を書いてから、保存観測を開いてください。", false);
  }).catch(error => unavailable(error.message || "SHA-256を利用できません。"));
})();

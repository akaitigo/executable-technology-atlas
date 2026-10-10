/* 保存済み実recv結果の再生。ブラウザからsocketは開かない。 */
(() => {
  "use strict";
  const data = window.TCP_OBSERVATION;
  const $ = (id) => document.getElementById(id);
  if (!data || data.observation.status !== "pass") {
    $("runtime-status").textContent = "実観測なし / 操作は停止";
    return;
  }
  const observation = data.observation;
  const bytes = observation.input.stream_hex.match(/../g);
  let cap = 3, step = 0, prediction = null;
  const activeRun = () => observation.runs.find((run) => run.receive_cap === cap);
  const node = (tag, className, content) => {
    const el = document.createElement(tag);
    if (className) el.className = className;
    if (content !== undefined) el.textContent = content;
    return el;
  };
  function byteRow(id, count, start) {
    const cells = bytes.map((hex, index) => {
      const header = [0, 1, 6, 7].includes(index);
      const label = header ? hex : String.fromCharCode(parseInt(hex, 16));
      const el = node("span", "byte" + (header ? " header" : "") +
        (id === "stream-bytes" && index >= count ? " unread" : "") +
        (id === "stream-bytes" && index >= start && index < count ? " active" : ""), label);
      el.append(node("small", "", String(index).padStart(2, "0")));
      el.title = `offset ${index} / hex ${hex}`;
      return el;
    });
    if (id === "input-bytes") {
      $(id).replaceChildren(...[{start:0,end:6,label:"sendall #1 · 6 bytes",format:"00 04 + PING"},
        {start:6,end:13,label:"sendall #2 · 7 bytes",format:"00 05 + HELLO"}].map((frame) => {
        const group = node("div", "input-frame");
        group.append(node("div", "frame-label", frame.label));
        const row = node("div", "bytes"); row.append(...cells.slice(frame.start, frame.end));
        group.append(row, node("div", "frame-format", frame.format));
        return group;
      }));
    } else $(id).replaceChildren(...cells);
  }
  function messages(id, values) {
    $(id).replaceChildren(...(values.length ? values.map((value) => node("span", "message", value)) : [node("span", "", "まだなし")]));
  }
  function render() {
    const run = activeRun(), visible = run.chunks.slice(0, step), done = step > run.chunks.length;
    const received = visible.reduce((sum, chunk) => sum + chunk.returned, 0);
    const last = visible[visible.length - 1];
    const emitted = visible.flatMap((chunk) => chunk.emitted);
    const accepted = visible.filter((chunk) => chunk.naive.status === "accepted").map((chunk) => chunk.naive.payload);
    byteRow("input-bytes", bytes.length, bytes.length);
    byteRow("stream-bytes", received, received - (last ? last.returned : 0));
    $("progress").textContent = `${received} / ${bytes.length} bytes${done ? " · EOF" : ""}`;
    let offset = 0;
    $("receive-slices").replaceChildren(...visible.map((chunk) => {
      const slice = node("span", "slice", `recv #${chunk.call} · ${chunk.returned} B · offset ${offset}–${offset + chunk.returned - 1}`);
      offset += chunk.returned; return slice;
    }));
    $("sequence-recv").textContent = visible.length ? visible.map((chunk) => chunk.returned).join(" + ") + " bytes" + (done ? " → EOF" : "") : "まだ読んでいない";
    messages("good-messages", emitted);
    messages("bad-messages", accepted);
    $("buffer-value").textContent = last && last.buffer_hex ? last.buffer_hex.match(/../g).join(" ") : "0 bytes";
    const reasonNames = {"header incomplete": "長さ2 bytesが揃わない", "invalid length prefix": "長さとして読めない", "recv boundary is not a frame boundary": "recv境界とframe境界が不一致"};
    $("bad-reason").textContent = last ? (reasonNames[last.naive.reason] || "1 frameとして受理") : "未実行";
    $("good-state").textContent = done ? "2件を復元" : emitted.length ? `${emitted.length}件を復元` : step ? "蓄積中" : "待機";
    $("bad-state").textContent = done ? (run.oracle.naive_matches ? "今回一致" : "復元失敗") : visible.some((chunk) => chunk.naive.status === "refused") ? "境界で拒否" : "待機";
    $("next").disabled = !prediction || done;
    $("finish").disabled = !prediction || done;
    $("next").textContent = step === run.chunks.length ? "EOFを確認する →" : "recvを1回進める →";
    $("trace-count").textContent = `${visible.length + (done ? 1 : 0)} calls`;
    const trace = visible.map((chunk) => {
      const row = node("div", "trace-row");
      const event = run.events.find((event) => event.operation === "recv" && event.call === chunk.call);
      row.append(node("strong", "", `recv #${chunk.call}`), node("span", "", `${chunk.requested} → ${chunk.returned} B`),
        node("code", "", chunk.hex.match(/../g).join(" ")), node("small", "", event.at.split("T")[1]));
      return row;
    });
    if (done) {
      const row = node("div", "trace-row");
      const eof = run.events.find((event) => event.operation === "recv" && event.returned === 0);
      row.append(node("strong", "", "EOF"), node("span", "", `${cap} → 0 B`), node("code", "", "b''"), node("small", "", eof.at.split("T")[1]));
      trace.push(row);
    }
    $("trace-rows").replaceChildren(...(trace.length ? trace : [node("p", "quiet", "操作すると、要求幅・返却長・hex・時刻がここに並びます。") ]));
    $("run-window").textContent = run.id + " / " + run.started_at;
    $("answer-title").textContent = done ? "メッセージの境界は、アプリが復元する。" : "最後まで進めて、答えを確かめよう。";
    $("answer-text").textContent = done ? `今回のsendallは6 + 7 bytes。recv(${cap})は${run.oracle.recv_lengths.join(" + ")} bytesでした。TCPは順序のある13 bytesを届け、length framingはPINGとHELLOを復元しました。recvごとに1件とする実装は${run.oracle.naive_matches ? "この条件では一致しましたが、その一致は保証されません" : "この同じ受信列を復元できませんでした"}。受信幅やOSの都合が変わっても扱えるよう、未完了bytesを残して解析します。` : "TCPの区切りとアプリの区切り。今回の実観測で何が一致し、何が一致しなかったかを見ます。";
    $("answer-metrics").replaceChildren(...(done ? [node("span", "answer-metric", "送信: 2 calls / 13 B"), node("span", "answer-metric", `受信: ${run.chunks.length} data calls / 13 B`), node("span", "answer-metric", "復元: 2 messages")] : []));
    $("prediction-feedback").textContent = !prediction ? "予想を選ぶと、実観測を1回ずつ進められます。" : done ? (prediction === "variable" ? "今回の観測と一致。もう一方の受信幅も比較してみましょう。" : "2回sendしてもrecv回数は固定されません。今回の生出力で確認できました。") : "予想を記録しました。実観測を進めて、確かめてください。";
  }
  document.querySelectorAll("[data-prediction]").forEach((button) => button.addEventListener("click", () => {
    prediction = button.dataset.prediction;
    document.querySelectorAll("[data-prediction]").forEach((other) => {
      const selected = other === button; other.classList.toggle("selected", selected); other.setAttribute("aria-pressed", String(selected));
    }); render();
  }));
  document.querySelectorAll("[data-cap]").forEach((button) => button.addEventListener("click", () => {
    cap = Number(button.dataset.cap); step = 0;
    document.querySelectorAll("[data-cap]").forEach((other) => {
      const selected = other === button; other.classList.toggle("selected", selected); other.setAttribute("aria-pressed", String(selected));
    }); render();
  }));
  $("next").addEventListener("click", () => { step = Math.min(step + 1, activeRun().chunks.length + 1); render(); });
  $("finish").addEventListener("click", () => { step = activeRun().chunks.length + 1; render(); });
  $("reset").addEventListener("click", () => {
    step = 0; prediction = null;
    document.querySelectorAll("[data-prediction]").forEach((button) => { button.classList.remove("selected"); button.setAttribute("aria-pressed", "false"); }); render();
  });
  $("runtime-status").textContent = "実TCP観測済み / 2条件";
  const env = observation.environment;
  const metadata = {"Catalog ID": observation.subject_id, "実行ID": observation.execution_id,
    "観測時刻UTC": observation.started_at + " — " + observation.completed_at,
    "実行環境": `${env.os} ${env.os_release} / ${env.machine} / ${env.implementation} ${env.python}`,
    "接続": `${env.transport} / 127.0.0.1 / 動的port / 2接続`, "入力": "PING / HELLO · 2-byte length · 13 bytes",
    "上限": "各socket 3秒 / 各接続32 recvまで / outer command 20秒", "試行": "attempt 1 / retry 0",
    "cleanup": "各接続のowned socket 3個をclose / open 0 / sender thread終了",
    "Source確認日": "2026-10-05 / RFC 9293 / Python docs 3.9.25", "公開範囲": "ローカル教材 / Subject completionへの加算なし"};
  $("metadata").replaceChildren(...Object.entries(metadata).flatMap(([key, value]) => [node("dt", "", key), node("dd", "", value)]));
  $("artifact-links").replaceChildren(...["observation.json", "command.json", "manifest.json"].map((name) => {
    const link = node("a", "", name); link.href = data.artifact_directory + "/" + name; return link;
  }));
  $("raw-command").textContent = JSON.stringify(data.record, null, 2) + "\n\n生stdout/stderrはcommand.jsonで参照できます。";
  // Load raw command only from the declared local artifact, no broker/runtime request.
  fetch(data.artifact_directory + "/command.json").then((response) => {
    if (!response.ok) throw new Error("raw command file unavailable");
    return response.json();
  }).then((record) => { $("raw-command").textContent = JSON.stringify(record, null, 2); })
    .catch(() => { $("raw-command").append("\n生出力は上のcommand.jsonリンクから確認してください。file://では直接リンクを使用します。"); });
  render();
})();

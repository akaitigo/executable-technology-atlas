/* このファイルは file:// でも動く。ネットワーク・外部ライブラリは使用しない。 */
"use strict";
const CapacityLesson = (() => {
  const costs = Object.freeze({A: 5, B: 1, C: 1});
  const orders = Object.freeze(["ABC", "ACB", "BAC", "BCA", "CAB", "CBA"]);
  const predictions = ["earlier", "same", "later"];
  function schedule(order) {
    if (!orders.includes(order)) throw new Error("REFUSED_INPUT");
    let clock = 0;
    const jobs = {};
    for (const name of order) {
      const start = clock;
      clock += costs[name];
      jobs[name] = {arrival: 0, service: costs[name], start, finish: clock,
                    wait: start, response: clock};
    }
    const sum = Object.values(jobs).reduce((s, job) => s + job.finish, 0);
    const fraction = n => n % 3 === 0 ? String(n / 3) : `${n}/3`;
    return {order, jobs, sum_completion: sum, mean_completion: fraction(sum),
      mean_wait: fraction(sum - 7), max_completion: clock, makespan: clock,
      throughput: "3/7", time_unit: "model tick", benchmark: false};
  }
  function frame(result, tick) {
    if (!Number.isInteger(tick) || tick < 0 || tick > 7) throw new Error("REFUSED_TICK");
    return Object.fromEntries(Object.entries(result.jobs).map(([name, job]) => [name,
      tick < job.start ? "待ち" : tick < job.finish ? "実行中" : "完了"]));
  }
  function initial() { return {order: "BCA", tick: 0, prediction: "", revealed: false}; }
  function transition(state, action) {
    if (action.type === "order") {
      schedule(action.value);
      return {...state, order: action.value, tick: 0, prediction: "", revealed: false};
    }
    if (action.type === "tick") { frame(schedule(state.order), action.value); return {...state, tick: action.value}; }
    if (action.type === "predict") {
      if (!predictions.includes(action.value)) throw new Error("REFUSED_PREDICTION");
      return {...state, prediction: action.value, revealed: false};
    }
    if (action.type === "reveal") {
      if (!predictions.includes(state.prediction)) throw new Error("PREDICTION_REQUIRED");
      return {...state, revealed: true};
    }
    if (action.type === "reset") return initial();
    throw new Error("REFUSED_ACTION");
  }
  return {schedule, frame, orders, initial, transition};
})();
if (typeof module !== "undefined") module.exports = CapacityLesson;

if (typeof document !== "undefined") {
  (() => {
    const $ = id => document.getElementById(id);
    let state = CapacityLesson.initial();
    const fifo = CapacityLesson.schedule("ABC");
    const labels = {earlier: "早くなる", same: "変わらない", later: "遅くなる"};
    const format = value => value.includes("/") ? `${value} ≈ ${(Number(value.split("/")[0]) / 3).toFixed(2)}` : value;
    const dispatch = action => { state = CapacityLesson.transition(state, action); render(); };
    function timeline(result) {
      const statuses = CapacityLesson.frame(result, state.tick);
      const host = document.createElement("div");
      const track = document.createElement("div");
      track.className = "track";
      track.setAttribute("role", "img");
      track.setAttribute("aria-label", [...result.order].map(name => `${name}: ${result.jobs[name].start}から${result.jobs[name].finish}`).join("、"));
      for (const name of result.order) {
        const job = result.jobs[name];
        const segment = document.createElement("div");
        segment.className = `job job-${name}`;
        segment.style.flex = String(job.service);
        segment.textContent = `${name}（${job.service}）`;
        track.append(segment);
      }
      const cursor = document.createElement("div");
      cursor.className = "cursor";
      cursor.style.left = `${state.tick / 7 * 100}%`;
      cursor.setAttribute("aria-hidden", "true");
      track.append(cursor);
      host.append(track);
      const axis = document.createElement("div");
      axis.className = "axis";
      for (let i = 0; i <= 7; i++) { const span = document.createElement("span"); span.textContent = i; axis.append(span); }
      host.append(axis);
      const live = document.createElement("p");
      live.className = "states";
      live.textContent = `時刻 ${state.tick}：` + ["A", "B", "C"].map(name => `${name} ${statuses[name]}`).join(" ／ ");
      host.append(live);
      return host;
    }
    function render() {
      const chosen = CapacityLesson.schedule(state.order);
      $("order").value = state.order;
      $("previous-order").disabled = state.order === CapacityLesson.orders[0];
      $("next-order").disabled = state.order === CapacityLesson.orders[CapacityLesson.orders.length - 1];
      $("tick").value = state.tick;
      $("tick-value").textContent = state.tick;
      $("next").disabled = state.tick === 7;
      $("compare-title").textContent = `選んだ順序 ${[...state.order].join(" → ")}${state.order === "BCA" ? "（短い順）" : ""}`;
      $("fifo-timeline").replaceChildren(timeline(fifo));
      $("chosen-timeline").replaceChildren(timeline(chosen));
      for (const radio of document.querySelectorAll('input[name="prediction"]')) radio.checked = radio.value === state.prediction;
      $("answer-button").disabled = !state.prediction;
      const rows = [
        ["平均完了時間", format(fifo.mean_completion), format(chosen.mean_completion)],
        ["平均待ち時間", format(fifo.mean_wait), format(chosen.mean_wait)],
        ...["A", "B", "C"].map(name => [`${name} の完了時刻`, fifo.jobs[name].finish, chosen.jobs[name].finish]),
        ["最後の完了時刻", 7, chosen.makespan],
        ["完了数 / 全体の時間", "3/7", chosen.throughput]
      ];
      $("metrics").replaceChildren(...rows.map(values => {
        const row = document.createElement("tr");
        values.forEach((value, i) => { const cell = document.createElement(i === 0 ? "th" : "td"); cell.textContent = value; if (i === 0) cell.scope = "row"; row.append(cell); });
        return row;
      }));
      $("answer").hidden = !state.revealed;
      if (state.revealed) {
        const delta = chosen.jobs.A.finish - fifo.jobs.A.finish;
        const actual = delta > 0 ? "later" : delta < 0 ? "earlier" : "same";
        $("answer").textContent = `予想「${labels[state.prediction]}」は${state.prediction === actual ? "一致" : "不一致"}。A は 5 → ${chosen.jobs.A.finish}、${labels[actual]}。平均完了時間は 6 → ${chosen.mean_completion}。` +
          (delta > 0 ? "平均が小さくても、すべての仕事が早く終わるわけではありません。" : "この順序では A の完了時刻は変わりません。BCA と比べてみてください。") +
          "全体の終了時刻は 7、完了数は 3 のままです。";
      } else $("answer").textContent = "";
      $("raw").textContent = JSON.stringify(chosen, null, 2);
    }
    const chooseOrder = value => dispatch({type: "order", value});
    $("order").addEventListener("change", event => chooseOrder(event.target.value));
    $("previous-order").addEventListener("click", () => {
      const index = CapacityLesson.orders.indexOf(state.order);
      if (index > 0) chooseOrder(CapacityLesson.orders[index - 1]);
    });
    $("next-order").addEventListener("click", () => {
      const index = CapacityLesson.orders.indexOf(state.order);
      if (index < CapacityLesson.orders.length - 1) chooseOrder(CapacityLesson.orders[index + 1]);
    });
    $("tick").addEventListener("input", event => dispatch({type: "tick", value: Number(event.target.value)}));
    $("next").addEventListener("click", () => dispatch({type: "tick", value: Math.min(7, state.tick + 1)}));
    $("reset").addEventListener("click", () => dispatch({type: "reset"}));
    for (const radio of document.querySelectorAll('input[name="prediction"]')) radio.addEventListener("change", event => dispatch({type: "predict", value: event.target.value}));
    $("answer-button").addEventListener("click", () => dispatch({type: "reveal"}));
    render();
  })();
}

// SPDX-License-Identifier: Apache-2.0
(() => {
  const lesson = window.SQL_LESSON;
  if (!lesson) throw new Error("evidence/data.js is missing");
  const raw = lesson.raw;
  const queries = Object.fromEntries(raw.queries.map((item) => [item.id, item]));
  const joinCopy = {
    "join.inner": ["INNER JOIN", "一致するeventがある行だけ。gammaは入力側にいても結果から消えます。"],
    "join.left": ["LEFT JOIN", "eventがないgammaも、右側をNULLにして残ります。"],
    "join.left-where": ["LEFT JOIN + WHERE", "JOIN後のWHEREはNULL補完行にも作用し、betaとgammaが消えます。"],
    "join.left-on": ["LEFT JOIN + ON filter", "keep条件をONへ置くと、betaとgammaの左側行はNULL補完で残ります。"],
  };
  const display = (value) => value === null ? "NULL" : String(value);

  document.getElementById("runtimeEngine").textContent = raw.execution.engine;
  document.getElementById("runtimeVersion").textContent = raw.execution.sqlite_version;
  document.getElementById("equalsNullCount").textContent = queries["null.equals-null"].rows.length;
  const isNull = queries["null.is-null"].rows;
  document.getElementById("isNullCount").textContent = `${isNull.length} · ${isNull[0].label}`;

  const truth = queries["null.truth-values"].rows[0];
  const truthItems = [
    ["NULL = NULL", truth.null_eq_null, "UNKNOWN"],
    ["NULL IS NULL", truth.null_is_null, "TRUE"],
    ["UNKNOWN OR TRUE", truth.unknown_or_true, "TRUE"],
    ["UNKNOWN AND FALSE", truth.unknown_and_false, "FALSE"],
  ];
  document.getElementById("truthStrip").innerHTML = truthItems.map(([label, actual, word]) =>
    `<div class="truth-chip"><small>${label}</small><strong>${word}</strong><small>raw: ${display(actual)}</small></div>`
  ).join("");

  function showJoin(id) {
    const item = queries[id];
    document.querySelectorAll("[data-query]").forEach((button) =>
      button.setAttribute("aria-pressed", String(button.dataset.query === id))
    );
    document.getElementById("joinTitle").textContent = joinCopy[id][0];
    document.getElementById("joinCount").textContent = `${item.rows.length} rows`;
    document.getElementById("joinSql").textContent = item.sql;
    document.getElementById("joinNote").textContent = joinCopy[id][1];
    document.getElementById("joinRows").innerHTML = item.rows.map((row) => {
      const cells = [row.row_id, row.label, row.event_id, row.kind].map((value) =>
        `<td class="${value === null ? "null-cell" : ""}">${display(value)}</td>`
      ).join("");
      return `<tr>${cells}<td class="kept">kept</td></tr>`;
    }).join("");
  }
  document.querySelectorAll("[data-query]").forEach((button) =>
    button.addEventListener("click", () => showJoin(button.dataset.query))
  );
  showJoin("join.inner");

  const cases = raw.constraints.cases;
  document.getElementById("constraintGrid").innerHTML = cases.map((item) => {
    const title = {
      "constraint.not-null": "NOT NULL",
      "constraint.unique-non-null": "UNIQUE",
      "constraint.foreign-key": "FOREIGN KEY",
    }[item.id];
    const identity = item.sqlite_errorname || item.error_type;
    return `<article><span class="badge actual">actual error</span><h3>${title}</h3><p class="rejected">REJECTED</p><code>${identity}</code><p>${item.message}</p></article>`;
  }).join("");
})();

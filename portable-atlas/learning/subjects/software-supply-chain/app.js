/* 実生成済みfileと検査結果の再生。ブラウザ内の新buildではない。 */
(() => {
  "use strict";
  const data = window.SUPPLY_CHAIN_OBSERVATION;
  const $ = (id) => document.getElementById(id);
  if (!data || data.observation.status !== "pass") {
    $("observation-status").textContent = "実観測なし / 再生停止";
    return;
  }
  const observation = data.observation;
  const scenarios = {
    "normal": {name:"正常build",kind:"正常 / INITIAL BUILD",title:"最初の成果物を基準にする。",description:"合成source・依存config・recipeから実buildしたbytesと、署名なしmanifest。Consumerがこの初期baselineを選んでpinを別に保持した設定です。",answer:"checksum、input来歴、初期baselineは一致しました。これは今回の比較条件が揃った結果です。checksumや署名なしmanifestから、作成者のidentityや安全性を証明したわけではありません。"},
    "source-changed": {name:"Sourceだけ変更",kind:"異常 / STALE BUILD",title:"入力は変わった。成果物は古い。",description:"source.txtを変更し、artifactとmanifestを以前のまま残しました。Artifactのchecksumだけでは、このstaleな来歴を見逃します。",answer:"Artifactは変わらずmanifestとのchecksumも一致します。しかしsourceの実bytesはinput申告・初期baselineと異なります。入力と成果物のbindingが必要な理由です。"},
    "artifact-tampered": {name:"Artifact改ざん",kind:"異常 / ARTIFACT TAMPER",title:"Helloを、EVIL!へ変えた。",description:"Artifactの本文5 bytesだけを変更し、manifestは据え置き。sizeが同じでも、SHA-256は一致しません。",answer:"Artifactのsizeは同じでもdigestは変わりました。変更されていないmanifestとのchecksum照合で拒否できます。これは信頼できる比較digestが別にある条件での改ざん検出です。"},
    "manifest-only": {name:"Manifestだけ差替え",kind:"異常 / CLAIM TAMPER",title:"bytesはそのまま。来歴の申告だけが違う。",description:"manifestのsource digestを0埋めの別digestへ差替え。Artifact descriptorは変更しません。",answer:"Artifact checksumは一致しますが、source bytesとmanifestのinput申告は不一致です。Manifest自体も初期baselineと異なります。checksum検査の範囲をArtifactだけへ絞ると、来歴の差替えは検出できません。"},
    "pair-rewritten": {name:"Artifact＋Manifest変更",kind:"反例 / CONSISTENT FORGERY",title:"改ざんしたbytesに、digestも合わせた。",description:"ArtifactをEVIL!へ変更し、manifestのArtifact digestも再計算。元のinput hashとrecipe申告は残しました。",answer:"自己整合checksumとinput hashのbindingは一致しました。しかし初期baselineとは違います。署名なしmanifestには、元のinputからこのoutputを作ったと虚偽申告できます。独立基準なしのdigest照合だけでは、両方を一緒に変更した差を検出できません。"},
    "baseline-replaced": {name:"Baselineもすり替え",kind:"反例 / TRUST SUBSTITUTION",title:"比較する基準まで、届いたbundleに任せたら？",description:"Artifact・Manifestを変更し、それに合うbaselineへ差替え。最初のpinはConsumer側で固定したままです。",answer:"初期pinを別に持つ検査は、差替えbaselineのdigest不一致で拒否しました。一方、届いたbaselineからpinも作り直す検査は受理しました。何を信頼すると先に決めたのかを保つ必要があります。"},
    "source-rebuilt": {name:"Source更新＋build",kind:"更新 / NEW EXPECTATIONS NEEDED",title:"新しいsourceを、正しくbuildへ反映。",description:"sourceを変更し、ArtifactとManifestを再生成しました。整合していますが、初期baselineとは別の成果物です。",answer:"新しいsource、Artifact、Manifestのbindingは一致し、同じinputからの再buildとも一致しました。初期baselineとは違うため、その基準のままでは拒否します。更新の正当性や新baselineの承認は別の判断で、この教材では自動承認していません。"},
    "dependency-updated": {name:"依存更新＋build",kind:"更新 / LOCAL DEPENDENCY CONFIG",title:"依存configの更新も、outputへ伝わる。",description:"合成依存configを1.0.0のv1 prefixから1.1.0のv2 prefixへ更新し、ArtifactとManifestを実再生成しました。package resolverは使っていません。",answer:"依存configのbytes・version・prefixが変わり、ArtifactとManifestのdigestも変わりました。新inputとの整合と、初期baselineへの一致は別の検査です。更新が悪意かどうかはdigestだけでは判断できません。"}
  };
  let current = "normal", step = 0, prediction = null, showUnsafe = false;
  const row = () => observation.scenarios.find((item) => item.id === current);
  const make = (tag, className, text) => {
    const el = document.createElement(tag); if (className) el.className = className;
    if (text !== undefined) el.textContent = text; return el;
  };
  const short = (digest) => digest.slice(0,20) + "…";
  function state(id, reached, value, yes, no) {
    const el = $(id); el.textContent = reached ? value ? yes : no : "未検査";
    el.classList.toggle("pass", reached && value); el.classList.toggle("fail", reached && !value);
  }
  function render() {
    const actual = row(), meta = scenarios[current], result = actual.result;
    $("scenario-kind").textContent = meta.kind;
    $("scenario-title").textContent = meta.title;
    $("scenario-description").textContent = meta.description;
    document.querySelectorAll("[data-scenario]").forEach((button) => {
      const selected = button.dataset.scenario === current;
      button.classList.toggle("selected", selected); button.setAttribute("aria-pressed", String(selected));
    });
    $("stages").replaceChildren(...["変更", "checksum", "input", "baseline", "答え"].map((label,index) => make("span","stage"+(step>index ? " active" : ""),`${index+1} ${label}`)));
    $("next").textContent = ["変更を見る →","SHA256を照合 →","input来歴を照合 →","独立baselineを照合 →","答えを見る →","再生完了"][step];
    $("next").disabled = !prediction || step === 5;
    $("finish").disabled = !prediction || step === 5;
    $("replay-note").textContent = `${observation.execution_id} / ${actual.observed_at} の保存済み実結果。表示の操作でbuildやfile改ざんを新しく実行するものではありません。`;
    $("trusted-pin").textContent = observation.trusted_pin;
    document.querySelectorAll("[data-node]").forEach((node) => {
      const name = node.dataset.node, changed = actual.changed_files.includes(name);
      node.classList.toggle("changed",step >= 1 && changed);
      node.querySelector("code").textContent = step >= 1 ? short(actual.files[name].digest) : "操作後にdigestを表示";
      node.querySelector("span").textContent = step >= 1 ? `${actual.files[name].size} bytes · ${changed ? "初期から変更" : "初期と同じ"}` : "保存済みbytes";
    });
    state("checksum-state",step >= 2,result.checksum_match,"一致","不一致");
    state("baseline-state",step >= 4,result.baseline_match,"一致","拒否");
    $("checksum-result").textContent = step < 2 ? "まだ検査していません。" : result.checksum_match ? "Artifactの実digestとsizeは、届いたmanifestの値に一致。作成者・由来の証明は未検証です。" : "Artifactの実bytesがmanifestの申告と不一致。Artifact checksum検査で拒否。";
    $("input-result").textContent = step < 3 ? "input来歴の照合はまだ。" : `input hash binding: ${result.input_binding_match ? "一致" : "不一致"}。これは申告と手元のinputの一致で、build実行のidentity証明ではありません。`;
    $("baseline-result").textContent = step < 4 ? "まだ検査していません。" : result.baseline_match ? "独立pinと初期baselineのfile基準に一致。今回のlocal条件の受入です。" : "初期基準との照合で拒否。差替え、staleなinput、または未承認更新を区別して確認します。";
    $("baseline-extra").textContent = step < 4 ? "初期pinを固定して比較。" : `失敗した照合: ${result.errors.length ? result.errors.join(", ") : "なし"}。署名検証は未実施。`;
    $("unsafe-panel").hidden = !(current === "baseline-replaced" && step >= 4);
    $("unsafe-toggle").setAttribute("aria-pressed",String(showUnsafe));
    $("unsafe-toggle").textContent = showUnsafe ? "反例を閉じる" : "危険な検査結果を見る";
    $("unsafe-result").textContent = showUnsafe ? `届いたbaselineからpinを作り直す検査: ${actual.unsafe_pin_from_supplied_baseline_accepts ? "受理" : "拒否"}。初期pinを固定した検査: ${result.baseline_match ? "受理" : "拒否"}。元のinputで再buildしたbytesとの比較は${result.rebuild_current_inputs_matches ? "一致" : "不一致"}。` : "";
    const reached = result.checks.filter((check,index) => index === 0 ? step >= 2 : index < 4 ? step >= 3 : step >= 4);
    $("checks-list").replaceChildren(...(reached.length ? reached.map((check) => {
      const item = make("div","check-row"), label = make("div","check-label",check.label);
      label.append(make("span","",check.pass ? "MATCH" : "MISMATCH"));
      const values = make("div","check-values");
      values.append(make("strong","","expected: "),make("span","",JSON.stringify(check.expected)),make("br"),make("strong","","actual: "),make("span","",JSON.stringify(check.actual)));
      item.append(label,values);return item;
    }) : [make("p","quiet","検査を進めると、実fileから得た比較値を表示します。") ]));
    $("artifact-preview").textContent = step >= 1 ? actual.artifact_preview : "変更を見る操作で開きます。";
    $("manifest-preview").textContent = step >= 1 ? actual.manifest_preview : "変更を見る操作で開きます。";
    $("scenario-links").replaceChildren(...["source.txt","dependency.json","recipe.py","artifact.json","manifest.json","baseline.json","verification.json"].map((name) => {
      const link = make("a","",name);link.href = `${data.directory}/${actual.directory}/${name}`;return link;
    }));
    $("prediction-feedback").textContent = !prediction ? "予想を選ぶと、変更と検査を1段ずつ見られます。" : step < 2 ? "予想を記録しました。実fileの検査結果を確かめてください。" : (prediction === "accept") === result.checksum_match ? "checksumの予想と今回の結果は一致。独立baselineではどうなるでしょう？" : "checksumの予想とは違いました。どのbytesを比較しているか、確かめましょう。";
    $("answer-title").textContent = step === 5 ? current === "normal" ? "一致した範囲を、言葉にする。" : meta.title : "検査の最後で、答えを確かめる。";
    $("answer-text").textContent = step === 5 ? meta.answer : "checksumが一致することと、期待した由来であることを分けて見ます。";
    $("answer-points").replaceChildren(...(step === 5 ? [make("span","answer-point",`checksum: ${result.checksum_match ? "match" : "mismatch"}`),make("span","answer-point",`initial baseline: ${result.baseline_match ? "match" : "refused"}`),make("span","answer-point",`既知recipeで再build比較: ${result.rebuild_current_inputs_matches ? "一致" : "不一致"}`),make("span","answer-point","署名: 未実施")] : []));
  }
  $("scenarios").replaceChildren(...Object.entries(scenarios).map(([id,meta]) => {
    const button = make("button","",meta.name);button.dataset.scenario=id;
    button.addEventListener("click",() => {current=id;step=0;prediction=null;showUnsafe=false;clearPredictions();render();});return button;
  }));
  function clearPredictions() {
    document.querySelectorAll("[data-prediction]").forEach((button) => {button.classList.remove("selected");button.setAttribute("aria-pressed","false");});
  }
  document.querySelectorAll("[data-prediction]").forEach((button) => button.addEventListener("click",() => {
    prediction=button.dataset.prediction;clearPredictions();button.classList.add("selected");button.setAttribute("aria-pressed","true");render();
  }));
  $("next").addEventListener("click",() => {step=Math.min(step+1,5);render();});
  $("finish").addEventListener("click",() => {step=5;render();});
  $("reset").addEventListener("click",() => {step=0;prediction=null;showUnsafe=false;clearPredictions();render();});
  $("unsafe-toggle").addEventListener("click",() => {showUnsafe=!showUnsafe;render();});
  $("observation-status").textContent="実file生成済み / 8条件";
  $("repeat-result").replaceChildren(...["artifact","manifest"].map((name) => {
    const box=make("div","repeat-line");box.append(make("strong","",`${name} bytes: ${observation.repeat_build[name+"_bytes_equal"] ? "一致" : "不一致"}`),make("span","",observation.repeat_build[name+"_digest"]));return box;
  }));
  const runtime=observation.runtime;
  const metadata={"Catalog ID":observation.subject_id,"実行ID":observation.execution_id,"UTC観測時刻":observation.started_at+" — "+observation.completed_at,
    "実行環境":`${runtime.os} ${runtime.os_release} / ${runtime.machine} / ${runtime.implementation} ${runtime.python}`,
    "入力":observation.initial_inputs.source_ascii.trim()+" / 合成dependency config 1.0.0 → 1.1.0","Recipe":observation.initial_inputs.recipe,
    "試行/上限":"attempt 1 / retry 0 / outer command 15秒","署名":"未実装・未検証 / 独自JSON / SLSA level未実証",
    "Builder binding":observation.source_bindings["pipeline.py"],"実験binding":observation.source_bindings["experiment.py"],"実command exit":String(data.command.exit_code),"範囲":"ローカル教材 / 全Subject・理解度の完成は未測定"};
  $("metadata").replaceChildren(...Object.entries(metadata).flatMap(([key,value]) => [make("dt","",key),make("dd","",value)]));
  $("record-links").replaceChildren(...["observation.json","command.json","artifact-index.json"].map((name) => {const link=make("a","",name);link.href=data.directory+"/"+name;return link;}));
  $("command-record").textContent=JSON.stringify(data.command,null,2);
  fetch(data.directory+"/command.json").then((response) => {if(!response.ok)throw new Error("command record unavailable");return response.json();})
    .then((record) => {$("command-record").textContent=JSON.stringify(record,null,2);})
    .catch(() => {$("command-record").append("\n生stdout/stderrはcommand.jsonリンクから参照してください。");});
  render();
})();

// A projection of existing receipt fields. This module executes no native program.
export const cases = ["normal", "boundary", "failure", "rejection"];
export const labels = {normal:"通常の文字列",boundary:"空文字列",failure:"契約を破る戻り値",rejection:"null引数"};
export const snippets = {
 normal:'// Java\n@NotNull String stable(boolean empty) {\n    return empty ? "" : "atlas";\n}\n// Kotlin\nJavaNulls.stable(false).length',
 boundary:'// Java\n@NotNull String stable(boolean empty) {\n    return empty ? "" : "atlas";\n}\n// Kotlin\nJavaNulls.stable(true).length',
 failure:'// Java\n@NotNull String violatesContract() {\n    return null;\n}\n// Kotlin\nJavaNulls.violatesContract().length',
 rejection:'// Java\nint consume(@NotNull String value) {\n    return value.length();\n}\n// Kotlin\nJavaNulls.consume(null)'
};
export function validateReceipt(receipt, expected) {
 if(receipt.id!=="java-nullability-enhancement-process-pilot-v1" || receipt.schema_version!==1 ||
    !receipt.oracle?.matches || receipt.runtime_cases?.length!==3 || receipt.compile?.java?.exit_code!==0 || receipt.compile?.kotlin?.exit_code!==0 ||
    receipt.toolchain?.compiler?.version!=="2.4.10" || receipt.toolchain?.java?.version!=="17.0.17" ||
    expected.compiler_version!=="2.4.10" || expected.rejection_diagnostic_id!=="NULL_FOR_NONNULL_TYPE") throw new Error("保存原票の形式・有限条件を確認できません。");
 for(const id of cases.slice(0,3)) {
  const records=receipt.runtime_cases.filter(r=>r.name===id), e=expected[id];
  if(records.length!==1 || !e || !records[0].oracle_matches || records[0].exit_code!==e.exit_code || !records[0].stdout_matches || !records[0].stderr_matches) throw new Error("runtimeの記録と期待値が一致しません。");
 }
 const reject=receipt.compile.rejection;
 if(reject.exit_code!==1 || reject.output_artifact_created!==false || reject.diagnostic_id!==expected.rejection_diagnostic_id || !reject.diagnostic_id_matches) throw new Error("compile拒否の記録が一致しません。");
}
export function projectCase(receipt, expected, id) {
 if(!cases.includes(id)) throw new Error("未知の条件です。");
 validateReceipt(receipt,expected);
 if(id==="rejection") {
  const r=receipt.compile.rejection;
  return {id,kind:"compile-rejection",outcome:"compileで拒否 / exit 1",record:`diagnostic = ${r.diagnostic_id}\n生成JARなし。拒否されたソースのruntime記録なし。`,expectation:`固定期待 diagnostic = ${expected.rejection_diagnostic_id}\n元原票の一致判定 = ${r.diagnostic_id_matches}`,digestNote:"diagnostic IDと一致判定は保存されています。完全なcompiler stderrは保存されていません。",comparison:[labels[id],"compile拒否・JARなし・runtimeなし",r.diagnostic_id],raw:{compile:r},explanation:"Kotlinから@NotNullの引数へnullを渡すソースが、NULL_FOR_NONNULL_TYPEとして拒否された記録です。実行した結果のNPEではありません。Javaの戻り値が契約を守るかとは別の検査です。"};
 }
 const r=receipt.runtime_cases.find(row=>row.name===id),e=expected[id],normal=id!=="failure";
 return {id,kind:normal?"normal":"runtime-failure",outcome:normal?"正常終了 / exit 0":"実行時失敗 / exit 1",record:`Kotlin compileは受理。runtime exit = ${r.exit_code}\n元原票の期待照合 = ${r.oracle_matches}`+(normal?"":"\n契約違反を直接JVM NPEとして観測した判定 = "+receipt.oracle.runtime_contract_violation_observed_as_direct_jvm_npe),expectation:normal?`固定期待 stdout = ${JSON.stringify(e.stdout)}\nこの文字列のSHA-256を保存stdout digestと照合します。`:`固定期待 stderrの部分文字列 = ${JSON.stringify(e.stderr_contains)}\n元原票の部分文字列照合 = ${r.stderr_matches}`,digestNote:normal?"期待文字列と保存digestの対応です。保存stdout全文の再生ではありません。":"stderr全文は未保存です。ここでNPE文字列の再照合はできず、原票に残る判定を読んでいます。",comparison:[labels[id],normal?"runtime正常 / exit 0":"runtime失敗 / exit 1",normal?"固定stdout "+JSON.stringify(e.stdout):"NPE部分文字列の照合true（元記録）"],raw:{compile:receipt.compile.kotlin,runtime:r,...(normal?{}:{bytecode_oracle:receipt.bytecode_oracle,contract_violation_judgement:receipt.oracle.runtime_contract_violation_observed_as_direct_jvm_npe})},explanation:id==="normal"?"Java実装はatlasを返し、Kotlin利用側はlengthを読みます。長さ5という固定期待のdigestが保存stdout digestと一致します。この値の説明はソースと期待値に基づきます。":id==="boundary"?"空文字列はnullではありません。lengthは0で、今回の契約に沿った正常な結果です。固定期待RESULT=0のdigestと元原票の一致判定を確認できます。":"Javaの宣言には@NotNullがありますが、実装はnullを返します。Kotlin利用側がlengthを読むため、原票は実行時失敗とNPEへの一致を記録しています。保存bytecode判定も補助根拠ですが、全文や実traceは未保存です。annotationだけからJava実装の実行時安全性を保証できません。"};
}

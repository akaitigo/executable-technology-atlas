import { readFile } from 'node:fs/promises';

export async function preserveRecordedGraphSnapshot(outputPath, candidate) {
  let recorded;
  try {
    recorded = JSON.parse(await readFile(outputPath, 'utf8'));
  } catch {
    return candidate;
  }

  if (recorded?.source?.dependencyGraph && candidate?.source?.dependencyGraph) {
    candidate.source.dependencyGraph = structuredClone(recorded.source.dependencyGraph);
  }
  if (recorded?.observed?.dependencyGraph && candidate?.observed?.dependencyGraph) {
    candidate.observed.dependencyGraph = structuredClone(recorded.observed.dependencyGraph);
  }
  // A bounded completion certificate is a derived attachment generated from
  // the commit containing readiness evidence. Preserve its recorded identity
  // to avoid a certificate -> readiness -> certificate digest cycle. Callers
  // still validate the live certificate payload before accepting the report.
  if (recorded?.source?.boundedCertificate && candidate?.source?.boundedCertificate) {
    candidate.source.boundedCertificate = structuredClone(recorded.source.boundedCertificate);
  }
  if (recorded?.observed?.boundedCertificate?.payloadDigest && candidate?.observed?.boundedCertificate) {
    candidate.observed.boundedCertificate.payloadDigest = recorded.observed.boundedCertificate.payloadDigest;
  }
  return candidate;
}

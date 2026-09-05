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
  return candidate;
}

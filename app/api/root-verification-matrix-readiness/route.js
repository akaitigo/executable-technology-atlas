import { readFile } from 'node:fs/promises';
import path from 'node:path';
import { validatePortalRootVerificationMatrixReadiness } from '../../../scripts/lib/portal-root-verification-matrix-readiness.mjs';
import { assertPortalRootVerificationMatrixReadinessSnapshot } from '../../lib/portal-root-verification-matrix-readiness.mjs';

export const dynamic = 'force-dynamic';
export const revalidate = 0;

function json(body, status) {
  return new Response(JSON.stringify(body), {
    status,
    headers: {
      'Cache-Control': 'no-store',
      'Content-Type': 'application/json; charset=utf-8',
    },
  });
}

export async function GET() {
  try {
    const root = process.cwd();
    const [schemaBytes, reportBytes] = await Promise.all([
      readFile(path.join(root, 'contracts/schemas/portal-root-verification-matrix-readiness.schema.json'), 'utf8'),
      readFile(path.join(root, 'evidence/portal-root-verification-matrix-readiness.json'), 'utf8'),
    ]);
    const schema = JSON.parse(schemaBytes);
    const report = JSON.parse(reportBytes);
    const result = await validatePortalRootVerificationMatrixReadiness(root, report, schema);
    if (!result.ok) {
      return json({ ok: false, status: 'not-evaluated', errors: result.errors }, 503);
    }
    return json(assertPortalRootVerificationMatrixReadinessSnapshot(report), 200);
  } catch (error) {
    return json({
      ok: false,
      status: 'not-evaluated',
      errors: [error instanceof Error ? error.message : 'unknown-error'],
    }, 503);
  }
}

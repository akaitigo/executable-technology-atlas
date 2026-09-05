import { evaluatePortalEvidenceRefreshReadiness, loadPortalEvidenceRefreshPolicy } from '../../../scripts/lib/portal-evidence-refresh-readiness.mjs';
import { assertPortalEvidenceRefreshStatusSnapshot } from '../../lib/portal-evidence-refresh-status.mjs';

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
    const { policy, schema } = await loadPortalEvidenceRefreshPolicy(process.cwd());
    const result = await evaluatePortalEvidenceRefreshReadiness(process.cwd(), policy, schema);
    if (!result.ok) {
      return json({ ok: false, status: 'not-evaluated', errors: result.errors }, 503);
    }
    return json(assertPortalEvidenceRefreshStatusSnapshot(result.report), 200);
  } catch (error) {
    return json({
      ok: false,
      status: 'not-evaluated',
      errors: [error instanceof Error ? error.message : 'unknown-error'],
    }, 503);
  }
}

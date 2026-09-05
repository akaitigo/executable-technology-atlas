import { evaluatePortalIntegrationStatus } from '../../../scripts/lib/portal-integration-status.mjs';
import { assertPortalIntegrationStatusSnapshot } from '../../lib/portal-integration-status.mjs';

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
    const result = await evaluatePortalIntegrationStatus(process.cwd());
    if (!result.ok) {
      return json({ ok: false, status: 'not-evaluated', errors: result.errors }, 503);
    }
    return json(assertPortalIntegrationStatusSnapshot(result.report), 200);
  } catch (error) {
    return json({
      ok: false,
      status: 'not-evaluated',
      errors: [error instanceof Error ? error.message : 'unknown-error'],
    }, 503);
  }
}

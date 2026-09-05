import { evaluatePortalImportLifecycleVisibility } from '../../../scripts/lib/portal-import-lifecycle-visibility.mjs';
import { assertPortalImportLifecycleSnapshot } from '../../lib/portal-import-lifecycle-visibility.mjs';

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
    const result = await evaluatePortalImportLifecycleVisibility(process.cwd());
    if (!result.ok) {
      return json({ ok: false, status: 'not-evaluated', errors: result.errors }, 503);
    }
    return json(assertPortalImportLifecycleSnapshot(result.report), 200);
  } catch (error) {
    return json({
      ok: false,
      status: 'not-evaluated',
      errors: [error instanceof Error ? error.message : 'unknown-error'],
    }, 503);
  }
}

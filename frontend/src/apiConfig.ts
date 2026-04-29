/** Backend base URL. Vite in-browser: use `import.meta.env`, never `process.env`. */
const envUrl = (import.meta.env.VITE_API_URL as string | undefined)?.trim();

/**
 * In dev, default to same-origin (empty) so requests hit the Vite proxy and PDF/image
 * URLs match the app origin (avoids 404 / CORS mismatches). In production builds, default
 * to localhost unless VITE_API_URL is set (e.g. Render/Vercel).
 */
export const API_BASE_URL =
  envUrl || (import.meta.env.DEV ? '' : 'http://localhost:8000');

/** Binary file fetch for document preview (same rules as API_BASE_URL). */
export function documentFileUrl(documentId: string): string {
  const base = API_BASE_URL.replace(/\/$/, '');
  return `${base}/documents/${documentId}/file`;
}

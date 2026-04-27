/** Backend base URL. Vite in-browser: use `import.meta.env`, never `process.env`. */
export const API_BASE_URL =
  (import.meta.env.VITE_API_URL as string | undefined)?.trim() ||
  "http://localhost:8000";

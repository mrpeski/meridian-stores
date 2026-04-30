/** Production: set `VITE_API_BASE_URL` to the API Gateway origin (no trailing slash). Dev: leave unset so `/api/*` hits the Vite proxy. */
export function apiUrl(path: string): string {
  const raw = import.meta.env.VITE_API_BASE_URL;
  const base = typeof raw === "string" ? raw.replace(/\/$/, "") : "";
  if (!base) {
    return path.startsWith("/") ? path : `/${path}`;
  }
  const p = path.startsWith("/") ? path : `/${path}`;
  return `${base}${p}`;
}

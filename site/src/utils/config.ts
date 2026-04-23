import { siteConfig } from "../../site.config";

export { siteConfig };

/** Full URL for a path.
 *
 * CF Pages serves pages with an enforced trailing slash (308 redirect on
 * bare paths). Canonical tags, og:url, hreflang and internal links built
 * from fullUrl() must include the slash; otherwise GSC flags the page
 * as "Alternative page with proper canonical tag" because the canonical
 * target redirects.
 */
export function fullUrl(path: string): string {
  const base = siteConfig.url.replace(/\/$/, "");
  const clean = path.startsWith("/") ? path : `/${path}`;
  const hasFileExt = /\.[a-z0-9]{2,5}($|[?#])/i.test(clean);
  const hasSuffix = /[/?#]$/.test(clean) || clean.includes("?") || clean.includes("#");
  if (hasFileExt || hasSuffix) return `${base}${clean}`;
  return `${base}${clean}/`;
}

/** Get Google Fonts URL */
export function fontsUrl(): string {
  const display = siteConfig.fonts.display.replace(/ /g, "+");
  const body = siteConfig.fonts.body.replace(/ /g, "+");
  return `https://fonts.googleapis.com/css2?family=${display}:wght@600;700;800&family=${body}:wght@400;500;600&display=swap`;
}

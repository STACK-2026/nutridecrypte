import { siteConfig } from "../../site.config";

export { siteConfig };

/** Full URL for a path */
export function fullUrl(path: string): string {
  const base = siteConfig.url.replace(/\/$/, "");
  const clean = path.startsWith("/") ? path : `/${path}`;
  return `${base}${clean}`;
}

/** Get Google Fonts URL */
export function fontsUrl(): string {
  const display = siteConfig.fonts.display.replace(/ /g, "+");
  const body = siteConfig.fonts.body.replace(/ /g, "+");
  return `https://fonts.googleapis.com/css2?family=${display}:wght@600;700;800&family=${body}:wght@400;500;600&display=swap`;
}

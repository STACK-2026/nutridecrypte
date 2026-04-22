import type { APIRoute } from "astro";

// Default homepage OG image. Product OG images will be added in Phase 1 when the
// product catalog is wired to Open Food Facts.
export function getStaticPaths() {
  return [{ params: { slug: "default" } }];
}

export const GET: APIRoute = async () => {
  const svg = `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1200 630" width="1200" height="630">
  <defs>
    <linearGradient id="bg" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#065f46"/>
      <stop offset="100%" stop-color="#0f766e"/>
    </linearGradient>
  </defs>
  <rect width="1200" height="630" fill="url(#bg)"/>
  <g transform="translate(180,200)">
    <rect width="240" height="260" rx="12" fill="#ffffff" opacity="0.12" stroke="#ffffff" stroke-width="3" stroke-opacity="0.5"/>
    <line x1="30" y1="50" x2="210" y2="50" stroke="#ffffff" stroke-width="3" stroke-linecap="round" opacity="0.7"/>
    <line x1="30" y1="90" x2="190" y2="90" stroke="#ffffff" stroke-width="3" stroke-linecap="round" opacity="0.7"/>
    <line x1="30" y1="130" x2="170" y2="130" stroke="#ffffff" stroke-width="3" stroke-linecap="round" opacity="0.5"/>
    <line x1="30" y1="170" x2="150" y2="170" stroke="#ffffff" stroke-width="3" stroke-linecap="round" opacity="0.4"/>
    <circle cx="200" cy="215" r="36" fill="none" stroke="#f59e0b" stroke-width="6"/>
    <line x1="226" y1="241" x2="256" y2="271" stroke="#f59e0b" stroke-width="6" stroke-linecap="round"/>
  </g>
  <text x="490" y="290" font-family="system-ui,-apple-system,sans-serif" font-size="28" font-weight="800" fill="#5eead4" letter-spacing="4">NUTRIDECRYPTE.COM</text>
  <text x="490" y="360" font-family="system-ui,-apple-system,sans-serif" font-size="60" font-weight="900" fill="#ffffff">On decrypte</text>
  <text x="490" y="420" font-family="system-ui,-apple-system,sans-serif" font-size="60" font-weight="900" fill="#ffffff">les etiquettes.</text>
  <text x="490" y="480" font-family="system-ui,-apple-system,sans-serif" font-size="24" font-weight="500" fill="#cfe4db">Nutri-Score + NOVA + EFSA + ANSES, A to E, free.</text>
</svg>`;

  return new Response(svg, {
    headers: { "Content-Type": "image/svg+xml" },
  });
};

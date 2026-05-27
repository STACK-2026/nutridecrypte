// Amazon Partenaires France configuration for NutriDecrypte.
// Single-merchant launch (2026-05-27). Tag nutridecrypte-21, amazon.fr only.

export const AMAZON_TAG = import.meta.env.PUBLIC_AMAZON_TAG ?? "";
export const AMAZON_DOMAIN = "https://www.amazon.fr";

// French supermarket distributor brands (own-label not sold on Amazon).
const FR_DISTRIBUTOR_BRANDS = new Set<string>([
  "auchan",
  "carrefour",
  "u",
  "systeme u",
  "super u",
  "monoprix",
  "leclerc",
  "marque repere",
  "intermarche",
  "casino",
  "lidl",
  "aldi",
  "cora",
  "netto",
  "dia",
  "franprix",
]);

export function isDistributorBrand(brand: string | null | undefined): boolean {
  if (!brand) return false;
  return FR_DISTRIBUTOR_BRANDS.has(brand.trim().toLowerCase());
}

export function buildGoPath(slug: string): string {
  return `/go/${encodeURIComponent(slug)}`;
}

// amazon.fr search URL with our affiliate tag.
export function buildAmazonSearchUrl(opts: { query: string; tag?: string }): string | null {
  const tag = opts.tag ?? AMAZON_TAG;
  if (!tag) return null;
  const q = (opts.query ?? "").trim();
  if (!q) return null;
  const params = new URLSearchParams({
    k: q,
    tag,
    linkCode: "osi",
    ref: "as_li_ss_tl",
  });
  return `${AMAZON_DOMAIN}/s?${params.toString()}`;
}

// amazon.fr direct ASIN URL with tag.
export function buildAmazonAsinUrl(asin: string, tag?: string): string | null {
  const t = tag ?? AMAZON_TAG;
  if (!t || !asin) return null;
  if (!/^[A-Z0-9]{10}$/.test(asin)) return null;
  return `${AMAZON_DOMAIN}/dp/${asin}?tag=${encodeURIComponent(t)}&linkCode=osi&ref=as_li_ss_tl`;
}

// Awin affiliate configuration for NutriDécrypte.
// Monetization: food, supplements, and organic brands. No partner validated yet (Phase 0).
// When a merchant is approved, add its config to MERCHANTS and extend routeMerchant().

export const AWIN_PUBLISHER_ID = "";

export const MERCHANTS = {
  // placeholder, awaiting validation
} as const;

export type MerchantKey = keyof typeof MERCHANTS;

// Supermarket distributor brands (own-label lines not sold by affiliate partners).
// Kept lowercase. Match is case-insensitive, exact trim.
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

export function isDistributorBrand(brand: string): boolean {
  if (!brand) return false;
  return FR_DISTRIBUTOR_BRANDS.has(brand.trim().toLowerCase());
}

export function isMonetizableCountry(country: string | undefined): boolean {
  if (!country) return true;
  return ["FR", "BE", "CH", "EU", "INTL"].includes(country.toUpperCase());
}

export function buildGoPath(productId: string): string {
  return `/go/${productId}`;
}

// Curated Amazon FR search queries for NutriDecrypte niche.
// Each entry maps a topic/keyword cluster to an Amazon search query that
// returns relevant supplements/products. Search URLs (not /dp/ASIN) because:
//   1. PA-API access requires 3 sales/180d, bootstrap chicken-and-egg.
//   2. ASIN variants rotate; brand queries stay evergreen.

export interface AmazonPick {
  query: string;
  label: string;
  topic: "magnesium" | "collagene" | "vitamine-d" | "omega-3" | "probiotiques" | "additifs" | "general" | "bio";
  highlight?: string;
  /** Optional curation key matching `nutri_asins.csv`. When the ASIN map has
   *  a value for this key, link points to /dp/<ASIN>; search URL otherwise. */
  key?: string;
}

export const AMAZON_PICKS: AmazonPick[] = [
  // Magnesium
  { key: "magnesium-bisglycinate", query: "magnesium bisglycinate", label: "Magnésium bisglycinate", topic: "magnesium", highlight: "Forme premium" },
  { key: "magnesium-citrate", query: "magnesium citrate", label: "Magnésium citrate", topic: "magnesium" },
  { key: "magnesium-marin", query: "magnesium marin", label: "Magnésium marin", topic: "magnesium", highlight: "Multi-formes" },
  // Collagène
  { key: "collagene-marin-hydrolyse", query: "collagene marin hydrolysé", label: "Collagène marin hydrolysé", topic: "collagene", highlight: "Type I+III" },
  { key: "collagene-bovin-peptides", query: "collagene bovin peptides", label: "Collagène bovin peptides", topic: "collagene" },
  // Vitamine D
  { key: "vitamine-d3-k2", query: "vitamine d3 k2", label: "Vitamine D3 + K2", topic: "vitamine-d", highlight: "Synergie" },
  { key: "vitamine-d3-1000ui", query: "vitamine d3 1000 ui", label: "Vitamine D3 1000 UI", topic: "vitamine-d" },
  // Omega 3
  { key: "omega-3-epax", query: "omega 3 epax certifie", label: "Oméga-3 EPAX", topic: "omega-3", highlight: "Norvégien certifié" },
  { key: "omega-3-vegan-algue", query: "omega 3 vegan algue", label: "Oméga-3 vegan (algues)", topic: "omega-3" },
  // Probiotiques
  { key: "probiotiques-30-milliards", query: "probiotiques 30 milliards souches", label: "Probiotiques multi-souches", topic: "probiotiques", highlight: "30+ milliards UFC" },
  { key: "probiotiques-lactobacillus", query: "probiotiques lactobacillus rhamnosus", label: "Probiotiques Lactobacillus", topic: "probiotiques" },
  // Bio / label AB
  { key: "complement-bio", query: "complement alimentaire bio", label: "Compléments bio (label AB)", topic: "bio", highlight: "Certifiés AB" },
  { key: "spiruline-bio-france", query: "spiruline bio france", label: "Spiruline bio française", topic: "bio" },
  // Additifs / décryptage
  { key: "guide-etiquettes", query: "guide decryptage etiquettes alimentaires", label: "Lire les étiquettes alimentaires", topic: "additifs" },
  // General
  { key: "multivitamines-adulte", query: "multivitamines adulte", label: "Multivitamines adulte", topic: "general" },
  { key: "zinc-bisglycinate", query: "zinc bisglycinate", label: "Zinc bisglycinate", topic: "general", highlight: "Bonne biodispo" },
];

export function getPicksByTopic(
  topic: AmazonPick["topic"],
  count = 3,
): AmazonPick[] {
  return AMAZON_PICKS.filter((p) => p.topic === topic).slice(0, count);
}

// Heuristic: derive a topic from blog post slug/keywords.
export function inferTopicFromSlug(slug: string): AmazonPick["topic"] {
  const s = slug.toLowerCase();
  if (/magnes/i.test(s)) return "magnesium";
  if (/collag/i.test(s)) return "collagene";
  if (/vitamine.?d|vitamin.?d|cholecalciferol/i.test(s)) return "vitamine-d";
  if (/omega.?3|epa|dha|huile.de.poisson/i.test(s)) return "omega-3";
  if (/probiotiq|microbiote|lactobacill|bifidobact/i.test(s)) return "probiotiques";
  if (/bio|label.ab|biologique/i.test(s)) return "bio";
  if (/additif|e\d{3}|colorant|conservateur/i.test(s)) return "additifs";
  return "general";
}

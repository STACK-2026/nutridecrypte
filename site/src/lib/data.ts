// NutriDecrypte , build-time data fetcher from the VPS Postgres (Tier-2 migration 2026-06-01).
// Used by getStaticPaths() to pre-render product / brand / category pages.
// Was Supabase REST; now reads the shared VPS Postgres via src/lib/db.ts (DATABASE_URL + CF tunnel).

import { db, dbConfigured } from "./db";

export interface Product {
  id: number;
  slug: string;
  barcode: string | null;
  name: string;
  brand_slug: string | null;
  categories: string[];
  countries: string[];
  off_data: Record<string, unknown> | null;
  ingredients_text: string | null;
  nutrition_grade: string | null;
  nova_group: number | null;
  additives_tags: string[];
  allergens_tags: string[];
  labels_tags: string[];
  score_nutri: number | null;
  score_nova: number | null;
  score_additives: number | null;
  score_claims: number | null;
  score_density: number | null;
  score_overall: number | null;
  grade: "A" | "B" | "C" | "D" | "E" | null;
  verdict_en: string | null;
  verdict_fr: string | null;
  warnings: unknown;
  image_url: string | null;
  image_small_url: string | null;
  created_at: string;
  updated_at: string;
  last_scored_at: string | null;
}

export interface Brand {
  id: number;
  slug: string;
  name: string;
  country: string | null;
  parent_company: string | null;
  website: string | null;
  description: string | null;
  description_fr: string | null;
  average_grade: string | null;
  average_score: number | null;
  product_count: number;
}

export interface Additive {
  id: number;
  e_number: string;
  slug: string;
  name_en: string;
  name_fr: string | null;
  category: string | null;
  risk_level: "low" | "medium" | "high" | "unknown";
  controversy: boolean;
  banned_in: string[];
  anses_opinion: string | null;
  efsa_opinion_url: string | null;
  last_reviewed_at: string | null;
  summary_en: string | null;
  summary_fr: string | null;
}

const DEFAULT_LIMIT = 1000;

// ============================================================
// Products
// ============================================================
export async function getAllProducts(limit = DEFAULT_LIMIT): Promise<Product[]> {
  if (!dbConfigured()) return [];
  const rows = await db()<Product[]>`select * from products order by score_overall desc nulls last limit ${limit}`;
  return rows as unknown as Product[];
}

export async function getProductBySlug(slug: string): Promise<Product | null> {
  if (!dbConfigured()) return null;
  const rows = await db()<Product[]>`select * from products where slug = ${slug} limit 1`;
  return rows.length ? (rows[0] as unknown as Product) : null;
}

export async function getProductsByBrand(brandSlug: string): Promise<Product[]> {
  if (!dbConfigured()) return [];
  const rows = await db()<Product[]>`select * from products where brand_slug = ${brandSlug} order by score_overall desc nulls last limit 200`;
  return rows as unknown as Product[];
}

export async function getProductsByCategory(categoryTag: string, limit = 50): Promise<Product[]> {
  if (!dbConfigured()) return [];
  // categories is a text[] column; array containment
  const rows = await db()<Product[]>`select * from products where ${categoryTag} = any(categories) order by score_overall desc nulls last limit ${limit}`;
  return rows as unknown as Product[];
}

// ============================================================
// Brands
// ============================================================
export async function getAllBrands(limit = 500): Promise<Brand[]> {
  if (!dbConfigured()) return [];
  const rows = await db()<Brand[]>`select * from brands order by slug asc limit ${limit}`;
  return rows as unknown as Brand[];
}

export async function getBrandBySlug(slug: string): Promise<Brand | null> {
  if (!dbConfigured()) return null;
  const rows = await db()<Brand[]>`select * from brands where slug = ${slug} limit 1`;
  return rows.length ? (rows[0] as unknown as Brand) : null;
}

// ============================================================
// Categories (derived from products.categories[])
// ============================================================
export interface CategoryHub {
  slug: string;             // cleaned tag without 'en:' prefix
  raw_tag: string;          // original OFF tag
  product_count: number;
  avg_score: number;
  grade_distribution: Record<string, number>;
}

export function deriveCategories(products: Product[], minProducts = 3): CategoryHub[] {
  const hubs: Record<string, { raw: string; scores: number[]; grades: Record<string, number> }> = {};
  for (const p of products) {
    for (const rawTag of p.categories || []) {
      const slug = rawTag.replace(/^(en|fr|de|es|it):/, "").toLowerCase();
      if (!slug) continue;
      if (!hubs[slug]) {
        hubs[slug] = { raw: rawTag, scores: [], grades: { A: 0, B: 0, C: 0, D: 0, E: 0 } };
      }
      if (p.score_overall != null) hubs[slug].scores.push(p.score_overall);
      if (p.grade) hubs[slug].grades[p.grade] = (hubs[slug].grades[p.grade] || 0) + 1;
    }
  }
  const out: CategoryHub[] = [];
  for (const [slug, data] of Object.entries(hubs)) {
    const n = data.scores.length;
    if (n < minProducts) continue;
    const avg = Math.round(data.scores.reduce((a, b) => a + b, 0) / n);
    out.push({
      slug,
      raw_tag: data.raw,
      product_count: n,
      avg_score: avg,
      grade_distribution: data.grades,
    });
  }
  out.sort((a, b) => b.product_count - a.product_count);
  return out;
}

// ============================================================
// Additives
// ============================================================
export async function getAllAdditives(): Promise<Additive[]> {
  if (!dbConfigured()) return [];
  const rows = await db()<Additive[]>`select * from additives order by e_number asc`;
  return rows as unknown as Additive[];
}

export async function getAdditiveBySlug(slug: string): Promise<Additive | null> {
  if (!dbConfigured()) return null;
  const rows = await db()<Additive[]>`select * from additives where slug = ${slug} limit 1`;
  return rows.length ? (rows[0] as unknown as Additive) : null;
}

// ============================================================
// Helpers
// ============================================================
export function pickVerdict(product: Product, locale: "en" | "fr"): string {
  if (locale === "fr" && product.verdict_fr) return product.verdict_fr;
  if (locale === "en" && product.verdict_en) return product.verdict_en;
  // Fallback: generate from warnings and grade
  const g = product.grade || "?";
  const n = (product.additives_tags || []).length;
  if (locale === "fr") {
    return `Note ${g}. ${n} additif${n > 1 ? "s" : ""} detecte${n > 1 ? "s" : ""} dans la liste d'ingredients.`;
  }
  return `Grade ${g}. ${n} additive${n > 1 ? "s" : ""} detected in the ingredient list.`;
}

export function gradeColorVar(grade: string | null): string {
  if (!grade) return "var(--color-ink-soft)";
  return `var(--grade-${grade.toLowerCase()})`;
}

export function cleanCategorySlug(raw: string): string {
  return raw.replace(/^(en|fr|de|es|it):/, "").toLowerCase();
}

export function prettyCategoryName(slug: string): string {
  return slug.replace(/-/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());
}

// ============================================
// NutriDécrypte Score , deterministic A to E grading
// ============================================
//
// Philosophy: same ingredient list, same grade, every time.
// 5 weighted axes combined into a single 0-100 score then mapped to a letter.
// TODO Phase 1 , wire real component inputs from Open Food Facts + EFSA + ANSES.

export type Grade = "A" | "B" | "C" | "D" | "E";
export type NutriScoreLetter = "A" | "B" | "C" | "D" | "E";
export type NovaClass = 1 | 2 | 3 | 4;

export interface Additive {
  /** E number (e.g. "E950") or INS code. */
  code: string;
  /** ANSES / EFSA risk bucket: 0 = neutral, 1 = watch, 2 = suspected, 3 = to avoid. */
  risk: 0 | 1 | 2 | 3;
  name?: string;
}

export interface MarketingClaim {
  /** Raw claim as printed on the front of pack. */
  text: string;
  /** Post-audit verdict against the ingredient list / nutrition panel. */
  verdict: "honest" | "stretched" | "misleading";
}

export interface NutritionPanel {
  /** Grams per 100 g unless noted. */
  protein: number;
  fiber: number;
  sugar: number;
  saturatedFat: number;
  sodium: number; // mg
  micronutrientDensity?: number; // 0-100, optional pre-computed index
}

export interface ScoringInput {
  nutriScore?: NutriScoreLetter;
  nova?: NovaClass;
  additives?: Additive[];
  claims?: MarketingClaim[];
  nutrition?: NutritionPanel;
}

export interface ScoringBreakdown {
  nutriScore: number;
  nova: number;
  additives: number;
  claims: number;
  density: number;
}

export interface ScoringResult {
  score: number; // 0-100
  grade: Grade;
  breakdown: ScoringBreakdown;
}

// ============================================
// Weights (sum = 1.0). Keep in sync with /methodology page.
// ============================================
export const WEIGHTS = {
  nutriScore: 0.25,
  nova: 0.25,
  additives: 0.2,
  claims: 0.15,
  density: 0.15,
} as const;

// ============================================
// Grade thresholds on the final 0-100 score.
// ============================================
export const GRADE_THRESHOLDS: Record<Grade, number> = {
  A: 85,
  B: 70,
  C: 55,
  D: 40,
  E: 0,
};

export const GRADE_COLOURS: Record<Grade, string> = {
  A: "#0f766e",
  B: "#84cc16",
  C: "#eab308",
  D: "#f97316",
  E: "#dc2626",
};

export const GRADE_LABELS_EN: Record<Grade, string> = {
  A: "Excellent",
  B: "Good",
  C: "Average",
  D: "Poor",
  E: "Avoid",
};

export const GRADE_LABELS_FR: Record<Grade, string> = {
  A: "Excellent",
  B: "Bon",
  C: "Moyen",
  D: "Médiocre",
  E: "À éviter",
};

export function gradeLabel(g: Grade, locale: "en" | "fr"): string {
  return locale === "fr" ? GRADE_LABELS_FR[g] : GRADE_LABELS_EN[g];
}

// ============================================
// Component scorers (each returns a 0-100 value)
// ============================================

/**
 * Map official Nutri-Score letter to a 0-100 value.
 * Official Nutri-Score: A best, E worst.
 */
export function computeNutriScoreComponent(letter?: NutriScoreLetter): number {
  if (!letter) return 50; // neutral when unknown
  const map: Record<NutriScoreLetter, number> = {
    A: 95,
    B: 78,
    C: 60,
    D: 40,
    E: 15,
  };
  return map[letter];
}

/**
 * Map NOVA ultra-processing class to a 0-100 value.
 * NOVA 1 = unprocessed, NOVA 4 = ultra-processed.
 */
export function computeNovaComponent(nova?: NovaClass): number {
  if (!nova) return 55;
  const map: Record<NovaClass, number> = {
    1: 95,
    2: 78,
    3: 55,
    4: 20,
  };
  return map[nova];
}

/**
 * Score the additive list. Each additive is weighted by its EFSA/ANSES risk.
 * 0 additives = 100, heavy risk profile = 0.
 */
export function computeAdditiveRisk(additives?: Additive[]): number {
  if (!additives || additives.length === 0) return 100;
  const riskPenalty: Record<Additive["risk"], number> = {
    0: 3,
    1: 10,
    2: 22,
    3: 40,
  };
  const totalPenalty = additives.reduce((acc, a) => acc + riskPenalty[a.risk], 0);
  return Math.max(0, Math.min(100, 100 - totalPenalty));
}

/**
 * Audit marketing claims. "honest" has no penalty, "misleading" is heavy.
 */
export function auditClaims(claims?: MarketingClaim[]): number {
  if (!claims || claims.length === 0) return 90;
  const penalty: Record<MarketingClaim["verdict"], number> = {
    honest: 0,
    stretched: 12,
    misleading: 30,
  };
  const totalPenalty = claims.reduce((acc, c) => acc + penalty[c.verdict], 0);
  return Math.max(0, Math.min(100, 100 - totalPenalty));
}

/**
 * Score nutritional density.
 * Rewards protein and fiber, penalizes excess sugar, saturated fat, and sodium.
 * Optional pre-computed index (micronutrientDensity) overrides the formula.
 */
export function computeNutritionalDensity(nutrition?: NutritionPanel): number {
  if (!nutrition) return 55;
  if (typeof nutrition.micronutrientDensity === "number") {
    return Math.max(0, Math.min(100, nutrition.micronutrientDensity));
  }
  const positive = Math.min(30, nutrition.protein * 1.2) + Math.min(30, nutrition.fiber * 3);
  const sugarPenalty = Math.min(35, nutrition.sugar * 1.2);
  const satFatPenalty = Math.min(25, nutrition.saturatedFat * 2);
  const sodiumPenalty = Math.min(20, nutrition.sodium / 20);
  const raw = 60 + positive - sugarPenalty - satFatPenalty - sodiumPenalty;
  return Math.max(0, Math.min(100, raw));
}

// ============================================
// Final score + grade
// ============================================

/** Map a 0-100 score to an A-E letter. */
export function numericToGrade(n: number): Grade {
  if (n >= GRADE_THRESHOLDS.A) return "A";
  if (n >= GRADE_THRESHOLDS.B) return "B";
  if (n >= GRADE_THRESHOLDS.C) return "C";
  if (n >= GRADE_THRESHOLDS.D) return "D";
  return "E";
}

/** Compute the overall NutriDécrypte grade from scoring inputs. */
export function computeOverallGrade(input: ScoringInput): ScoringResult {
  const breakdown: ScoringBreakdown = {
    nutriScore: computeNutriScoreComponent(input.nutriScore),
    nova: computeNovaComponent(input.nova),
    additives: computeAdditiveRisk(input.additives),
    claims: auditClaims(input.claims),
    density: computeNutritionalDensity(input.nutrition),
  };

  const score =
    breakdown.nutriScore * WEIGHTS.nutriScore +
    breakdown.nova * WEIGHTS.nova +
    breakdown.additives * WEIGHTS.additives +
    breakdown.claims * WEIGHTS.claims +
    breakdown.density * WEIGHTS.density;

  const rounded = Math.round(score * 10) / 10;
  return {
    score: rounded,
    grade: numericToGrade(rounded),
    breakdown,
  };
}

/** Sort an array of items with a numeric `score` descending. */
export function sortByGrade<T extends { score: number }>(items: T[]): T[] {
  return [...items].sort((a, b) => b.score - a.score);
}

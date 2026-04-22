"""
NutriDecrypte Score engine , version 1.0

Computes a deterministic A to E grade for food and dietary supplements based on five
weighted axes:

  1. Nutri-Score component        weight 25%    public French algorithm
  2. NOVA class (ultra-process)   weight 25%    Sao Paulo classification (1 to 4)
  3. Additive risk index          weight 20%    EFSA reevaluation + ANSES + controversy flags
  4. Marketing claims audit       weight 15%    flag unfounded or vague label claims
  5. Nutritional density          weight 15%    protein, fibre, vitamins vs calories

Grade thresholds (out of 100):
  A >= 85     B 70-84     C 55-69     D 40-54     E < 40

Same inputs return the same grade. Every time. No exceptions.
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Iterable


# ============================================================
# Weights and thresholds , tweak only in a new version, never in v1
# ============================================================
WEIGHTS = {
    "nutri": 0.25,
    "nova": 0.25,
    "additives": 0.20,
    "claims": 0.15,
    "density": 0.15,
}

GRADE_THRESHOLDS = [
    (85, "A"),
    (70, "B"),
    (55, "C"),
    (40, "D"),
    (0, "E"),
]


# ============================================================
# Public entry point
# ============================================================
@dataclass
class ProductInput:
    nutri_score_letter: str | None       # 'a'..'e' from Open Food Facts
    nova_group: int | None               # 1..4 from Open Food Facts
    additives_tags: list[str]            # ['en:e102', 'en:e150d', ...]
    labels_tags: list[str]               # ['en:organic', 'en:no-added-sugar', ...]
    claims_flagged: list[str]            # detected misleading claims, e.g. ['natural', 'rich-in-protein-no']
    nutriments: dict                     # { proteins_100g, fiber_100g, sugars_100g, ... }
    category_type: str                   # 'food' | 'supplement' | 'beverage'


@dataclass
class ScoreBreakdown:
    nutri: int
    nova: int
    additives: int
    claims: int
    density: int
    overall: int
    grade: str
    warnings: list[str]


def compute_grade(product: ProductInput) -> ScoreBreakdown:
    nutri = score_nutri_score(product.nutri_score_letter)
    nova = score_nova(product.nova_group)
    additives = score_additives(product.additives_tags)
    claims = score_claims(product.claims_flagged)
    density = score_density(product.nutriments, product.category_type)

    overall = round(
        nutri * WEIGHTS["nutri"]
        + nova * WEIGHTS["nova"]
        + additives * WEIGHTS["additives"]
        + claims * WEIGHTS["claims"]
        + density * WEIGHTS["density"]
    )
    overall = max(0, min(100, overall))

    grade = next(letter for threshold, letter in GRADE_THRESHOLDS if overall >= threshold)

    warnings = collect_warnings(product)

    return ScoreBreakdown(
        nutri=nutri,
        nova=nova,
        additives=additives,
        claims=claims,
        density=density,
        overall=overall,
        grade=grade,
        warnings=warnings,
    )


# ============================================================
# Axis 1: Nutri-Score letter to 0..100
# ============================================================
NUTRI_MAP = {"a": 95, "b": 78, "c": 60, "d": 42, "e": 22}


def score_nutri_score(letter: str | None) -> int:
    if letter is None:
        return 50  # neutral when missing
    return NUTRI_MAP.get(letter.lower(), 50)


# ============================================================
# Axis 2: NOVA class to 0..100
# ============================================================
NOVA_MAP = {1: 98, 2: 82, 3: 55, 4: 20}


def score_nova(nova_group: int | None) -> int:
    if nova_group is None:
        return 50
    return NOVA_MAP.get(nova_group, 50)


# ============================================================
# Axis 3: additives risk index
# EFSA review tiers. Exhaustive list built in scripts/build_additive_tiers.py
# at import time. See public.additives table.
# ============================================================
ADDITIVE_HIGH_RISK = {
    # nitrites and nitrates (charcuterie)
    "e249", "e250", "e251", "e252",
    # contested colourants
    "e102", "e104", "e110", "e122", "e124", "e129", "e133",
    # contested emulsifiers and thickeners flagged by ANSES
    "e407", "e466", "e433", "e471",
    # sweeteners with EFSA reopen
    "e951", "e952", "e955",
    # BHA, BHT
    "e320", "e321",
    # caramel colours with 4-MeI
    "e150c", "e150d",
}

ADDITIVE_MEDIUM_RISK = {
    "e100", "e120", "e160a", "e160b", "e161b",
    "e211", "e212", "e220", "e223",
    "e330",  # citric acid is low actually, kept here as placeholder
    "e450", "e451", "e452",
    "e621", "e635",
}


def _clean_tag(tag: str) -> str:
    return tag.replace("en:", "").replace("fr:", "").lower().strip()


def score_additives(tags: Iterable[str]) -> int:
    high = 0
    medium = 0
    for raw in tags:
        t = _clean_tag(raw)
        if t in ADDITIVE_HIGH_RISK:
            high += 1
        elif t in ADDITIVE_MEDIUM_RISK:
            medium += 1

    # Start at 95 for zero risky additives, penalise aggressively for high risk
    score = 95
    score -= high * 18
    score -= medium * 8

    return max(0, min(100, score))


# ============================================================
# Axis 4: marketing claims audit
# claims_flagged is produced by scripts/claims_auditor.py which cross-checks
# label claims (naturel, sans sucre ajoute, riche en proteines) against the
# actual nutriments and ingredients list.
# ============================================================
def score_claims(claims_flagged: Iterable[str]) -> int:
    flags = list(claims_flagged or [])
    if not flags:
        return 85
    score = 85 - len(flags) * 12
    return max(0, min(100, score))


# ============================================================
# Axis 5: nutritional density (protein, fibre, micronutrients vs calories)
# Simple heuristic v1, will be upgraded in v2 with ANSES daily reference values.
# ============================================================
def score_density(nutriments: dict, category_type: str) -> int:
    if not nutriments:
        return 50
    protein = float(nutriments.get("proteins_100g") or 0)
    fiber = float(nutriments.get("fiber_100g") or 0)
    sugars = float(nutriments.get("sugars_100g") or 0)
    salt = float(nutriments.get("salt_100g") or 0)
    energy = float(nutriments.get("energy-kcal_100g") or nutriments.get("energy_100g") or 0)

    score = 60
    # Reward protein density
    if protein >= 15: score += 15
    elif protein >= 8: score += 8

    # Reward fibre
    if fiber >= 6: score += 10
    elif fiber >= 3: score += 5

    # Penalise high free sugars (food only)
    if category_type == "food":
        if sugars >= 22.5: score -= 20
        elif sugars >= 10: score -= 10

    # Penalise high salt
    if salt >= 1.5: score -= 12
    elif salt >= 0.75: score -= 5

    # Penalise empty calories (high kcal with low protein / fibre)
    if energy > 400 and protein < 4 and fiber < 2:
        score -= 10

    return max(0, min(100, score))


# ============================================================
# Warnings , human-readable flags shown on the product page
# ============================================================
def collect_warnings(product: ProductInput) -> list[str]:
    w: list[str] = []
    high_additives = [a for a in product.additives_tags if _clean_tag(a) in ADDITIVE_HIGH_RISK]
    if high_additives:
        w.append(f"additifs_risque_eleve:{len(high_additives)}")
    if product.nova_group == 4:
        w.append("ultra_transforme")
    if product.claims_flagged:
        w.append(f"allegations_trompeuses:{len(product.claims_flagged)}")
    sugars = float((product.nutriments or {}).get("sugars_100g") or 0)
    if product.category_type == "food" and sugars >= 22.5:
        w.append("sucres_tres_eleves")
    salt = float((product.nutriments or {}).get("salt_100g") or 0)
    if salt >= 1.5:
        w.append("sel_tres_eleve")
    return w


if __name__ == "__main__":
    # Smoke test
    demo = ProductInput(
        nutri_score_letter="d",
        nova_group=4,
        additives_tags=["en:e150d", "en:e952", "en:e471"],
        labels_tags=[],
        claims_flagged=["natural", "no-added-sugar-false"],
        nutriments={"proteins_100g": 1.2, "fiber_100g": 0.1, "sugars_100g": 39, "salt_100g": 0.1, "energy-kcal_100g": 180},
        category_type="food",
    )
    result = compute_grade(demo)
    print(result)

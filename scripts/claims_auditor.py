"""
claims_auditor.py , detect misleading nutrition and health claims on food packaging.

Inputs :
    - product dict (Open Food Facts format)

Output :
    - list of claim flags, e.g. ['natural', 'no-added-sugar-violation', 'rich-in-protein-false']

Reference :
    - EU Regulation 1924/2006 (nutrition and health claims)
    - ANSES 2024 opinion on front-of-pack claims
"""
from __future__ import annotations
import re
from typing import Iterable


# =======================================================
# Rule set, each rule returns a flag string when matched
# =======================================================

def _lower_join(*fields: str | list | None) -> str:
    parts: list[str] = []
    for f in fields:
        if f is None:
            continue
        if isinstance(f, list):
            parts.extend(str(x) for x in f)
        else:
            parts.append(str(f))
    return " ".join(parts).lower()


# Regulation 1924/2006 thresholds for mandatory nutrition claims
# https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=celex%3A32006R1924
CLAIMS = {
    "low_fat": {"max": 3.0, "unit": "g/100g"},         # food
    "low_fat_liquid": {"max": 1.5, "unit": "g/100ml"}, # liquid
    "low_sugar": {"max": 5.0, "unit": "g/100g"},
    "low_sugar_liquid": {"max": 2.5, "unit": "g/100ml"},
    "sugar_free": {"max": 0.5},
    "no_added_sugar_threshold": {"max": 0.5},  # indicative
    "low_salt": {"max": 0.3, "unit": "g/100g"},
    "low_salt_liquid": {"max": 0.3, "unit": "g/100ml"},
    "salt_free": {"max": 0.0125},
    "source_of_fibre": {"min": 3.0},
    "high_in_fibre": {"min": 6.0},
    "source_of_protein": {"pct_of_energy_min": 12},
    "high_in_protein": {"pct_of_energy_min": 20},
    "source_of_vitamin": {"pct_of_nrv_min": 15},
    "high_in_vitamin": {"pct_of_nrv_min": 30},
}


def _num(nutri: dict, key: str) -> float:
    try:
        return float(nutri.get(key) or 0)
    except (TypeError, ValueError):
        return 0.0


def audit_claims(product: dict) -> list[str]:
    """Return list of claim flags found on this product."""
    labels = _lower_join(product.get("labels_tags"), product.get("labels"))
    front = _lower_join(product.get("product_name"), product.get("generic_name"),
                        product.get("product_name_fr"), product.get("product_name_en"))
    all_text = labels + " " + front

    nutri = product.get("nutriments") or {}
    ingr = (product.get("ingredients_text") or product.get("ingredients_text_fr") or "").lower()
    flags: list[str] = []

    # --- "natural" claim abuse ---
    if any(k in all_text for k in ["natural", "naturel", "naturelle", "100% natural", "100% naturel"]):
        # Red flag when the ingredients list contains clear industrial additives
        if re.search(r"e\d{3}", ingr) or any(x in ingr for x in [
            "maltodextr", "amidon modif", "arome de synt", "dextrose",
            "huile de palme", "sirop de glucose", "fructose", "colorant"
        ]):
            flags.append("natural_claim_violation")

    # --- "no added sugar" claim abuse ---
    no_added_sugar = any(k in all_text for k in [
        "no added sugar", "sans sucre ajoute", "sans sucres ajoutes",
        "no-added-sugar", "no-added-sugars"
    ])
    if no_added_sugar:
        # Violation if any of these sugar ingredients are listed
        sugar_aliases = [
            "sucre", "sucre de canne", "sucre roux", "sucre inverti",
            "sirop de glucose", "sirop de fructose", "sirop d'agave",
            "sirop d'erable", "sirop de riz", "dextrose", "maltose",
            "fructose", "glucose", "lactose ajoute", "jus de raisin concentre",
            "jus de pomme concentre", "concentre de jus",
            "miel",
            "high fructose corn syrup", "corn syrup", "cane sugar", "brown sugar"
        ]
        if any(a in ingr for a in sugar_aliases):
            flags.append("no_added_sugar_violation")

    # --- "sugar free" ---
    if any(k in all_text for k in ["sugar free", "sans sucre", "zero sugar", "zero sucre"]):
        if _num(nutri, "sugars_100g") > 0.5:
            flags.append("sugar_free_violation")

    # --- "rich in protein" or "high in protein" ---
    if any(k in all_text for k in ["high in protein", "riche en proteines", "high-protein", "rich in protein", "riche en protein"]):
        proteins = _num(nutri, "proteins_100g")
        energy_kcal = _num(nutri, "energy-kcal_100g") or (_num(nutri, "energy_100g") / 4.184 if nutri.get("energy_100g") else 0)
        if energy_kcal > 0:
            pct_energy = (proteins * 4 / energy_kcal) * 100
            if pct_energy < 20:
                flags.append("high_protein_claim_violation")
        elif proteins < 10:
            flags.append("high_protein_claim_violation")

    # --- "source of protein" threshold ---
    if any(k in all_text for k in ["source of protein", "source de proteines"]):
        proteins = _num(nutri, "proteins_100g")
        energy_kcal = _num(nutri, "energy-kcal_100g") or (_num(nutri, "energy_100g") / 4.184 if nutri.get("energy_100g") else 0)
        if energy_kcal > 0:
            pct_energy = (proteins * 4 / energy_kcal) * 100
            if pct_energy < 12:
                flags.append("source_of_protein_violation")

    # --- "source of fibre" ---
    if any(k in all_text for k in ["source of fibre", "source de fibres", "source of fiber"]):
        if _num(nutri, "fiber_100g") < 3.0:
            flags.append("source_of_fibre_violation")

    # --- "rich in fibre" ---
    if any(k in all_text for k in ["high in fibre", "riche en fibres", "high fibre", "rich in fibre", "rich in fiber"]):
        if _num(nutri, "fiber_100g") < 6.0:
            flags.append("high_fibre_claim_violation")

    # --- "light" or "allege" without 30% reduction ---
    if any(k in all_text for k in ["light", "allege", "allege en", "reduced"]):
        # Requires comparison to reference, flag as needs_manual_check for now
        flags.append("light_claim_unchecked")

    # --- "artisanal" / "fait maison" on clearly industrial products ---
    if any(k in all_text for k in ["artisanal", "fait maison", "homemade", "traditional", "traditionnel"]):
        additives = product.get("additives_tags") or []
        if len(additives) >= 3:
            flags.append("artisanal_claim_violation")

    # --- "sans conservateur" but preservatives present ---
    if any(k in all_text for k in ["sans conservateur", "no preservatives", "preservative free"]):
        additives = product.get("additives_tags") or []
        preservative_codes = ["e200", "e201", "e202", "e203", "e210", "e211", "e212", "e213",
                              "e214", "e215", "e216", "e217", "e218", "e219", "e220", "e221",
                              "e222", "e223", "e224", "e226", "e227", "e228", "e230", "e231",
                              "e232", "e233", "e234", "e235", "e239", "e242", "e249", "e250",
                              "e251", "e252"]
        for a in additives:
            cleaned = a.replace("en:", "").replace("fr:", "").lower().strip()
            if cleaned in preservative_codes:
                flags.append("no_preservatives_violation")
                break

    # --- "riche en oméga 3" without EPA+DHA breakdown ---
    if any(k in all_text for k in ["riche en omega", "rich in omega", "omega-3"]):
        # ANSES: requires >= 40 mg EPA+DHA per 100g or 100kcal
        # Without the data, flag as unchecked
        if not any(k in ingr for k in ["epa", "dha", "huile de poisson", "fish oil"]):
            flags.append("omega3_claim_unverified")

    return flags


if __name__ == "__main__":
    # Smoke test
    demo = {
        "labels_tags": ["en:natural", "en:no-added-sugar"],
        "product_name": "Natural Fruit Bar",
        "ingredients_text": "dattes, sirop de glucose, arome naturel, e150d, dextrose",
        "nutriments": {"sugars_100g": 45.0, "proteins_100g": 3.0, "energy-kcal_100g": 340},
        "additives_tags": ["en:e150d"],
    }
    print("FLAGS:", audit_claims(demo))

    demo2 = {
        "labels_tags": ["en:high-in-protein"],
        "product_name": "Protein Bar",
        "ingredients_text": "whey, cocoa",
        "nutriments": {"proteins_100g": 6.0, "energy-kcal_100g": 420},
        "additives_tags": [],
    }
    print("FLAGS2:", audit_claims(demo2))

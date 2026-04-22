"""
build_additive_tiers.py , rebuild HIGH_RISK / MEDIUM_RISK additive sets
from the Supabase public.additives table, so scoring_engine stays in
sync with editorial updates to the additives dictionary.

Run whenever public.additives is edited.

Writes to scripts/additive_tiers.generated.json, which scoring_engine loads
at import time if present (overrides the built-in defaults).
"""
from __future__ import annotations
import json
import os
import sys
import urllib.request
from pathlib import Path

SUPABASE_URL = os.environ.get("SUPABASE_URL", "").rstrip("/")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_KEY") or os.environ.get("SUPABASE_ANON_KEY", "")


def fetch_additives() -> list[dict]:
    url = f"{SUPABASE_URL}/rest/v1/additives?select=e_number,risk_level&order=e_number"
    req = urllib.request.Request(url, headers={
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Accept": "application/json",
        "User-Agent": "nutridecrypte-build-tiers/0.1",
    })
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read())


def main():
    if not SUPABASE_URL or not SUPABASE_KEY:
        print("FATAL: SUPABASE_URL + SUPABASE_SERVICE_KEY required", file=sys.stderr)
        sys.exit(1)

    rows = fetch_additives()
    high = sorted({r["e_number"].lower() for r in rows if r.get("risk_level") == "high"})
    medium = sorted({r["e_number"].lower() for r in rows if r.get("risk_level") == "medium"})
    low = sorted({r["e_number"].lower() for r in rows if r.get("risk_level") == "low"})

    out = {
        "generated_at": __import__("datetime").datetime.utcnow().isoformat() + "Z",
        "high_risk": high,
        "medium_risk": medium,
        "low_risk": low,
    }
    out_path = Path(__file__).parent / "additive_tiers.generated.json"
    out_path.write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"OK: wrote {out_path}")
    print(f"  high_risk: {len(high)}")
    print(f"  medium_risk: {len(medium)}")
    print(f"  low_risk: {len(low)}")


if __name__ == "__main__":
    main()

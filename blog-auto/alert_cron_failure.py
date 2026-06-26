#!/usr/bin/env python3
"""
Envoie un email via Resend quand un workflow GitHub Actions fail.

Utilise comme dernier step (if: failure()) dans les workflows :
    - name: Alert on failure
      if: failure()
      env:
        RESEND_API_KEY: ${{ secrets.RESEND_API_KEY }}
      run: python3 blog-auto/alert_cron_failure.py "${{ github.workflow }}" "${{ github.run_id }}"

FROM = onboarding@resend.dev (sender universel Resend, pas besoin de domaine verifie
sur le plan 1-domaine). Ne casse JAMAIS le workflow (return 0 sur toute erreur).
"""
from __future__ import annotations
import os
import sys
import json
import urllib.request
import urllib.error

RESEND_URL = "https://api.resend.com/emails"
FROM_EMAIL = "onboarding@resend.dev"
TO_EMAIL = "augustin.foucheres@gmail.com"
REPO = "STACK-2026/nutridecrypte"


def main() -> int:
    api_key = os.getenv("RESEND_API_KEY", "")
    if not api_key:
        print("RESEND_API_KEY missing, skipping alert", file=sys.stderr)
        return 0

    workflow = sys.argv[1] if len(sys.argv) > 1 else "unknown"
    run_id = sys.argv[2] if len(sys.argv) > 2 else "unknown"
    run_url = f"https://github.com/{REPO}/actions/runs/{run_id}"

    subject = f"[nutridecrypte] Deploy FAIL : {workflow}"
    body_html = f"""<html><body style="font-family:system-ui,sans-serif;max-width:600px">
<h2>Workflow GitHub Actions KO</h2>
<p><strong>Workflow :</strong> {workflow}</p>
<p><strong>Run ID :</strong> {run_id}</p>
<p><a href="{run_url}" style="background:#000;color:#fff;padding:10px 20px;border-radius:6px;text-decoration:none">Voir le run</a></p>
<hr>
<p>Cause probable : contenu non conforme au schema (category hors enum, source url:"", champ requis manquant) ou content guard. Voir le log du step "Build Astro site".</p>
</body></html>"""

    payload = json.dumps({
        "from": FROM_EMAIL,
        "to": [TO_EMAIL],
        "subject": subject,
        "html": body_html,
    }).encode("utf-8")

    req = urllib.request.Request(
        RESEND_URL,
        data=payload,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "User-Agent": "NutridecrypteAlerts/1.0",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            print(f"Alert sent: {r.status} {r.read().decode('utf-8')[:200]}")
            return 0
    except urllib.error.HTTPError as e:
        print(f"Alert HTTP error {e.code}: {e.read().decode('utf-8')[:200]}", file=sys.stderr)
        return 0
    except Exception as e:
        print(f"Alert error: {e}", file=sys.stderr)
        return 0


if __name__ == "__main__":
    sys.exit(main())

# nutridecrypte.com — STACK-2026

## Contexte
Média indépendant de décodage de l'alimentation **humaine** (basé Open Food Facts) :
additifs, ultra-transformés, étiquettes, allégations, compléments. Astro SSG + Cloudflare
Pages. ~1 470 pages produits notées, 23 articles, ~2 550 pages. Bilingue (FR + EN).

## Quick refs — lire AVANT toute modif
- **Domaine live** : https://nutridecrypte.com
- **CF Pages project** : `nutridecrypte`
- **Repo** : https://github.com/STACK-2026/nutridecrypte
- **Données produits (BUILD-TIME)** : **VPS Postgres `db_nutridecrypte`** (Tier-2 STACK-2026), via `src/lib/db.ts` / `data.ts` (`DATABASE_URL`, tunnel CF). Pas de Supabase runtime produits.
- **i18n** : `defaultLocale: "en"` → racine = EN, **FR sous `/fr/`**. Articles FR : `lang: fr`.
- **IndexNow key** : `site/public/*.txt` (clé partagée portfolio `584654e3...`).
- **Règle contenu** : **0 tiret cadratin (— ni –)**, accents FR obligatoires.
- **Auteurs** : Thomas Moreau, Camille Roux (rédaction) ; Sarah Keller (diététicienne-nutritionniste) + Lucie Bernard (responsable éditoriale) en relecture.

## Blog (format premium — ajouté 01/06/2026)
- `src/layouts/BlogLayout.astro` : Article + Breadcrumb JSON-LD, **+ FAQPage + Speakable** quand frontmatter `faq` (array `{q,a}`) / `tldr` présents → encart TL;DR + accordéon FAQ visibles.
- Routes : FR `/fr/blog/<slug>/`, EN `/blog/<slug>/`. `AmazonPicks` injecté en fin d'article.
- ⚠️ **Ne jamais linker un article daté dans le futur** (`date > today`) : exclu du build (`date<=now`) → lien cassé.
- Articles rédigés via **Gemini 2.5 Pro** (`GEMINI_API_KEY`, `maxOutputTokens≥12000`), faits vérifiés à la main, sources EFSA/ANSES/OMS inline.

## Affiliation
- **Amazon** via `AmazonPicks.astro` + fonction `functions/go/[product].js` (redirection trackée). Affiliate.ts présent. Pas de système multi-marchand Awin (contrairement à petfoodrate).

## Déploiement (T2 — IMPÉRATIF)
- **Build LOCAL tunnelé** (vraies données VPS) :
  ```
  /tmp/cloudflared access tcp --hostname pg.augustinfoucheres.com --url 127.0.0.1:5432 \
    --service-token-id $VPS_PG_CF_ACCESS_CLIENT_ID --service-token-secret $VPS_PG_CF_ACCESS_CLIENT_SECRET &
  DATABASE_URL=$VPS_PG_NUTRIDECRYPTE_URL npm run build   # dans site/
  ```
- **Deploy** = `npx wrangler@4 pages deploy dist --project-name=nutridecrypte --branch=main` (creds `.env.master`).
- ⚠️ **`deploy-site.yml` = `disabled_manually`** (rebuild CI sans DB dégrade). Push `main` sûr, ne déploie pas. Après deploy : IndexNow + vérif live.
- Au build, les routes `/fr/<x>` dupliquées affichent "(file not created, response body was empty)" = dédup i18n normal, bénin.

## Gotchas
- `.stagger-children` (animations.css) : catch-all `.in-view > *` présent (corrigé 01/06) — sinon listes >10 rendent blanc.
- Sibling de petfoodrate / bebedecrypte (même template STACK-2026). Voir `petfoodrate/CLAUDE.md` pour le détail du pipeline data si besoin de portage.

## Mémoire (claude-mem)
- `project-petfoodrate-blog-reveal-and-brand-ranking-fix.md` — section finale documente le portage du format blog nutridecrypte + comparatif des 3 sites frères.

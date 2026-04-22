# NutriDécrypte

> On décrypte ce que les étiquettes cachent.

Independent European nutrition decoder. Grades food and dietary supplements from A to E using Open Food Facts, the Nutri-Score, the NOVA classification, and the EFSA additives registry.

## Stack

- Astro 6 static site generator
- Cloudflare Pages hosting
- Supabase (project `zrgchcrhufdbreykipkj`, region `eu-west-2`) for analytics and newsletter
- Resend (`send.nutridecrypte.com`) for transactional email
- GitHub Actions for CI/CD and blog-auto scheduling

## Monorepo layout

- `site/` , Astro static site (EN default + FR at `/fr/`)
- `scripts/` , data pipeline: Open Food Facts ingestion, EFSA additive database, NutriDécrypte Score engine
- `blog-auto/` , Mistral + Claude-audit editorial pipeline with Gemini SERP briefs
- `pending/` , raw scraped data before ingestion

## Live

- Production: https://nutridecrypte.com
- Preview: https://nutridecrypte.pages.dev

## Development

```bash
cd site
npm install
npm run dev
```

## Deploy

Pushes to `main` trigger GitHub Actions workflow `deploy-site.yml` (wrangler-action@v3, Cloudflare Pages direct upload).

## Data sources

- Open Food Facts (CC-BY-SA, 3M+ products)
- EFSA additive reevaluation registry
- NOVA classification (University of Sao Paulo)
- ANSES scientific opinions
- Nutri-Score algorithm (Sante publique France)

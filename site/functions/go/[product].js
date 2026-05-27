// Affiliate click redirect for /go/<slug>?to=<encoded-amazon-url>.
//
// NutriDecrypte is Amazon-only (Phase 3, 2026-05-27). AmazonPicks pre-builds
// the full amazon.fr URL at build time and passes it via ?to=. This function
// strictly validates the destination, logs the click in Supabase
// affiliate_clicks, then 302s.
//
// File is named [product].js for legacy compatibility with the existing CF
// route. The route param is exposed as params.product but semantically holds
// the page slug (e.g. "fr-blog-magnesium-complement-meilleur-2026").
//
// Env vars (CF Pages → Settings → Environment variables):
//   SUPABASE_URL  → nutridecrypte project URL
//   SUPABASE_ANON → anon JWT (INSERT on affiliate_clicks)
//   AMAZON_TAG    → "nutridecrypte-21"

const BOT_UA_REGEX =
  /bot|crawl|spider|slurp|facebookexternalhit|linkedinbot|twitterbot|whatsapp|telegram|googlebot|bingbot|yandexbot|baiduspider|duckduckbot|gptbot|claudebot|perplexitybot|amazonbot|applebot|ccbot|bytespider|headlesschrome|preview|fetch|http-client|libwww|wget|curl\/|axios|node-fetch|python-requests|python-urllib|go-http-client|java\/|okhttp|ruby|guzzlehttp|httpclient|httpx|requests\/|vercel|netlify|cloudflare-workers|pingdom|uptime|monitor|cron|scraper|scrapy|phantomjs|puppeteer|playwright|jsdom|nutch|semrushbot|ahrefsbot|mj12bot|dotbot|petalbot|seznambot|datatools/i;

function isSyntheticUA(ua) {
  if (!ua) return true;
  if (/iphone|ipad|ipod/i.test(ua) && !/applewebkit\/60[5-9]/i.test(ua)) return true;
  if (/build\/opd3\.170816/i.test(ua)) return true;
  if (/sm-s901[a-z]\b/i.test(ua) && /android\s?(8|9|10|11)(\.|;|\))/i.test(ua)) return true;
  return false;
}

function sanitizeSlug(raw) {
  if (!raw || typeof raw !== "string") return null;
  const m = raw.toLowerCase().match(/^[a-z0-9][a-z0-9-]{0,119}$/);
  return m ? m[0] : null;
}

function validateAmazonUrl(raw, expectedTag) {
  if (!raw || typeof raw !== "string" || raw.length > 2048) return null;
  let u;
  try { u = new URL(raw); } catch { return null; }
  if (u.protocol !== "https:") return null;
  if (u.hostname !== "www.amazon.fr") return null;
  if (u.searchParams.get("tag") !== expectedTag) return null;
  return u.toString();
}

async function sha1Hex(input) {
  const buf = new TextEncoder().encode(input);
  const hash = await crypto.subtle.digest("SHA-1", buf);
  return Array.from(new Uint8Array(hash))
    .map((b) => b.toString(16).padStart(2, "0"))
    .join("");
}

async function logClick(env, payload, waitUntil) {
  if (!env.SUPABASE_URL || !env.SUPABASE_ANON) return;
  const promise = fetch(`${env.SUPABASE_URL}/rest/v1/affiliate_clicks`, {
    method: "POST",
    headers: {
      apikey: env.SUPABASE_ANON,
      Authorization: `Bearer ${env.SUPABASE_ANON}`,
      "Content-Type": "application/json",
      Prefer: "return=minimal",
    },
    body: JSON.stringify(payload),
  }).catch(() => {});
  if (waitUntil) waitUntil(promise);
  else await promise;
}

export async function onRequestGet(context) {
  const { request, env, params, waitUntil } = context;

  if (!env.AMAZON_TAG) {
    return new Response("Affiliate tag not configured", { status: 404 });
  }

  const slug = sanitizeSlug(params.product);
  if (!slug) return new Response("Bad slug", { status: 400 });

  const url = new URL(request.url);
  const destination = validateAmazonUrl(url.searchParams.get("to"), env.AMAZON_TAG);
  if (!destination) {
    return new Response("Invalid destination", { status: 422 });
  }

  const ua = request.headers.get("user-agent") || "";
  const rawReferer = request.headers.get("referer") || "";
  const country = request.headers.get("cf-ipcountry") || "";
  const isBot = BOT_UA_REGEX.test(ua) || isSyntheticUA(ua);

  let referer = "";
  if (rawReferer) {
    try {
      const r = new URL(rawReferer);
      referer = `${r.origin}${r.pathname}`;
    } catch {}
  }
  const uaHash = ua ? (await sha1Hex(ua)).slice(0, 16) : null;

  await logClick(
    env,
    {
      slug,
      merchant: "amazon",
      destination_url: destination,
      referrer: referer || null,
      country: country || null,
      ua_hash: uaHash,
      is_bot: isBot,
    },
    waitUntil
  );

  return new Response(null, {
    status: 302,
    headers: {
      Location: destination,
      "Cache-Control": "no-store, private",
    },
  });
}

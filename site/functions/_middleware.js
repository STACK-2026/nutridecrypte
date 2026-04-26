// Cloudflare Pages middleware — does two things:
//   1. Auto-redirect FR users from "/" to "/fr/" based on Accept-Language (existing).
//   2. Server-side bot crawl logger : each HTML GET from a bot UA is logged to
//      Supabase page_views with is_bot=true (new, captures GPTBot/ClaudeBot/etc.
//      which the consent-gated client JS beacon misses by design).
//
// Humans are tracked via the consent-gated client JS, not through this middleware
// (CNIL: no server-side identification of identifiable users).

const BOT_RE = /bot|crawl|spider|slurp|lighthouse|headless|curl|wget|python|httpx|scrap|fetch|monitor|preview|vercel|facebookexternalhit|whatsapp|telegram|skypeuripreview|linkedinbot|twitterbot|duckduckbot|yandex|semrush|ahrefs|mj12bot|dotbot|petalbot|seznambot|applebot|ccbot|claudebot|gptbot|google-extended|perplexitybot|youbot|amazonbot|bytespider|duckassistbot|chatgpt-user|oai-searchbot|anthropic|cohere|diffbot|archive|uptime|pingdom|gtmetrix|Nexus 5X Build\/MMB29P/i;

const ASSET_EXT = /\.(js|mjs|css|png|jpe?g|webp|avif|gif|svg|ico|woff2?|ttf|otf|eot|map|json|xml|txt|mp4|webm|mp3|pdf|zip)$/i;

export async function onRequest(context) {
  const { request, next, env, waitUntil } = context;
  const url = new URL(request.url);

  // ---- FR auto-redirect on root path "/" ----
  if (url.pathname === "/" || url.pathname === "") {
    const acceptLanguage = request.headers.get("Accept-Language") || "";
    const languages = acceptLanguage
      .split(",")
      .map((lang) => {
        const [code, q] = lang.trim().split(";q=");
        return { code: code.trim().toLowerCase(), q: q ? parseFloat(q) : 1.0 };
      })
      .sort((a, b) => b.q - a.q);
    const primaryLang = languages[0]?.code || "en";
    if (primaryLang.startsWith("fr")) {
      return Response.redirect(`${url.origin}/fr/`, 302);
    }
  }

  const response = await next();

  // ---- Server-side bot crawl logger ----
  try {
    if (request.method !== "GET") return response;

    const path = url.pathname;
    if (ASSET_EXT.test(path)) return response;
    if (path.startsWith("/api/")) return response;
    if (path.startsWith("/_astro/") || path.startsWith("/_worker")) return response;

    const ua = request.headers.get("user-agent") || "";
    if (!ua || !BOT_RE.test(ua)) return response;

    const contentType = response.headers.get("content-type") || "";
    if (!contentType.includes("text/html")) return response;

    if (!env.SUPABASE_URL || !env.SUPABASE_SERVICE_KEY) return response;

    const payload = {
      path: path.slice(0, 500),
      referrer: (request.headers.get("referer") || "").slice(0, 500) || null,
      user_agent: ua.slice(0, 500),
      is_bot: true,
      country: request.headers.get("cf-ipcountry") || null,
      city: request.headers.get("cf-ipcity") || null,
    };

    waitUntil(
      fetch(`${env.SUPABASE_URL}/rest/v1/page_views`, {
        method: "POST",
        headers: {
          apikey: env.SUPABASE_SERVICE_KEY,
          Authorization: `Bearer ${env.SUPABASE_SERVICE_KEY}`,
          "Content-Type": "application/json",
          Prefer: "return=minimal",
        },
        body: JSON.stringify(payload),
      }).catch(() => {}),
    );
  } catch {
    // silent: never break the page render
  }

  return response;
}

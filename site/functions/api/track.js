// CF Pages Function : POST /api/track
// First-party analytics endpoint. Logs to Supabase page_views with SERVICE_KEY
// (server-side, bypasses RLS). UA-based bot detection.

const BOT_RE = /bot|crawl|spider|slurp|lighthouse|headless|curl|wget|python|httpx|scrap|fetch|monitor|preview|vercel|facebookexternalhit|whatsapp|telegram|skypeuripreview|linkedinbot|twitterbot|duckduckbot|yandex|semrushbot|ahrefsbot|mj12bot|petalbot|seznambot|applebot|ccbot|claudebot|gptbot|google-extended|perplexitybot|youbot|amazonbot|bytespider|duckassistbot|chatgpt-user|oai-searchbot|anthropic|cohere|diffbot|archive|uptime|pingdom|gtmetrix|Nexus 5X Build\/MMB29P/i;

export async function onRequestPost({ request, env }) {
  try {
    if (!env.SUPABASE_URL || !env.SUPABASE_SERVICE_KEY) {
      return new Response(JSON.stringify({ ok: true, skipped: "no-supabase" }), { status: 200 });
    }

    const body = await request.json().catch(() => ({}));
    const ua = request.headers.get("user-agent") || "";
    const country = request.headers.get("cf-ipcountry") || null;
    const city = request.headers.get("cf-ipcity") || null;
    const isBot = BOT_RE.test(ua);

    // Build event_data jsonb with extra context (utm, title, screen, time_on_page)
    const eventData = {};
    for (const k of ["utm_source", "utm_medium", "utm_campaign", "utm_term", "utm_content", "title", "screen_width", "screen_height", "time_on_page_ms", "referrer_domain"]) {
      if (body[k] != null && body[k] !== "") eventData[k] = body[k];
    }

    const payload = {
      path: String(body.path || "/").slice(0, 500),
      referrer: body.referrer ? String(body.referrer).slice(0, 500) : null,
      user_agent: ua.slice(0, 500),
      is_bot: isBot,
      country,
      city,
      country_code: country,
      session_id: body.sessionId ? String(body.sessionId).slice(0, 60) : null,
      locale: body.locale ? String(body.locale).slice(0, 16) : null,
      event_type: body.event_type ? String(body.event_type).slice(0, 60) : "page_view",
      event_data: Object.keys(eventData).length ? eventData : null,
    };

    await fetch(`${env.SUPABASE_URL}/rest/v1/page_views`, {
      method: "POST",
      headers: {
        apikey: env.SUPABASE_SERVICE_KEY,
        Authorization: `Bearer ${env.SUPABASE_SERVICE_KEY}`,
        "Content-Type": "application/json",
        Prefer: "return=minimal",
      },
      body: JSON.stringify(payload),
    });

    return new Response(JSON.stringify({ ok: true }), {
      status: 200,
      headers: { "content-type": "application/json" },
    });
  } catch (e) {
    return new Response(JSON.stringify({ ok: false }), { status: 200 });
  }
}

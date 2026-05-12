// CF Pages Function: /api/event
// Receives client-side conversion events from /track.js.
// Renamed from /api/track to avoid collision with legacy page_views trackers.
// Uses whichever Supabase key is configured: SUPABASE_SERVICE_KEY (existing
// sites) or SUPABASE_ANON (new sites). Returns 204 silently if no key set.

const ALLOWED = new Set([
  "phone_click", "phone_reveal",
  "email_click", "email_reveal",
  "website_click",
  "cta_click",
  "form_view", "form_focus", "form_submit", "form_abandon",
  "affiliate_click",
  "scroll_depth",
]);

export async function onRequestPost({ request, env }) {
  if (!env.SUPABASE_URL || (!env.SUPABASE_SERVICE_KEY && !env.SUPABASE_ANON)) {
    return new Response(null, { status: 204 });
  }
  let body;
  try {
    const txt = await request.text();
    body = JSON.parse(txt || "{}");
  } catch {
    return new Response("bad json", { status: 400 });
  }

  const type = String(body.type || "").trim();
  if (!ALLOWED.has(type)) return new Response("bad type", { status: 400 });

  const target = body.target ? String(body.target).slice(0, 200) : null;
  const page = body.page ? String(body.page).slice(0, 500) : null;
  const sid = body.sid ? String(body.sid).slice(0, 64) : null;

  const key = env.SUPABASE_SERVICE_KEY || env.SUPABASE_ANON;
  const url = `${env.SUPABASE_URL}/rest/v1/events`;
  const r = await fetch(url, {
    method: "POST",
    headers: {
      apikey: key,
      Authorization: `Bearer ${key}`,
      "Content-Type": "application/json",
      Prefer: "return=minimal",
    },
    body: JSON.stringify({ type, target, page, session_id: sid }),
  });

  if (!r.ok) {
    return new Response("supabase error " + r.status, { status: 502 });
  }
  return new Response(null, { status: 204 });
}

export async function onRequestOptions() {
  return new Response(null, {
    status: 204,
    headers: {
      "Access-Control-Allow-Origin": "*",
      "Access-Control-Allow-Methods": "POST, OPTIONS",
      "Access-Control-Allow-Headers": "Content-Type",
    },
  });
}

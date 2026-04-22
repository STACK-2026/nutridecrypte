// Affiliate click redirect for /go/:product.
// Phase 0 stub: no affiliate merchant is active. Redirects to the home page until
// partners are signed. When a merchant is approved, wire AWIN_PUBLISHER_ID + MID,
// build the Awin deep link, and log the click to Supabase (affiliate_clicks table).
//
// IMPORTANT: robots.txt must keep /go/ Disallowed to prevent crawler follow.

function sanitizeProductId(raw) {
  if (!raw || typeof raw !== "string") return null;
  const match = raw.toLowerCase().match(/^[a-z0-9][a-z0-9-]{0,119}$/);
  return match ? match[0] : null;
}

export async function onRequestGet(context) {
  const { params, request } = context;
  const productId = sanitizeProductId(params.product);

  if (!productId) {
    return new Response("Invalid product slug", { status: 400 });
  }

  // TODO Phase 1: resolve merchant by product.country / category, build Awin deep link,
  // log click to Supabase `affiliate_clicks` with Referer + CF country.
  const origin = new URL(request.url).origin;
  return Response.redirect(`${origin}/rankings/`, 302);
}

// Cloudflare Pages middleware: auto-detect browser language and redirect FR users to /fr/
// Only applies to the root path "/" - all other paths are served as-is.
// Respects existing locale preference (if user has already navigated to /fr/ or /).

export async function onRequest(context) {
  const { request, next } = context;
  const url = new URL(request.url);

  // Only redirect on the root path "/"
  // Don't redirect if already on /fr/, or on any other page, or if it's an asset
  if (url.pathname !== "/" && url.pathname !== "") {
    return next();
  }

  // Check Accept-Language header
  const acceptLanguage = request.headers.get("Accept-Language") || "";

  // Parse primary language
  const languages = acceptLanguage
    .split(",")
    .map((lang) => {
      const [code, q] = lang.trim().split(";q=");
      return { code: code.trim().toLowerCase(), q: q ? parseFloat(q) : 1.0 };
    })
    .sort((a, b) => b.q - a.q);

  const primaryLang = languages[0]?.code || "en";

  // If French is the primary language, redirect to /fr/
  if (primaryLang.startsWith("fr")) {
    return Response.redirect(`${url.origin}/fr/`, 302);
  }

  // Otherwise, serve the English homepage (default)
  return next();
}

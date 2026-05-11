// NutriDecrypte - analytics tracker
// POSTs to /api/track (CF Pages Function) which writes to Supabase with SERVICE_KEY server-side.
// Consent gated by Analytics.astro (nd-cookie-choice === "all" required).
(function () {
  var SESSION_KEY = "nd_session_id";
  var UTM_KEY = "nd_utm";
  var lastPath = "";
  var lastSendAt = 0;
  var pendingTimeOnPage = null;

  function getSessionId() {
    try {
      var id = sessionStorage.getItem(SESSION_KEY);
      if (!id) {
        id = (Date.now().toString(36) + Math.random().toString(36).slice(2, 10)).slice(0, 60);
        sessionStorage.setItem(SESSION_KEY, id);
      }
      return id;
    } catch (e) {
      return "no-storage-" + Date.now();
    }
  }

  function extractDomain(url) {
    if (!url) return null;
    try { return new URL(url).hostname.replace(/^www\./, ""); } catch (e) { return null; }
  }

  function captureUtm() {
    try {
      var params = new URLSearchParams(location.search);
      var utm = {
        utm_source: params.get("utm_source"),
        utm_medium: params.get("utm_medium"),
        utm_campaign: params.get("utm_campaign"),
        utm_term: params.get("utm_term"),
        utm_content: params.get("utm_content"),
      };
      var has = Object.values(utm).some(function (v) { return !!v; });
      if (has && !sessionStorage.getItem(UTM_KEY)) {
        sessionStorage.setItem(UTM_KEY, JSON.stringify(utm));
      }
    } catch (e) {}
  }

  function getStoredUtm() {
    try { return JSON.parse(sessionStorage.getItem(UTM_KEY) || "{}"); } catch (e) { return {}; }
  }

  function post(body, useBeacon) {
    var payload = JSON.stringify(body);
    if (useBeacon && navigator.sendBeacon) {
      try {
        return navigator.sendBeacon("/api/track", new Blob([payload], { type: "application/json" }));
      } catch (e) {}
    }
    return fetch("/api/track", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: payload,
      keepalive: true,
    }).catch(function () {});
  }

  function trackPageView() {
    var path = location.pathname;
    if (path === lastPath) return;
    captureUtm();
    var utm = getStoredUtm();
    var referrer = document.referrer || null;
    post({
      event_type: "page_view",
      path: path,
      referrer: referrer,
      referrer_domain: extractDomain(referrer),
      sessionId: getSessionId(),
      locale: (navigator.language || "en").split("-")[0],
      title: document.title ? document.title.slice(0, 200) : null,
      screen_width: window.innerWidth,
      screen_height: window.innerHeight,
      utm_source: utm.utm_source || null,
      utm_medium: utm.utm_medium || null,
      utm_campaign: utm.utm_campaign || null,
      utm_term: utm.utm_term || null,
      utm_content: utm.utm_content || null,
    });
    lastPath = path;
    lastSendAt = Date.now();
  }

  function trackEvent(name, props) {
    post({
      event_type: name,
      path: location.pathname,
      sessionId: getSessionId(),
      title: document.title ? document.title.slice(0, 200) : null,
      // pass props as flat keys so /api/track can pick the well-known ones (utm/title/etc.)
      // and ignore unknown extras gracefully (event_data captures all extras in jsonb).
      ...((props && typeof props === "object") ? props : {}),
    });
  }

  function sendTimeOnPage() {
    if (!lastSendAt) return;
    var dt = Date.now() - lastSendAt;
    if (dt < 1500) return; // ignore bounces <1.5s
    post({
      event_type: "engagement",
      path: lastPath || location.pathname,
      sessionId: getSessionId(),
      time_on_page_ms: dt,
    }, true);
  }

  window.addEventListener("beforeunload", sendTimeOnPage);
  document.addEventListener("visibilitychange", function () {
    if (document.visibilityState === "hidden") sendTimeOnPage();
  });

  trackPageView();
  window.nd = { trackPageView: trackPageView, trackEvent: trackEvent, getSessionId: getSessionId };
})();

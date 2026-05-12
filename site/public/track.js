// STACK-2026 conversion tracker. Drop-in script: emits events to /api/event AND forwards to GA4 (window.gtag).
// No PII captured: only event type, target string, page path, session UUID.
// Auto-instruments:
//   - a[href^="tel:"]          -> phone_click
//   - a[href^="mailto:"]       -> email_click
//   - [data-cta]               -> cta_click
//   - a[href^="/go/"]          -> affiliate_click
//   - a[href^="http"] (extern) -> website_click  (outbound to other domains)
//   - [data-form-id]           -> form_view / form_focus / form_submit / form_abandon
//   - scroll                   -> scroll_depth at 25/50/75/100% (once per session)
(function () {
  if (window.__stackTrackerInit) return;
  window.__stackTrackerInit = true;

  var SID_KEY = "stack_sid";
  var SID_TTL_DAYS = 30;
  function uuid() {
    return ([1e7] + -1e3 + -4e3 + -8e3 + -1e11).replace(/[018]/g, function (c) {
      return (c ^ (crypto.getRandomValues(new Uint8Array(1))[0] & (15 >> (c / 4)))).toString(16);
    });
  }
  function sid() {
    try {
      var raw = localStorage.getItem(SID_KEY);
      if (raw) {
        var p = JSON.parse(raw);
        if (p && p.id && p.exp > Date.now()) return p.id;
      }
      var id = uuid();
      localStorage.setItem(SID_KEY, JSON.stringify({ id: id, exp: Date.now() + SID_TTL_DAYS * 86400000 }));
      return id;
    } catch (e) {
      return "ephemeral-" + Date.now();
    }
  }
  var SID = sid();
  var PAGE = location.pathname + location.search;
  var HOST = location.hostname;

  function send(type, target) {
    // 1. Custom backend: /api/event (Supabase events table)
    var payload = JSON.stringify({ type: type, target: target || null, page: PAGE, sid: SID });
    try {
      if (navigator.sendBeacon) {
        navigator.sendBeacon("/api/event", new Blob([payload], { type: "application/json" }));
      } else {
        fetch("/api/event", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: payload,
          keepalive: true,
        });
      }
    } catch (e) {
      /* swallow */
    }
    // 2. GA4 forward (only if gtag bootstrapped + consent granted in GA4Tracker)
    try {
      if (typeof window.gtag === "function") {
        window.gtag("event", type, {
          event_category: "engagement",
          event_label: target || undefined,
          page_path: PAGE,
        });
      }
    } catch (e) {
      /* swallow */
    }
  }

  // 1. Phone clicks (tel:)
  document.addEventListener("click", function (ev) {
    var a = ev.target.closest && ev.target.closest('a[href^="tel:"]');
    if (a) send("phone_click", a.getAttribute("href"));
  });

  // 2. Email clicks (mailto:)
  document.addEventListener("click", function (ev) {
    var a = ev.target.closest && ev.target.closest('a[href^="mailto:"]');
    if (a) send("email_click", a.getAttribute("href"));
  });

  // 3. CTA clicks ([data-cta])
  document.addEventListener("click", function (ev) {
    var el = ev.target.closest && ev.target.closest("[data-cta]");
    if (el) send("cta_click", el.getAttribute("data-cta"));
  });

  // 4. Affiliate outbound (/go/*)
  document.addEventListener("click", function (ev) {
    var a = ev.target.closest && ev.target.closest('a[href^="/go/"]');
    if (a) send("affiliate_click", a.getAttribute("href"));
  });

  // 5. Outbound clicks (a[href^="http"] to any non-host domain, excluding /go/ which is already affiliate)
  document.addEventListener("click", function (ev) {
    var a = ev.target.closest && ev.target.closest('a[href^="http"]');
    if (!a) return;
    var href = a.getAttribute("href") || "";
    try {
      var u = new URL(href, location.href);
      if (u.hostname && u.hostname !== HOST && !u.pathname.startsWith("/go/")) {
        send("website_click", u.hostname);
      }
    } catch (e) {
      /* swallow */
    }
  });

  // 6. Form lifecycle (each form needs data-form-id="<name>")
  var formsSeen = new Set();
  var formsFocused = new Set();
  var formsSubmitted = new Set();

  function instrumentForm(form) {
    var fid = form.getAttribute("data-form-id");
    if (!fid) return;
    if (!formsSeen.has(fid) && "IntersectionObserver" in window) {
      var io = new IntersectionObserver(function (entries) {
        entries.forEach(function (e) {
          if (e.isIntersecting && !formsSeen.has(fid)) {
            formsSeen.add(fid);
            send("form_view", fid);
            io.disconnect();
          }
        });
      }, { threshold: 0.3 });
      io.observe(form);
    }
    form.addEventListener("focusin", function () {
      if (!formsFocused.has(fid)) {
        formsFocused.add(fid);
        send("form_focus", fid);
      }
    });
    form.addEventListener("submit", function () {
      formsSubmitted.add(fid);
      send("form_submit", fid);
    });
  }
  function scanForms() {
    document.querySelectorAll("form[data-form-id]").forEach(instrumentForm);
  }
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", scanForms);
  } else {
    scanForms();
  }
  if ("MutationObserver" in window) {
    new MutationObserver(scanForms).observe(document.documentElement, { childList: true, subtree: true });
  }

  // 7. Form abandon = visibility loss after focus, before submit
  document.addEventListener("visibilitychange", function () {
    if (document.visibilityState !== "hidden") return;
    formsFocused.forEach(function (fid) {
      if (!formsSubmitted.has(fid)) send("form_abandon", fid);
    });
    formsFocused.clear();
  });

  // 8. Scroll depth (25 / 50 / 75 / 100 %), once per session per page
  var scrollMarks = [25, 50, 75, 100];
  var fired = new Set();
  function pct() {
    var doc = document.documentElement;
    var body = document.body;
    var total = Math.max(doc.scrollHeight, body.scrollHeight) - window.innerHeight;
    if (total <= 0) return 100;
    return Math.round(((window.scrollY || doc.scrollTop) / total) * 100);
  }
  var scrollTimer = null;
  window.addEventListener("scroll", function () {
    if (scrollTimer) return;
    scrollTimer = setTimeout(function () {
      scrollTimer = null;
      var p = pct();
      for (var i = 0; i < scrollMarks.length; i++) {
        var m = scrollMarks[i];
        if (p >= m && !fired.has(m)) {
          fired.add(m);
          send("scroll_depth", String(m));
        }
      }
    }, 250);
  }, { passive: true });
})();

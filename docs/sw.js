// Le Loisir du Matin: keeps the shell and the last edition available offline.
const SHELL = "loisir-shell-2026-11-14";
const FILES = ["./", "index.html", "manifest.webmanifest", "icon-192.png", "icon-512.png", "icon-180.png"];
self.addEventListener("install", e => { e.waitUntil(caches.open(SHELL).then(c => c.addAll(FILES)).then(() => self.skipWaiting())); });
self.addEventListener("activate", e => { e.waitUntil(caches.keys().then(ks => Promise.all(ks.filter(k => k !== SHELL && k !== "loisir-data").map(k => caches.delete(k)))).then(() => self.clients.claim())); });
self.addEventListener("fetch", e => {
  const u = new URL(e.request.url);
  if (e.request.method !== "GET") return;
  if (u.origin !== location.origin) {
    if (/fonts\.(googleapis|gstatic)\.com$/.test(u.hostname)) e.respondWith(caches.open(SHELL).then(c => c.match(e.request).then(r => r || fetch(e.request).then(n => { c.put(e.request, n.clone()); return n; }))));
    return; // radio streams and everything else go straight to the network
  }
  // same origin: network first so a new edition or a new version shows at once, cache when offline
  e.respondWith(fetch(e.request).then(n => { const copy = n.clone(); caches.open(u.pathname.includes("/data/") ? "loisir-data" : SHELL).then(c => c.put(e.request, copy)); return n; }).catch(() => caches.match(e.request).then(r => r || caches.match("index.html"))));
});

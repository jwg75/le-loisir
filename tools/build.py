#!/usr/bin/env python3
"""Build the standalone web app in docs/ from the page source (index.html) and the latest edition."""
import json, pathlib, shutil
root = pathlib.Path(__file__).resolve().parent.parent
page = (root / "index.html").read_text(encoding="utf-8")
page = page.replace('fetch("edition.json")', 'fetch("data/edition.json",{cache:"no-store"})').replace('fetch("image.json")', 'fetch("data/image.json",{cache:"no-store"})')
assert "data/edition.json" in page and "data/image.json" in page
head = """<!doctype html>
<html lang="fr">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<meta name="robots" content="noindex,nofollow">
<meta name="theme-color" content="#eceae3" media="(prefers-color-scheme: light)">
<meta name="theme-color" content="#17181a" media="(prefers-color-scheme: dark)">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-status-bar-style" content="default">
<meta name="apple-mobile-web-app-title" content="Le Loisir">
<link rel="manifest" href="manifest.webmanifest">
<link rel="apple-touch-icon" href="icon-180.png">
<link rel="icon" href="icon-192.png">
<style>html{color-scheme:light dark}body{margin:0}img{max-width:100%}[hidden]{display:none!important}</style>
</head>
<body>
"""
tail = """
<style>body{padding-top:env(safe-area-inset-top,0px)}</style>
<script>if("serviceWorker" in navigator){navigator.serviceWorker.register("sw.js").catch(function(){})}</script>
</body>
</html>
"""
docs = root / "docs"
(docs / "data").mkdir(parents=True, exist_ok=True)
(docs / "index.html").write_text(head + page + tail, encoding="utf-8")
(docs / ".nojekyll").write_text("")
for name in ("edition.json", "image.json"):
    src = root / name
    if src.exists():
        shutil.copy(src, docs / "data" / name)
ed = json.loads((root / "edition.json").read_text(encoding="utf-8"))
(docs / "sw.js").write_text("""// Le Loisir du Matin: keeps the shell and the last edition available offline.
const SHELL = "loisir-shell-%s";
const FILES = ["./", "index.html", "manifest.webmanifest", "icon-192.png", "icon-512.png", "icon-180.png"];
self.addEventListener("install", e => { e.waitUntil(caches.open(SHELL).then(c => c.addAll(FILES)).then(() => self.skipWaiting())); });
self.addEventListener("activate", e => { e.waitUntil(caches.keys().then(ks => Promise.all(ks.filter(k => k !== SHELL && k !== "loisir-data").map(k => caches.delete(k)))).then(() => self.clients.claim())); });
self.addEventListener("fetch", e => {
  const u = new URL(e.request.url);
  if (e.request.method !== "GET") return;
  if (u.origin !== location.origin) {
    if (/fonts\\.(googleapis|gstatic)\\.com$/.test(u.hostname)) e.respondWith(caches.open(SHELL).then(c => c.match(e.request).then(r => r || fetch(e.request).then(n => { c.put(e.request, n.clone()); return n; }))));
    return; // radio streams and everything else go straight to the network
  }
  // same origin: network first so a new edition or a new version shows at once, cache when offline
  e.respondWith(fetch(e.request).then(n => { const copy = n.clone(); caches.open(u.pathname.includes("/data/") ? "loisir-data" : SHELL).then(c => c.put(e.request, copy)); return n; }).catch(() => caches.match(e.request).then(r => r || caches.match("index.html"))));
});
""" % ed.get("date", "0"))
(docs / "manifest.webmanifest").write_text(json.dumps({
    "name": "Le Loisir du Matin", "short_name": "Le Loisir", "lang": "fr", "start_url": "./", "scope": "./",
    "display": "standalone", "orientation": "portrait", "background_color": "#eceae3", "theme_color": "#eceae3",
    "icons": [{"src": "icon-192.png", "sizes": "192x192", "type": "image/png"}, {"src": "icon-512.png", "sizes": "512x512", "type": "image/png", "purpose": "any maskable"}]
}, ensure_ascii=False, indent=1), encoding="utf-8")
print("built docs/ for edition", ed.get("date"))

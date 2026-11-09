// Bump the version when index.html changes so phones pick up the new copy
const CACHE = 'stotras-v11';
const FILES = ['./', 'index.html', 'manifest.webmanifest', 'icon.png'];

self.addEventListener('install', e => {
  // 'reload' skips the browser's HTTP cache, which can hold the old page for 10 minutes
  e.waitUntil(caches.open(CACHE).then(c => c.addAll(FILES.map(f => new Request(f, { cache: 'reload' })))));
  self.skipWaiting();
});

self.addEventListener('activate', e => {
  e.waitUntil(caches.keys().then(keys =>
    // Only this app's old versions: other apps on this origin keep their caches
    Promise.all(keys.filter(k => k.startsWith('stotras-') && k !== CACHE).map(k => caches.delete(k)))));
  self.clients.claim();
});

// The page itself: newest from the network when online, so updates show straight away.
// The saved copy is for when the phone is offline or the network takes over 3 seconds.
async function freshPage(e) {
  const cache = await caches.open(CACHE);
  const saved = e.request.url.split(/[?#]/)[0]; // one saved copy, whatever the query string
  const network = fetch(e.request.url, { cache: 'no-cache' }).then(res => {
    if (res.ok) cache.put(saved, res.clone());
    return res;
  });
  e.waitUntil(network.catch(() => {}));
  const slow = new Promise(resolve => setTimeout(resolve, 3000));
  const res = await Promise.race([network.catch(() => null), slow]);
  if (res && res.ok) return res;
  return (await cache.match(saved)) || network;
}

// Everything else: from the phone first; fall back to the network and keep a copy (fonts included)
self.addEventListener('fetch', e => {
  if (e.request.method !== 'GET') return;
  if (e.request.mode === 'navigate') {
    e.respondWith(freshPage(e));
    return;
  }
  e.respondWith(caches.match(e.request).then(hit => hit || fetch(e.request).then(res => {
    const copy = res.clone();
    caches.open(CACHE).then(c => c.put(e.request, copy));
    return res;
  })));
});

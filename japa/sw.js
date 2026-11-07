// Bump the version when index.html changes so phones pick up the new copy
const CACHE = 'japa-v7';
const FILES = ['./', 'index.html', 'manifest.webmanifest', 'icon.png'];

self.addEventListener('install', e => {
  // 'reload' skips the browser's HTTP cache, which can hold the old page for 10 minutes
  e.waitUntil(caches.open(CACHE).then(c => c.addAll(FILES.map(f => new Request(f, { cache: 'reload' })))));
  self.skipWaiting();
});

self.addEventListener('activate', e => {
  e.waitUntil(caches.keys().then(keys =>
    // Only this app's old versions: the stotras app shares this origin
    Promise.all(keys.filter(k => k.startsWith('japa-') && k !== CACHE).map(k => caches.delete(k)))));
  self.clients.claim();
});

// Serve from the phone first; fall back to the network and keep a copy (fonts included)
self.addEventListener('fetch', e => {
  if (e.request.method !== 'GET') return;
  e.respondWith(caches.match(e.request).then(hit => hit || fetch(e.request).then(res => {
    const copy = res.clone();
    caches.open(CACHE).then(c => c.put(e.request, copy));
    return res;
  })));
});

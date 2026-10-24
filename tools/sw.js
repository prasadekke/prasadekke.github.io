// The toolbox moved to https://prasadekke.com/tools/. This worker replaces the old cache-first
// one on installed copies: it drops the toolbox caches, unregisters itself, and reloads open
// pages so they pick up the redirect. Other apps on this origin (stotras, japa) keep their caches.
self.addEventListener('install', () => self.skipWaiting());

self.addEventListener('activate', e => {
  e.waitUntil((async () => {
    const keys = await caches.keys();
    await Promise.all(keys.filter(k => k.startsWith('toolbox-')).map(k => caches.delete(k)));
    await self.registration.unregister();
    const pages = await self.clients.matchAll({ type: 'window' });
    pages.forEach(page => page.navigate(page.url));
  })());
});

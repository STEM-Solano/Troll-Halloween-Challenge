// Cache only this versioned game archive. Engine scripts use normal browser caching.
const CACHE = 'troll-halloween-assets-fast2';
const archive = new URL('./trials-and-trolls-math-v1.3-fast2.tar.gz', self.location.href).href;
self.addEventListener('install', event => {
    // Reuse the early preload/HTTP cache when possible. Failure never blocks play.
    event.waitUntil(caches.open(CACHE).then(cache => cache.add(archive))
        .catch(() => {}).then(() => self.skipWaiting()));
});
self.addEventListener('activate', event => {
    event.waitUntil(caches.keys().then(keys => Promise.all(keys
        .filter(key => key.startsWith('troll-halloween-assets-') && key !== CACHE)
        .map(key => caches.delete(key)))).then(() => self.clients.claim()));
});
self.addEventListener('fetch', event => {
    if (event.request.method !== 'GET' || event.request.url !== archive) return;
    event.respondWith(caches.open(CACHE).then(async cache => {
        const hit = await cache.match(event.request);
        if (hit) return hit;
        const response = await fetch(event.request);
        if (response.ok) await cache.put(event.request, response.clone());
        return response;
    }).catch(() => fetch(event.request)));
});

const CACHE_NAME = 'ghostboard-v1';
const STATIC_ASSETS = [
  '/',             // Our index.html (depending on how you're serving it, see note below)
  '/static/simplemde.min.css',
  '/static/simplemde.min.js',
  '/static/manifest.json',
];

// Install event: cache all critical assets
self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then(cache => cache.addAll(STATIC_ASSETS))
      .then(self.skipWaiting())
  );
});

// Activate event: clean up old caches if any
self.addEventListener('activate', event => {
  event.waitUntil(
    caches.keys().then(keys => 
      Promise.all(
        keys.map(key => {
          if (key !== CACHE_NAME) {
            return caches.delete(key);
          }
        })
      )
    ).then(() => self.clients.claim())
  );
});

// Fetch event: try cache first, then network fallback
self.addEventListener('fetch', event => {
  event.respondWith(
    caches.match(event.request).then(cachedResponse => {
      if (cachedResponse) {
        return cachedResponse;
      }
      return fetch(event.request);
    })
  );
});

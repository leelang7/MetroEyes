const CACHE = 'subwaybev-citizen-v3';
const ASSETS = [
  './',
  './index.html',
  './onboard.html',
  './styles.css',
  './manifest.webmanifest',
  '../shared/bev_engine.js',
  '../shared/safety_features.js',
  '../shared/llm_assistant.js',
];

self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE).then((cache) => cache.addAll(ASSETS)).catch(() => {})
  );
  self.skipWaiting();
});

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((keys) => Promise.all(
      keys.filter((k) => k !== CACHE).map((k) => caches.delete(k))
    ))
  );
  self.clients.claim();
});

self.addEventListener('fetch', (event) => {
  if (event.request.method !== 'GET') return;
  event.respondWith(
    caches.match(event.request).then((cached) =>
      cached || fetch(event.request).then((res) => {
        if (res.ok && new URL(event.request.url).origin === location.origin) {
          const clone = res.clone();
          caches.open(CACHE).then((c) => c.put(event.request, clone)).catch(() => {});
        }
        return res;
      }).catch(() => cached)
    )
  );
});

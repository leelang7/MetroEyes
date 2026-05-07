const CACHE = 'subwaybev-citizen-v8-stationpicker';
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

// IDEA-9 도착 알림 — Service Worker 레벨 notificationclick 핸들러
// 잠금 화면 / 백그라운드에서 도착 알림 탭 시 PWA 포커스 복귀
self.addEventListener('notificationclick', (event) => {
  if (event.notification.tag !== 'metroeyes-arrival') return;
  event.notification.close();
  event.waitUntil((async () => {
    const all = await self.clients.matchAll({ type: 'window', includeUncontrolled: true });
    // 이미 열린 PWA 클라이언트 있으면 포커스
    for (const c of all) {
      if (c.url.includes('/passenger_app/')) {
        try { return c.focus(); } catch {}
      }
    }
    // 없으면 새로 오픈
    if (self.clients.openWindow) {
      return self.clients.openWindow('./index.html');
    }
  })());
});

// 페이지에서 SW로 도착 알림 위임 (페이지가 백그라운드 throttle된 경우 SW가 발사)
self.addEventListener('message', (event) => {
  if (!event.data || event.data.type !== 'metroeyes-arrival') return;
  const { title, body, requireInteraction } = event.data;
  try {
    self.registration.showNotification(title, {
      body, tag: 'metroeyes-arrival',
      renotify: true, requireInteraction: !!requireInteraction,
      silent: false,
    });
  } catch {}
});

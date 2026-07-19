// En tom service worker räcker för att göra appen installerbar som en MVP
self.addEventListener('install', (e) => {
  self.skipWaiting();
});

self.addEventListener('fetch', (e) => {
  // Här kan vi lägga till offline-stöd senare om vi vill
});
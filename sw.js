/* The Orthodox Lamp — service worker
   Strategy: stale-while-revalidate for same-origin GET requests, so every page
   and data file you visit is cached and remains available offline. A small shell
   is precached on install so the site opens even on a cold offline start. */
var CACHE = 'ol-cache-v1';
var SHELL = ['./', './index.html', './manifest.webmanifest',
             './icon-192.png', './icon-512.png'];

self.addEventListener('install', function (e) {
  e.waitUntil(
    caches.open(CACHE).then(function (c) {
      // best-effort: don't fail install if one asset 404s
      return Promise.allSettled(SHELL.map(function (u) { return c.add(u); }));
    }).then(function () { return self.skipWaiting(); })
  );
});

self.addEventListener('activate', function (e) {
  e.waitUntil(
    caches.keys().then(function (keys) {
      return Promise.all(keys.map(function (k) {
        if (k !== CACHE) return caches.delete(k);
      }));
    }).then(function () { return self.clients.claim(); })
  );
});

self.addEventListener('fetch', function (e) {
  var req = e.request;
  if (req.method !== 'GET') return;
  var url = new URL(req.url);
  if (url.origin !== self.location.origin) return; // pass through cross-origin

  e.respondWith(
    caches.open(CACHE).then(function (cache) {
      return cache.match(req).then(function (cached) {
        var network = fetch(req).then(function (res) {
          if (res && res.status === 200 && res.type === 'basic') {
            cache.put(req, res.clone());
          }
          return res;
        }).catch(function () {
          // offline: for navigations, fall back to a cached page then the shell
          if (req.mode === 'navigate') {
            return cache.match(req).then(function (m) {
              return m || cache.match('./index.html') || cache.match('./');
            });
          }
          return cached;
        });
        return cached || network;
      });
    })
  );
});

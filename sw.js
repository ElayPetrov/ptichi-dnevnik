// Птичи дневник — service worker.
// Пази копие на страницата, иконите и шрифтовете, за да се отваря и без интернет.
// Записите и снимките НЕ са тук — те са в localStorage / IndexedDB на устройството.
const V = 'pd-3';   // смени, ако промениш този файл; старият кеш се трие сам
const SHELL = ['manifest.webmanifest', 'icon-192.png', 'icon-512.png', 'apple-touch-icon.png'];
const FONTS = /^https:\/\/fonts\.(googleapis|gstatic)\.com\//;

// пренасочен отговор не бива да се дава на навигация — пазим чисто копие
const clean = async r => r.redirected
  ? new Response(await r.blob(), { status: r.status, statusText: r.statusText, headers: r.headers })
  : r;

self.addEventListener('install', e => e.waitUntil((async () => {
  const c = await caches.open(V);
  try { const r = await fetch('./', { cache: 'reload' }); if (r.ok) await c.put('index.html', await clean(r)); } catch (x) {}
  await Promise.all(SHELL.map(u => fetch(u, { cache: 'reload' }).then(r => r.ok && c.put(u, r)).catch(() => {})));
  await self.skipWaiting();
})()));

self.addEventListener('activate', e => e.waitUntil((async () => {
  for (const k of await caches.keys()) if (k !== V) await caches.delete(k);
  await self.clients.claim();
})()));

self.addEventListener('fetch', e => {
  const r = e.request;
  if (r.method !== 'GET') return;

  if (r.mode === 'navigate') {
    // Страницата: първо мрежата, за да идват обновленията. Ако до 3 с няма отговор
    // (една чертичка обхват) или няма мрежа — запазеното копие. Късен отговор пак обновява копието.
    // GitHub Pages казва на браузъра да пази страницата 10 минути; „no-cache“ все пак пита сървъра (евтино, с ETag),
    // така че новата версия идва веднага, а не до 10 минути по-късно.
    const net = fetch(new Request(r.url, { cache: 'no-cache', credentials: 'same-origin' })).then(async res => {
      if (res.ok) { const c = await caches.open(V); await c.put('index.html', await clean(res.clone())); }
      return res;
    });
    e.waitUntil(net.catch(() => {}));
    e.respondWith((async () => {
      const cached = await caches.match('index.html');
      if (!cached) return net;
      return new Promise(ok => {
        let done = false;
        const give = x => { if (!done) { done = true; ok(x); } };
        net.then(res => give(res.ok || res.type === 'opaqueredirect' ? res : cached), () => give(cached));
        setTimeout(() => give(cached), 3000);
      });
    })());
    return;
  }

  if (new URL(r.url).origin === location.origin || FONTS.test(r.url)) {
    // иконите, манифестът, шрифтовете: веднага от копието, мрежата го опреснява за следващия път
    const net = fetch(r).then(async res => {
      if (res.ok) { const c = await caches.open(V); await c.put(r, res.clone()); }
      return res;
    });
    e.waitUntil(net.catch(() => {}));
    e.respondWith(caches.match(r).then(hit => hit || net));
  }
  // всичко останало (истинската карта, Leaflet) върви направо към мрежата
});

// Известия (2026-11-03): помощникът „push“ праща {t: заглавие, b: текст, u: къде да отвори, g: етикет}.
// Етикетът слива повторенията (напр. няколко предложения по един въпрос стават едно известие).
self.addEventListener('push', e => {
  let d = {};
  try { d = e.data ? e.data.json() : {}; } catch (x) { d = { b: e.data ? e.data.text() : '' }; }
  e.waitUntil(self.registration.showNotification(d.t || 'Перá', {
    body: d.b || '', icon: 'icon-192.png', badge: 'icon-192.png', tag: d.g || undefined, renotify: !!d.g, data: { u: d.u || './' } }));
});
// Докоснато известие: отворената Перá се показва и отива на мястото; ако не е отворена — отваря се там.
self.addEventListener('notificationclick', e => {
  e.notification.close();
  const url = new URL((e.notification.data && e.notification.data.u) || './', self.registration.scope).href;
  e.waitUntil((async () => {
    for (const c of await self.clients.matchAll({ type: 'window', includeUncontrolled: true }))
      if (c.url.startsWith(self.registration.scope)) { await c.focus(); c.postMessage({ go: url }); return; }
    await self.clients.openWindow(url);
  })());
});

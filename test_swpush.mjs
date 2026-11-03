// The service worker's notification part (sw.js), run in Node with a stand-in „self“:
// an arriving message is shown with its title, text, tag and target; a tap opens Перá or brings the open one there.
import fs from "node:fs";
let fails = 0;
const check = (n, got, exp) => { const ok = JSON.stringify(got) === JSON.stringify(exp); fails += !ok; console.log((ok ? "PASS " : "FAIL ") + n + (ok ? "" : "\n     got " + JSON.stringify(got) + "\n     exp " + JSON.stringify(exp))); };
const H = {}, shown = [], opened = [], posted = [];
let windows = [];
const self = {
  addEventListener: (t, f) => { H[t] = f; }, skipWaiting: async () => {},
  registration: { scope: "https://elaypetrov.github.io/ptichi-dnevnik/", showNotification: async (t, o) => { shown.push([t, o]); } },
  clients: { claim: async () => {}, matchAll: async () => windows, openWindow: async (u) => { opened.push(u); } },
};
new Function("self", "caches", "fetch", "location", fs.readFileSync("sw.js", "utf8"))(self, {}, async () => ({}), { origin: "https://elaypetrov.github.io" });
const ev = (extra) => { const w = []; return { ...extra, waitUntil: (p) => w.push(p), done: () => Promise.all(w) }; };
let e = ev({ data: { json: () => ({ t: "Петър пита: какво е това?", b: "3 ное, Копринка", u: "./?go=friends", g: "ask:u2:5" }) } });
H.push(e); await e.done();
check("W1 a message is shown with its title, text and tag (repeats merge), and remembers where to open", shown[0],
  ["Петър пита: какво е това?", { body: "3 ное, Копринка", icon: "icon-192.png", badge: "icon-192.png", tag: "ask:u2:5", renotify: true, data: { u: "./?go=friends" } }]);
e = ev({ data: { json: () => { throw new Error("not json"); }, text: () => "просто текст" } }); H.push(e); await e.done();
check("W2 a plain-text message still shows, titled „Перá“", [shown[1][0], shown[1][1].body], ["Перá", "просто текст"]);
let closed = 0;
e = ev({ notification: { close: () => closed++, data: { u: "./?go=q:42" } } }); H.notificationclick(e); await e.done();
check("W3 tapping with Перá closed opens it at the right place", [closed, opened], [1, ["https://elaypetrov.github.io/ptichi-dnevnik/?go=q:42"]]);
windows = [{ url: "https://elaypetrov.github.io/ptichi-dnevnik/", focus: async () => posted.push("focus"), postMessage: (m) => posted.push(m) }];
e = ev({ notification: { close: () => closed++, data: { u: "./?go=friends" } } }); H.notificationclick(e); await e.done();
check("W4 tapping with Перá open brings it forward and tells it where to go (no second window)", [posted, opened.length], [["focus", { go: "https://elaypetrov.github.io/ptichi-dnevnik/?go=friends" }], 1]);
check("W5 the cache version moved on, so phones pick up the new worker", /const V = 'pd-3'/.test(fs.readFileSync("sw.js", "utf8")), true);
console.log("FAILURES:", fails);

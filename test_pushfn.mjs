// The push helper (supabase/functions/push): encryption checked against an independent decryptor (http_ece),
// the VAPID signature against Node's own crypto, and who gets told what.
// Run: cp supabase/functions/push/index.ts /tmp/pushfn.mjs && node test_pushfn.mjs   (needs: npm install http_ece in /tmp/pushtest)
import crypto from "node:crypto";
import { createRequire } from "node:module";
const require = createRequire("/tmp/pushtest/");
const ece = require("http_ece");
const F = await import("/tmp/pushfn.mjs");
let fails = 0;
const check = (n, got, exp) => { const ok = JSON.stringify(got) === JSON.stringify(exp); fails += !ok; console.log((ok ? "PASS " : "FAIL ") + n + (ok ? "" : "\n     got " + JSON.stringify(got) + "\n     exp " + JSON.stringify(exp))); };
// a phone: its own key pair and auth secret, as a browser would make them
const ua = crypto.createECDH("prime256v1"); ua.generateKeys();
const auth = crypto.randomBytes(16);
const sub = { endpoint: "https://fcm.googleapis.com/fcm/send/abc", p256dh: F.b64u.enc(ua.getPublicKey()), auth: F.b64u.enc(auth) };
const msg = JSON.stringify({ t: "Петър пита: какво е това?", b: "3 ное, Копринка", u: "./?go=friends" });
const body = await F.encrypt(msg, sub.p256dh, sub.auth);
const plain = ece.decrypt(Buffer.from(body), { version: "aes128gcm", privateKey: ua, authSecret: auth }).toString("utf8");
check("P1 the phone can decrypt the message (independent RFC 8291 decryptor)", plain, msg);
check("P2 the header: 16-byte salt, record size 4096, the sender key (65 bytes)", [Buffer.from(body.slice(16, 20)).readUInt32BE(0), body[20]], [4096, 65]);
const keys = await F.makeKeys();
const a = await F.vapidAuth(sub.endpoint, keys, "mailto:pera@birds.bg", Date.UTC(2026, 10, 3));
const m = /^vapid t=([^.]+)\.([^.]+)\.([^,]+), k=(.+)$/.exec(a);
const claims = JSON.parse(Buffer.from(m[2], "base64url").toString());
const pubKey = crypto.createPublicKey({ key: { kty: "EC", crv: "P-256", x: F.b64u.enc(F.b64u.dec(keys.pub).slice(1, 33)), y: F.b64u.enc(F.b64u.dec(keys.pub).slice(33)) }, format: "jwk" });
const okSig = crypto.verify("sha256", Buffer.from(m[1] + "." + m[2]), { key: pubKey, dsaEncoding: "ieee-p1363" }, Buffer.from(m[3], "base64url"));
check("P3 the VAPID signature verifies with the public key; audience is the push service, 12 h validity", [okSig, claims.aud, claims.exp - Math.floor(Date.UTC(2026, 10, 3) / 1000), m[4] === keys.pub], [true, "https://fcm.googleapis.com", 43200, true]);
// who gets told what
const names = { me: "Иван", u2: "Петър", u3: "Мария" };
const J = (obs, outs = []) => ({ obs, outs });
const first = F.journalEvents("u2", J([{ id: 1, ask: 5, bg: "Сива овесарка", date: "2026-11-03", place: "Копринка" }]), null, ["me", "u3"], names);
check("P4 the first look at a journal only remembers it (no flood of old questions)", [first.ev.length, first.now], [0, { ask: ["1"], ok: [], inv: [] }]);
const j2 = J([{ id: 1, ask: 5, bg: "Сива овесарка", date: "2026-11-03", place: "Копринка" }, { id: 2, ask: 9, bg: "Непозната птица", date: "2026-11-03", note: "малка, кафява" }],
  [{ id: "s1", date: "2026-11-08", place: "Атанасовско езеро", inv: { me: 77 } }]);
const e2 = F.journalEvents("u2", j2, first.now, ["me", "u3"], names).ev;
check("P5 a new question goes to every follower; a new invitation to the invited", e2.map((e) => [e.to, e.kind, e.t, e.b]), [
  ["me", "ask", "Петър пита: какво е това?", "3 ное — малка, кафява"], ["u3", "ask", "Петър пита: какво е това?", "3 ное — малка, кафява"],
  ["me", "inv", "Петър те кани на излет", "8 ное, Атанасовско езеро"]]);
const j3 = J([{ id: 1, bg: "Червеногръдка", date: "2026-11-03", askOk: { by: "me" } }]);
const e3 = F.journalEvents("u2", j3, F.sig(j2), ["me"], names).ev;
check("P6 an accepted identification goes to whoever suggested it", e3.map((e) => [e.to, e.kind, e.t, e.b]), [["me", "idp", "Петър прие твоето определение", "Червеногръдка · 3 ное"]]);
const S = (row, thread = []) => F.socialEvents(row, names, thread).map((e) => [e.to, e.kind, e.t, e.b, e.u]);
check("P7 a suggestion on your question", S({ owner: "u2", item: "q:2", author: "me", kind: "comment", body: "🔎 Сива овесарка (Emberiza calandra)\nдебел клюн" }),
  [["u2", "idp", "Иван предложи вид", "Сива овесарка (Emberiza calandra)", "./?go=q:2"]]);
check("P8 a comment on your outing; your own comment tells nobody", [S({ owner: "u2", item: "o:s1", author: "me", kind: "comment", body: "Страхотен ден!" }), S({ owner: "u2", item: "o:s1", author: "u2", kind: "comment", body: "Благодаря" })],
  [[["u2", "comment", "Иван коментира", "Страхотен ден!", "./?go=friends"]], []]);
check("P9 a reply „@Мария: …“ reaches Мария (who wrote in that thread) as well as the owner", S({ owner: "u2", item: "o:s1", author: "me", kind: "comment", body: "@Мария: и аз го видях!" }, [{ author: "u3" }, { author: "me" }]),
  [["u2", "comment", "Иван коментира", "и аз го видях!", "./?go=friends"], ["u3", "comment", "Иван ти отговори", "и аз го видях!", "./?go=friends"]]);
check("P10 a bravo, as its own kind", S({ owner: "u2", item: "d:2026-11-03", author: "me", kind: "bravo" }), [["u2", "bravo", "Иван: браво!", "за записите ти от 3 ное", "./?go=friends"]]);
// the whole helper with a fake database: kinds per phone, dead phones removed, keys made once
const DB = { push_keys: [], push_subs: [
  { id: "a", user_id: "u2", endpoint: "https://x/1", p256dh: sub.p256dh, auth: sub.auth, kinds: ["ask", "idp", "inv", "comment"] },
  { id: "b", user_id: "u2", endpoint: "https://x/2", p256dh: sub.p256dh, auth: sub.auth, kinds: ["comment"] },
  { id: "c", user_id: "u2", endpoint: "https://x/dead", p256dh: sub.p256dh, auth: sub.auth, kinds: ["idp"] }],
  social: [{ id: "r1", owner: "u2", item: "q:2", author: "me", kind: "comment", body: "🔎 Сива овесарка (Emberiza calandra)" }],
  profiles: [{ user_id: "me", name: "Иван" }, { user_id: "u2", name: "Петър" }] };
const fake = { get: async (p) => { const t = p.split("?")[0], q = decodeURIComponent(p.split("?")[1] || "");
    let rows = DB[t] || [];
    for (const [, k, v] of q.matchAll(/(\w+)=eq\.([^&]+)/g)) rows = rows.filter((r) => String(r[k]) === v);
    for (const [, k, v] of q.matchAll(/(\w+)=in\.\(([^)]*)\)/g)) { const L = v.split(",").map((x) => x.replace(/"/g, "")); rows = rows.filter((r) => L.includes(String(r[k]))); }
    return rows; },
  put: async (p, b) => { const t = p.split("?")[0]; DB[t] = (DB[t] || []).filter((r) => r.id !== b.id && r.owner !== b.owner || r.owner === undefined && r.id !== b.id).concat([b]); },
  del: async (p) => { const id = /id=eq\.(.+)$/.exec(p)[1]; DB.push_subs = DB.push_subs.filter((s) => s.id !== id); } };
const sent = [];
const send = async (s, payload) => { sent.push([s.endpoint, payload.k, payload.t]); return s.endpoint.endsWith("dead") ? 410 : 201; };
const R = (body) => new Request("https://f/push", { method: "POST", body: JSON.stringify(body) });
const r1 = await (await F.handle(R({ table: "social", id: "r1" }), { db: fake, send })).json();
check("P11 only phones that chose that kind are told; a dead phone's subscription is removed", [r1, sent, DB.push_subs.map((s) => s.id)],
  [{ sent: 1 }, [["https://x/1", "idp", "Иван предложи вид"], ["https://x/dead", "idp", "Иван предложи вид"]], ["a", "b"]]);
const k1 = await (await F.handle(new Request("https://f/push?key=1"), { db: fake, send })).json();
const k2 = await (await F.handle(new Request("https://f/push?key=1"), { db: fake, send })).json();
check("P12 the public key is made once and then always the same", [typeof k1.key, k1.key.length, k1.key === k2.key, DB.push_keys.length], ["string", 87, true, 1]);
sent.length = 0;
const t1 = await (await F.handle(R({ test: "https://x/2" }), { db: fake, send })).json();
const t2 = await (await F.handle(R({ test: "https://not/subscribed" }), { db: fake, send })).json();
check("P13 a test message only reaches a phone that is subscribed", [t1.sent, t2.sent, sent.length], [1, 0, 1]);
console.log("FAILURES:", fails);

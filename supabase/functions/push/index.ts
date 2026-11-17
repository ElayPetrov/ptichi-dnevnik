// push — известията на Перá към телефоните (Web Push).
// Базата казва „нещо стана“ само с номер (нов ред в social) или с човек (променен дневник); помощникът сам чете
// истинските данни със служебния ключ и решава кого да извести. Затова фалшиво повикване не може да измисли известие.
// Ключовете VAPID се правят сами при първото повикване и стоят в таблица push_keys (само служебният ключ я вижда).
// Шифрирането е по RFC 8291 (aes128gcm), подписът — по RFC 8292 (ES256), само с WebCrypto.
const CORS = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Headers": "authorization, x-client-info, apikey, content-type",
  "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
};
const json = (d, status = 200) => new Response(JSON.stringify(d), { status, headers: { ...CORS, "Content-Type": "application/json" } });
export const KINDS = ["ask", "idp", "inv", "comment", "bravo"];
const te = new TextEncoder();
export const b64u = {
  enc: (b) => { let s = ""; for (const x of new Uint8Array(b)) s += String.fromCharCode(x); return btoa(s).replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/, ""); },
  dec: (s) => { s = String(s).replace(/-/g, "+").replace(/_/g, "/"); while (s.length % 4) s += "="; return Uint8Array.from(atob(s), (c) => c.charCodeAt(0)); },
};
const cat = (...a) => { const n = a.reduce((x, y) => x + y.length, 0), o = new Uint8Array(n); let i = 0; for (const x of a) { o.set(x, i); i += x.length; } return o; };
const S = () => globalThis.crypto.subtle;

// ---- ключовете ----
export async function makeKeys() {
  const kp = await S().generateKey({ name: "ECDSA", namedCurve: "P-256" }, true, ["sign", "verify"]);
  return { pub: b64u.enc(await S().exportKey("raw", kp.publicKey)), priv: JSON.stringify(await S().exportKey("jwk", kp.privateKey)) };
}
// подписът VAPID за адреса на телефона (aud = origin на адреса)
export async function vapidAuth(endpoint, keys, sub = "mailto:pera@birds.bg", now = Date.now()) {
  const enc = (o) => b64u.enc(te.encode(JSON.stringify(o)));
  const head = enc({ typ: "JWT", alg: "ES256" }), body = enc({ aud: new URL(endpoint).origin, exp: Math.floor(now / 1000) + 12 * 3600, sub });
  const k = await S().importKey("jwk", JSON.parse(keys.priv), { name: "ECDSA", namedCurve: "P-256" }, false, ["sign"]);
  const sig = await S().sign({ name: "ECDSA", hash: "SHA-256" }, k, te.encode(head + "." + body));
  return "vapid t=" + head + "." + body + "." + b64u.enc(sig) + ", k=" + keys.pub;
}
const hkdf = async (salt, ikm, info, len) => new Uint8Array(await S().deriveBits({ name: "HKDF", hash: "SHA-256", salt, info },
  await S().importKey("raw", ikm, "HKDF", false, ["deriveBits"]), len * 8));
// шифрира съобщението за един телефон (p256dh и auth са от абонамента му)
export async function encrypt(text, p256dh, auth, salt = globalThis.crypto.getRandomValues(new Uint8Array(16))) {
  const ua = b64u.dec(p256dh), secret = b64u.dec(auth);
  const eph = await S().generateKey({ name: "ECDH", namedCurve: "P-256" }, true, ["deriveBits"]);
  const asPub = new Uint8Array(await S().exportKey("raw", eph.publicKey));
  const uaKey = await S().importKey("raw", ua, { name: "ECDH", namedCurve: "P-256" }, false, []);
  const shared = new Uint8Array(await S().deriveBits({ name: "ECDH", public: uaKey }, eph.privateKey, 256));
  const ikm = await hkdf(secret, shared, cat(te.encode("WebPush: info\0"), ua, asPub), 32);
  const cek = await hkdf(salt, ikm, te.encode("Content-Encoding: aes128gcm\0"), 16);
  const nonce = await hkdf(salt, ikm, te.encode("Content-Encoding: nonce\0"), 12);
  const key = await S().importKey("raw", cek, "AES-GCM", false, ["encrypt"]);
  const ct = new Uint8Array(await S().encrypt({ name: "AES-GCM", iv: nonce }, key, cat(te.encode(text), new Uint8Array([2]))));
  const rs = new Uint8Array([0, 0, 16, 0]);   // 4096
  return cat(salt, rs, new Uint8Array([asPub.length]), asPub, ct);
}
async function sendOne(sub, payload, keys) {
  const body = await encrypt(JSON.stringify(payload), sub.p256dh, sub.auth);
  const r = await fetch(sub.endpoint, { method: "POST", body, headers: {
    Authorization: await vapidAuth(sub.endpoint, keys), TTL: "86400", Urgency: "normal",
    "Content-Encoding": "aes128gcm", "Content-Type": "application/octet-stream" } });
  return r.status;
}

// ---- какво се е случило ----
const PROP = /^🔎 ([^\n(]+?)(?: \(([^)\n]+)\))?(?:\n|$)/;
const short = (t, n = 110) => { t = String(t || "").replace(/\s+/g, " ").trim(); return t.length > n ? t.slice(0, n - 1) + "…" : t; };
const dayBG = (d) => { const m = /^(\d{4})-(\d\d)-(\d\d)$/.exec(d || ""); return m ? +m[3] + " " + ["яну", "фев", "мар", "апр", "май", "юни", "юли", "авг", "сеп", "окт", "ное", "дек"][+m[2] - 1] : ""; };
// подписът на дневника: отворените въпроси, приетите определения и поканите (същото като public.push_sig в базата)
export function sig(data) {
  const obs = (data && data.obs) || [], outs = (data && data.outs) || [];
  return {
    ask: obs.filter((o) => o && o.ask && !o.askOk).map((o) => String(o.id)),
    ok: obs.filter((o) => o && o.askOk && o.askOk.by).map((o) => String(o.id) + ":" + o.askOk.by),
    inv: outs.flatMap((s) => Object.entries((s && s.inv) || {}).map(([u, t]) => String(s.id) + ":" + u + ":" + t)),
  };
}
// събитията в дневника на owner спрямо видяното досега; при първо виждане — само се запомня, без известия
export function journalEvents(owner, data, seen, followers, names) {
  const now = sig(data), ev = [], nm = names[owner] || "Приятел";
  if (!seen) return { ev, now };
  const fresh = (k) => now[k].filter((x) => !(seen[k] || []).includes(x));
  const obs = (data.obs || []), outs = (data.outs || []);
  for (const id of fresh("ask")) {
    const o = obs.find((o) => String(o.id) === id) || {};
    const guess = o.bg && o.bg !== "Непозната птица" ? "Мисли, че е " + o.bg + "? " : "";
    for (const u of followers) ev.push({ to: u, kind: "ask", t: nm + " пита: какво е това?", b: short(guess + [dayBG(o.date), o.place].filter(Boolean).join(", ") + (o.note ? " — " + o.note : "")), u: "./?go=friends", g: "ask:" + owner + ":" + id });
  }
  for (const k of fresh("ok")) {
    const [id, by] = [k.slice(0, k.lastIndexOf(":")), k.slice(k.lastIndexOf(":") + 1)];
    if (by === owner) continue;
    const o = obs.find((o) => String(o.id) === id) || {};
    ev.push({ to: by, kind: "idp", t: nm + " прие твоето определение", b: short((o.bg || "") + (o.date ? " · " + dayBG(o.date) : "")), u: "./?go=friends", g: "ok:" + owner + ":" + id });
  }
  for (const k of fresh("inv")) {
    const [sid, u] = k.split(":");
    const s = outs.find((s) => String(s.id) === sid) || {};
    ev.push({ to: u, kind: "inv", t: nm + " те кани на излет", b: short([dayBG(s.date), s.place].filter(Boolean).join(", ")), u: "./?go=friends", g: "inv:" + owner + ":" + sid });
  }
  return { ev, now };
}
// събитията от нов ред в social
export function socialEvents(row, names, thread) {
  const ev = [], a = names[row.author] || "Приятел", item = String(row.item || "");
  if (row.kind === "bravo" && row.author !== row.owner) ev.push({ to: row.owner, kind: "bravo", t: a + ": браво!", b: item.startsWith("o:") ? "за излета ти" : "за записите ти от " + dayBG(item.slice(2)), u: "./?go=friends", g: "bravo:" + item });
  if (row.kind !== "comment") return ev;
  if (item.startsWith("q:")) {
    const m = PROP.exec(row.body || "");
    if (row.author !== row.owner) ev.push({ to: row.owner, kind: "idp", t: a + " предложи вид", b: m ? m[1] + (m[2] ? " (" + m[2] + ")" : "") : short(row.body), u: "./?go=q:" + item.slice(2), g: "idp:" + item });
    return ev;
  }
  const body = String(row.body || ""), rm = /^@([^:\n]{1,60}):\s*/.exec(body);
  if (row.author !== row.owner) ev.push({ to: row.owner, kind: "comment", t: a + " коментира", b: short(rm ? body.slice(rm[0].length) : body), u: "./?go=friends", g: "c:" + item });
  if (rm) {   // отговор „@Име: …“ — към хората с това име, писали в същата нишка
    const who = [...new Set(thread.filter((s) => s.author !== row.author && (names[s.author] || "") === rm[1].trim()).map((s) => s.author))];
    for (const u of who) if (u !== row.owner || row.author === row.owner) ev.push({ to: u, kind: "comment", t: a + " ти отговори", b: short(body.slice(rm[0].length)), u: "./?go=friends", g: "r:" + item });
  }
  return ev;
}

// ---- базата (служебният ключ) ----
function restDB() {
  const env = (k) => Deno.env.get(k), SB = env("SUPABASE_URL"), SK = env("SUPABASE_SERVICE_ROLE_KEY");
  const H = { apikey: SK, Authorization: "Bearer " + SK, "Content-Type": "application/json" };
  return {
    get: async (p) => { const r = await fetch(SB + "/rest/v1/" + p, { headers: H }); return r.ok ? await r.json() : []; },
    put: async (p, body) => { await fetch(SB + "/rest/v1/" + p, { method: "POST", headers: { ...H, Prefer: "resolution=merge-duplicates" }, body: JSON.stringify(body) }); },
    del: async (p) => { await fetch(SB + "/rest/v1/" + p, { method: "DELETE", headers: H }); },
  };
}
async function getKeys(db) {
  const k = (await db.get("push_keys?select=pub,priv&id=eq.1"))[0];
  if (k) return k;
  const n = await makeKeys(); await db.put("push_keys", { id: 1, ...n });
  return (await db.get("push_keys?select=pub,priv&id=eq.1"))[0] || n;
}
const inList = (ids) => "(" + ids.map((x) => '"' + x + '"').join(",") + ")";
async function namesOf(db, ids) {
  const out = {};
  if (ids.length) for (const p of await db.get("profiles?select=user_id,name&user_id=in." + inList(ids))) out[p.user_id] = p.name || "Приятел";
  return out;
}
// изпраща събитията на абонираните за този вид телефони; изтрива мъртвите абонаменти
async function deliver(db, ev, send) {
  const to = [...new Set(ev.map((e) => e.to))].filter(Boolean);
  if (!to.length) return { sent: 0 };
  const subs = await db.get("push_subs?select=id,user_id,endpoint,p256dh,auth,kinds&user_id=in." + inList(to));
  const keys = await getKeys(db);
  let sent = 0;
  for (const e of ev) for (const s of subs.filter((s) => s.user_id === e.to && (s.kinds || []).includes(e.kind))) {
    try {
      const st = await send(s, { t: e.t, b: e.b, u: e.u, g: e.g, k: e.kind }, keys);
      if (st === 404 || st === 410) await db.del("push_subs?id=eq." + s.id); else if (st < 300) sent++;
    } catch (_) { /* един телефон не бива да спира другите */ }
  }
  return { sent };
}

export async function handle(req, deps = {}) {
  if (req.method === "OPTIONS") return new Response("ok", { headers: CORS });
  const db = deps.db || restDB(), send = deps.send || sendOne;
  try {
    if (req.method === "GET") return json({ key: (await getKeys(db)).pub });
    const p = await req.json().catch(() => ({}));
    if (p.test) {   // пробно известие — само до абонамент, който съществува (адресът е известен само на телефона)
      const s = (await db.get("push_subs?select=id,user_id,endpoint,p256dh,auth,kinds&endpoint=eq." + encodeURIComponent(p.test)))[0];
      if (!s) return json({ sent: 0 });
      const st = await send(s, { t: "Перá", b: "Известията работят на този телефон 🐦", u: "./", g: "test", k: "test" }, await getKeys(db));
      return json({ sent: st < 300 ? 1 : 0, status: st });
    }
    if (p.table === "social" && p.id) {
      const row = (await db.get("social?select=id,owner,item,author,kind,body&id=eq." + encodeURIComponent(p.id)))[0];
      if (!row) return json({ sent: 0 });
      const thread = row.kind === "comment" ? await db.get("social?select=author&kind=eq.comment&owner=eq." + row.owner + "&item=eq." + encodeURIComponent(row.item)) : [];
      const names = await namesOf(db, [...new Set([row.author, row.owner, ...thread.map((s) => s.author)])]);
      return json(await deliver(db, socialEvents(row, names, thread), send));
    }
    if (p.table === "journals" && p.owner) {
      const j = (await db.get("journals?select=data&user_id=eq." + encodeURIComponent(p.owner)))[0];
      if (!j) return json({ sent: 0 });
      const st = (await db.get("push_state?select=seen&owner=eq." + encodeURIComponent(p.owner)))[0];
      const followers = (await db.get("viewers?select=viewer&owner=eq." + encodeURIComponent(p.owner))).map((v) => v.viewer);
      const names = await namesOf(db, [p.owner]);
      const { ev, now } = journalEvents(p.owner, j.data || {}, st ? st.seen : null, followers, names);
      await db.put("push_state", { owner: p.owner, seen: now, updated_at: new Date().toISOString() });
      return json(await deliver(db, ev, send));
    }
    return json({ error: "?" }, 400);
  } catch (e) { return json({ error: String(e && e.message || e) }, 500); }
}
if (typeof Deno !== "undefined" && Deno.serve) Deno.serve((req) => handle(req));

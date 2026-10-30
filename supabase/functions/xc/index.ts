// xc — помощникът за гласовете на Птичи дневник.
// Приложението пита: „песен и обаждане за Turdus merula“ (?sp=Turdus%20merula). Помощникът пита xeno-canto със
// своя ключ (секрет XC_KEY — никога не стига до приложението), избира два записа и връща само номерата и авторите им.
// Избор: България, после съседите, после Европа, после отвсякъде; качество A, после B; дължина 4–60 секунди.
// Всеки вид се търси веднъж за всички (таблица xc_cache, пази 90 дни).
const NEAR = ["Romania", "Greece", "Serbia", "North Macedonia", "Turkey"];
const CORS = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Headers": "authorization, x-client-info, apikey, content-type",
  "Access-Control-Allow-Methods": "GET, OPTIONS",
};
const json = (d, status = 200) => new Response(JSON.stringify(d), { status, headers: { ...CORS, "Content-Type": "application/json" } });
const secs = (l) => { const p = String(l || "").split(":").map(Number); return p.length === 2 && p.every((n) => !isNaN(n)) ? p[0] * 60 + p[1] : 999; };
const tier = (c) => (c === "Bulgaria" ? 0 : NEAR.includes(c) ? 1 : 2);
// по-ниско е по-добре. Песента: първо мястото (птиците имат диалекти), после чист запис; обаждането: първо чист запис
// (бутонът „обаждане“ не бива да пуска предимно песен), после мястото. После качество и дължина.
const mixed = (x) => /\bsong\b/i.test(x.type || "") && /\bcall\b/i.test(x.type || "");
const score = (x, eu, t) => tier(x.cnt) * 1000 + (eu.has(x.id) || tier(x.cnt) < 2 ? 0 : 500) + (mixed(x) ? (t === "call" ? 5000 : 20) : 0) + ({ A: 0, B: 10 }[x.q] ?? 50) + (secs(x.length) >= 4 && secs(x.length) <= 60 ? 0 : 30);
const isType = (x, t) => new RegExp("\\b" + t + "\\b", "i").test(x.type || "");
export function choose(recs, euIds = new Set()) {
  const out = (x) => x && { id: x.id, file: x.file, rec: x.rec, lic: x.lic, cnt: x.cnt, loc: x.loc, len: x.length, url: x.url, q: x.q };
  const pick = (t) => recs.filter((x) => isType(x, t) && x.file).sort((a, b) => score(a, euIds, t) - score(b, euIds, t))[0] || null;
  return { song: out(pick("song")), call: out(pick("call")) };
}
async function xc(query, key) {
  const r = await fetch("https://xeno-canto.org/api/3/recordings?query=" + encodeURIComponent(query) + "&key=" + encodeURIComponent(key));
  if (!r.ok) throw new Error("xeno-canto " + r.status);
  return (await r.json()).recordings || [];
}
export async function handle(req) {
  if (req.method === "OPTIONS") return new Response("ok", { headers: CORS });
  const sp = (new URL(req.url).searchParams.get("sp") || "").trim();
  if (!/^[A-Z][a-zë-]+ [a-z-]+$/.test(sp)) return json({ error: "sp" }, 400);
  const env = (k) => Deno.env.get(k), SB = env("SUPABASE_URL"), SK = env("SUPABASE_SERVICE_ROLE_KEY"), KEY = env("XC_KEY");
  const H = { apikey: SK, Authorization: "Bearer " + SK, "Content-Type": "application/json" };
  try {
    const c = await fetch(SB + "/rest/v1/xc_cache?select=data,at&sp=eq." + encodeURIComponent(sp), { headers: H });
    const hit = c.ok ? (await c.json())[0] : null;
    if (hit && Date.now() - new Date(hit.at).getTime() < 90 * 864e5) return json(hit.data);
  } catch (_) { /* без паметта — питаме направо */ }
  if (!KEY) return json({ error: "no key" }, 500);
  try {
    const q = 'sp:"' + sp + '" grp:birds';
    let recs = await xc(q + " cnt:bulgaria", KEY), eu = new Set();
    let d = choose(recs);
    if (!d.song || !d.call) { const e = await xc(q + " area:europe", KEY); eu = new Set(e.map((x) => x.id)); recs = recs.concat(e); d = choose(recs, eu); }
    if (!d.song || !d.call) { recs = recs.concat(await xc(q, KEY)); d = choose(recs, eu); }
    await fetch(SB + "/rest/v1/xc_cache", { method: "POST", headers: { ...H, Prefer: "resolution=merge-duplicates" }, body: JSON.stringify({ sp, data: d, at: new Date().toISOString() }) });
    return json(d);
  } catch (e) { return json({ error: String(e && e.message || e) }, 502); }
}
if (typeof Deno !== "undefined" && Deno.serve) Deno.serve(handle);

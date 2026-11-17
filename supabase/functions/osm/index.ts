// osm — помощник на Перá: пита eBird (с ключа), зоните за птици на ЕАОС и Overpass от сървъра на Supabase, не от телефона.
// Нужен е, защото на някои мобилни мрежи безплатните сървъри на Overpass не отговарят на телефоните (виж app_errors, ноември 2026).
// Пита и трите сървъра наведнъж и връща първия добър отговор; приема само кратки заявки на Перá ([out:json]…);
// телефонът пази отговора за седмица (Cache-Control), така че едно и също място се пита веднъж.
const SERVERS = ((typeof Deno !== "undefined" && Deno.env.get("OSM_SERVERS")) ||
  "https://overpass-api.de/api/interpreter,https://overpass.kumi.systems/api/interpreter,https://overpass.private.coffee/api/interpreter").split(",");
const CORS = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Headers": "authorization, x-client-info, apikey, content-type",
  "Access-Control-Allow-Methods": "GET, OPTIONS",
};
const json = (o: unknown, status = 200, extra: Record<string, string> = {}) =>
  new Response(JSON.stringify(o), { status, headers: { ...CORS, "Content-Type": "application/json", ...extra } });

async function ask(u: string, q: string, ms: number) {
  const host = u.split("/")[2], t0 = Date.now(), ac = new AbortController(), tm = setTimeout(() => ac.abort(), ms);
  try {
    const r = await fetch(u, {
      method: "POST",
      body: "data=" + encodeURIComponent(q),
      headers: { "Content-Type": "application/x-www-form-urlencoded", "User-Agent": "Pera-bird-journal (https://elaypetrov.github.io/ptichi-dnevnik/)" },
      signal: ac.signal,
    });
    const body = await r.text();
    if (!r.ok) throw new Error(host + ": " + r.status);
    if (!body.trim().startsWith("{")) throw new Error(host + ": not JSON");
    return { body, via: host + " " + (Date.now() - t0) + "ms" };
  } catch (e) {
    throw new Error(e instanceof Error && e.message.startsWith(host) ? e.message : host + ": " + ((e as Error)?.name || e));
  } finally { clearTimeout(tm); }
}

// Зоните за птици по Натура 2000 (ЕАОС) — ако телефонът не може да ги поиска сам: ?eea=<заявката>, само към тази услуга.
const EEA = (typeof Deno !== "undefined" && Deno.env.get("EEA_URL")) ||
  "https://bio.discomap.eea.europa.eu/arcgis/rest/services/ProtectedSites/Natura2000Sites/MapServer/1/query";
async function eea(q: string): Promise<Response> {
  if (!q.startsWith("?where=") || q.length > 1500) return json({ error: "bad query" }, 400);
  const ac = new AbortController(), tm = setTimeout(() => ac.abort(), 20000);
  try {
    const r = await fetch(EEA + q, { headers: { "User-Agent": "Pera-bird-journal (https://elaypetrov.github.io/ptichi-dnevnik/)" }, signal: ac.signal });
    const body = await r.text();
    if (!r.ok || !body.trim().startsWith("{")) return json({ error: "eea", why: [String(r.status)] }, 502);
    return new Response(body, { headers: { ...CORS, "Content-Type": "application/json", "Cache-Control": "public, max-age=2592000" } });   // зоните се менят рядко — месец
  } catch (e) {
    return json({ error: "eea", why: [String((e as Error)?.name || e)] }, 502);
  } finally { clearTimeout(tm); }
}

// eBird (api.ebird.org/v2) с ключа от Supabase → Edge Functions → Secrets → EBIRD_KEY. Ключът не излиза от сървъра.
// Само няколко въпроса: имената на местата, наскорошните наблюдения на място или около точка, и кодовете на видовете.
const EBIRD = (typeof Deno !== "undefined" && Deno.env.get("EBIRD_URL")) || "https://api.ebird.org/v2/";
const EBIRD_OK = [
  /^ref\/hotspot\/info\/L\d+$/,
  /^data\/obs\/L\d+\/recent\?back=\d{1,2}$/,
  /^data\/obs\/geo\/recent(\/[a-z0-9]+)?\?lat=-?\d{1,2}(\.\d+)?&lng=-?\d{1,3}(\.\d+)?&dist=\d{1,2}&back=\d{1,2}$/,
];
let TAX: Map<string, string> | null = null;   // научно име → код на вида в eBird (докато сървърът е „топъл“)
async function ebird(path: string): Promise<Response> {
  const key = typeof Deno !== "undefined" ? Deno.env.get("EBIRD_KEY") : "";
  if (!key) return json({ error: "no key" }, 503);
  const H = { "X-eBirdApiToken": key, "User-Agent": "Pera-bird-journal (https://elaypetrov.github.io/ptichi-dnevnik/)" };
  try {
    if (path.startsWith("codes?")) {   // кодовете на eBird за няколко научни имена наведнъж
      const names = (new URLSearchParams(path.slice(6)).get("la") || "").split("|").filter(Boolean).slice(0, 500);
      if (!TAX) {
        const r = await fetch(EBIRD + "ref/taxonomy/ebird?fmt=json&cat=species", { headers: H });
        if (!r.ok) return json({ error: "ebird", why: [String(r.status)] }, 502);
        TAX = new Map((await r.json()).map((x: { sciName: string; speciesCode: string }) => [x.sciName.toLowerCase(), x.speciesCode]));
      }
      const out: Record<string, string> = {};
      for (const n of names) { const c = TAX.get(n.toLowerCase()); if (c) out[n] = c; }
      return json(out, 200, { "Cache-Control": "public, max-age=2592000" });
    }
    if (!EBIRD_OK.some((rx) => rx.test(path))) return json({ error: "bad query" }, 400);
    const r = await fetch(EBIRD + path, { headers: H });
    const body = await r.text();
    if (!r.ok) return json({ error: "ebird", why: [String(r.status)] }, 502);
    return new Response(body, { headers: { ...CORS, "Content-Type": "application/json", "Cache-Control": path.startsWith("ref/") ? "public, max-age=2592000" : "public, max-age=3600" } });
  } catch (e) {
    return json({ error: "ebird", why: [String((e as Error)?.name || e)] }, 502);
  }
}

export async function handle(req: Request): Promise<Response> {
  if (req.method === "OPTIONS") return new Response("ok", { headers: CORS });
  const eb = new URL(req.url).searchParams.get("ebird");
  if (eb !== null) return ebird(eb);
  const e = new URL(req.url).searchParams.get("eea");
  if (e !== null) return eea(e);
  const q = new URL(req.url).searchParams.get("data") || "";
  if (!q || q.length > 2000 || !q.startsWith("[out:json]")) return json({ error: "bad query" }, 400);   // само кратките заявки на Перá
  try {
    const r = await Promise.any(SERVERS.map((u) => ask(u, q, 25000)));   // първият добър отговор печели
    return new Response(r.body, { headers: { ...CORS, "Content-Type": "application/json", "Cache-Control": "public, max-age=604800", "X-Pera-Via": r.via } });
  } catch (e) {
    const why = e instanceof AggregateError ? e.errors.map((x) => String((x as Error).message || x)) : [String(e)];
    return json({ error: "overpass", why }, 502);
  }
}

if (typeof Deno !== "undefined" && Deno.serve) Deno.serve((req) => handle(req));

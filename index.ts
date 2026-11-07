// osm — помощник на Перá: пита Overpass (OpenStreetMap) от сървъра на Supabase, не от телефона.
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

export async function handle(req: Request): Promise<Response> {
  if (req.method === "OPTIONS") return new Response("ok", { headers: CORS });
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

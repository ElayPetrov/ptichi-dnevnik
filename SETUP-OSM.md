# Помощникът „osm“ (за 🏞 място в Карта → Изследвай)

На някои мобилни мрежи безплатните сървъри на Overpass (OpenStreetMap) не отговарят на телефона — в `app_errors`
се вижда „overpass-api.de: AbortError 10.0 с“ за всички сървъри. Помощникът пита Overpass от сървъра на Supabase.
Без него езерата и язовирите пак се намират (от Nominatim); с него — и резерватите, защитените места и парковете.

1. Supabase → **Edge Functions** → **Deploy a new function** → **Via Editor**, име точно `osm`.
2. В **Code** изтрий **целия** примерен код (`// Setup type definitions…`, `withSupabase`), постави целия
   `supabase/functions/osm/index.ts` и натисни **Deploy updates**. Първият ред трябва да е `// osm — помощник на Перá…`.
3. **Settings** на функцията → изключи „Enforce JWT verification“ → Save.
4. Проверка в браузъра (трябва да видиш `{"error":"bad query"}` — значи помощникът е там и отказва празна заявка):
   https://szyituwdlbwpqkfuklxq.supabase.co/functions/v1/osm

Перá сам го открива: щом помощникът е качен, използва него; ако го няма, пита сървърите направо (както досега).
В `app_errors` ще пише „osm (Supabase): …“ — какво е отговорил помощникът.

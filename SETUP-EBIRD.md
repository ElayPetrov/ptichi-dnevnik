# eBird в Перá (по желание, ~5 минути)

Какво дава: истинските имена на оранжевите места (вместо „eBird място L2205561“), „Наскоро тук“ — какво е видяно
на мястото за последните 30 дни, и в Цели — най-близкото скорошно наблюдение в eBird (до 50 км).
Без ключ Перá работи както досега.

1. Вземи безплатен ключ: https://ebird.org/api/keygen (влез с акаунта си в eBird / Cornell Lab).
2. Supabase → **Edge Functions** → **Secrets** → **Add new secret**: име `EBIRD_KEY`, стойност — ключът. Save.
   Ключът стои само там — Перá никога не го вижда и не може да изтече от телефона.
3. Обнови помощника `osm`: Edge Functions → osm → **Code** → изтрий всичко → постави новия
   `supabase/functions/osm/index.ts` → **Deploy updates**.
4. Проверка — отвори в браузъра (трябва да видиш името на мястото):
   https://szyituwdlbwpqkfuklxq.supabase.co/functions/v1/osm?ebird=ref%2Fhotspot%2Finfo%2FL2205561

Ако там пише `{"error":"no key"}` — ключът не е записан като `EBIRD_KEY` (стъпка 2).

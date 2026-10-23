# Recall measurements

## 2026-10-23 21:41 UTC -- recall measurement -- https://sail-event-dev.onrender.com -- fae046f (broken miss attribution: stageCounts was read from wrong nesting level)

| triple | criteria | gt | found | accepted | misses |
|--------|----------|----|-------|----------|--------|
| berlin_jazz | jazz in Berlin (Germany) next week | 5 | 1 | 1 | Emil Wahlgren "Autumn in Berli (not_fetched); STREAMLINE ORCHESTRA (not_fetched); ZIG ZAG HALL: Kurt Elling & Th (not_fetched); Jazzfest Berlin - Wendy Eisenb (not_fetched) |
| london_ai | AI meetups and tech events in London nex | 4 | 1 | 0 | The London AI Conference 2026 (not_fetched); The London Startup Party 2026 (not_fetched); Trustworthy AI: From Principle (not_fetched) |
| lisbon_fado | fado ao vivo em Lisboa este fim de seman | 4 | 1 | 0 | Fado in the Garden of the Hous (not_fetched); Fado Performance at Pateo in B (not_fetched); Ha Fado no Cais - Trio SUL (not_fetched) |
| valencia_regatta | regatas de vela en Valencia en noviembre | 3 | 0 | 0 | J80 Winter Series RCNV 2026-20 (not_fetched); Trofeo Levante 2026 (ILCA 4/6/ (not_fetched); Trofeo Varadero Valencia 2026 (not_fetched) |
| sevilla_kids | talleres infantiles y actividades para n | 4 | 1 | 0 | Black and White (magia infanti (not_fetched); El Ratoncito Perez (mision: di (not_fetched); Visita-taller familiar: Filmad (not_fetched) |
| paris_art | expositions d'art a Paris ce mois-ci | 4 | 0 | 0 | Mary Cassatt: Being Independen (not_fetched); Stan Douglas: Parallax (not_fetched); Gustave Fayet, Collector and C (not_fetched); Ibrahim Mahama: Harvest season (not_fetched) |
| tokyo_jazz | 東京 ジャズ 11月 | 3 | 0 | 0 | AZIZA featuring Dave Holland (not_fetched); Kenny Barron Trio (not_fetched); Benny Green Trio (not_fetched) |
| vienna_classical | classical concerts in Vienna, 1-15 Nov 2 | 4 | 0 | 0 | Otello (Verdi) - Kaufmann, Sal (not_fetched); La Fille du regiment (Donizett (not_fetched); Lise Davidsen and James Bailli (not_fetched); Madama Butterfly (Puccini) - J (not_fetched) |
| amsterdam_tech | tech meetups in Amsterdam this month | 3 | 0 | 0 | AI Tinkerers Amsterdam: Octobe (not_fetched); FastAPI Conf 2026 (not_fetched); SREday Amsterdam 2026 Q4 (not_fetched) |
| running_global | running | 4 | 0 | 0 | TCS New York City Marathon 202 (not_fetched); 48th Istanbul Marathon 2026 (not_fetched); 43rd Athens Authentic Marathon (not_fetched); Fukuoka Marathon 2026 (not_fetched) |

recall@run: **4/38 (10.5%)**
accepted-recall: **1/38 (2.6%)**

## 2026-10-23 22:34 UTC -- recall measurement -- https://sail-event-dev.onrender.com -- d7f840c

| triple | criteria | gt | found | accepted | misses |
|--------|----------|----|-------|----------|--------|
| berlin_jazz | jazz in Berlin (Germany) next week | 5 | 0 | 0 | Emil Wahlgren "Autumn in Berli (judged_out); Jazzfest Berlin - Elin Forkeli (likely_no_event_extracted); STREAMLINE ORCHESTRA (likely_no_event_extracted); ZIG ZAG HALL: Kurt Elling & Th (likely_no_event_extracted); Jazzfest Berlin - Wendy Eisenb (likely_no_event_extracted) |
| london_ai | AI meetups and tech events in London nex | 4 | 3 | 1 | The Infrastructure Decisions T (likely_no_event_extracted) |
| lisbon_fado | fado ao vivo em Lisboa este fim de seman | 4 | 2 | 2 | Fado Performance at Pateo in B (judged_out); Ha Fado no Cais - Trio SUL (likely_no_event_extracted) |
| valencia_regatta | regatas de vela en Valencia en noviembre | 3 | 0 | 0 | J80 Winter Series RCNV 2026-20 (likely_no_event_extracted); Trofeo Levante 2026 (ILCA 4/6/ (likely_no_event_extracted); Trofeo Varadero Valencia 2026  (judged_out) |
| sevilla_kids | talleres infantiles y actividades para n | 4 | 1 | 0 | Black and White (magia infanti (likely_no_event_extracted); El Ratoncito Perez (mision: di (likely_no_event_extracted); Visita-taller familiar: Filmad (likely_no_event_extracted) |
| paris_art | expositions d'art a Paris ce mois-ci | 4 | 0 | 0 | Mary Cassatt: Being Independen (likely_no_event_extracted); Stan Douglas: Parallax (likely_no_event_extracted); Gustave Fayet, Collector and C (likely_no_event_extracted); Ibrahim Mahama: Harvest season (likely_no_event_extracted) |
| tokyo_jazz | 東京 ジャズ 11月 | 3 | 0 | 0 | AZIZA featuring Dave Holland,  (likely_no_event_extracted); Kenny Barron Trio (likely_no_event_extracted); Benny Green Trio (likely_no_event_extracted) |
| vienna_classical | classical concerts in Vienna, 1-15 Nov 2 | 4 | 2 | 2 | Otello (Verdi) - Kaufmann, Sal (likely_no_event_extracted); Madama Butterfly (Puccini) - J (likely_no_event_extracted) |
| amsterdam_tech | tech meetups in Amsterdam this month | 3 | 1 | 1 | FastAPI Conf 2026 (judged_out); SREday Amsterdam 2026 Q4 (judged_out) |
| running_global | running | 4 | 0 | 0 | TCS New York City Marathon 202 (likely_no_event_extracted); 48th Istanbul Marathon 2026 (likely_no_event_extracted); 43rd Athens Authentic Marathon (likely_no_event_extracted); Fukuoka Marathon 2026 (likely_no_event_extracted) |

recall@run: **9/38 (23.7%)**  
accepted-recall: **6/38 (15.8%)**

The first run (4/38) and the corrected run (9/38) are separate searches on
the same day (2026-10-23, 21:41 and 22:34 UTC) with different Tavily draws.
The found/accepted counts differ because Tavily returned different result
pages; the miss attribution differs because the first run had a bug reading
stageCounts from the wrong nesting level (every miss read "not_fetched").

## 2026-10-23 23:45 UTC -- recall measurement -- https://sail-event-dev.onrender.com -- e39816b

| triple | criteria | gt | found | accepted | misses |
|--------|----------|----|-------|----------|--------|
| berlin_jazz | jazz in Berlin (Germany) next week | 5 | 0 | 0 | Emil Wahlgren "Autumn in Berli (likely_no_event_extracted); Jazzfest Berlin - Elin Forkeli (likely_no_event_extracted); STREAMLINE ORCHESTRA (likely_no_event_extracted); ZIG ZAG HALL: Kurt Elling & Th (likely_no_event_extracted); Jazzfest Berlin - Wendy Eisenb (likely_no_event_extracted) |
| london_ai | AI meetups and tech events in London nex | 4 | 3 | 0 | The Infrastructure Decisions T (likely_no_event_extracted) |
| lisbon_fado | fado ao vivo em Lisboa este fim de seman | 4 | 2 | 2 | Fado Performance at Pateo in B (likely_no_event_extracted); Ha Fado no Cais - Trio SUL (likely_no_event_extracted) |
| valencia_regatta | regatas de vela en Valencia en noviembre | 3 | 0 | 0 | J80 Winter Series RCNV 2026-20 (likely_no_event_extracted); Trofeo Levante 2026 (ILCA 4/6/ (likely_no_event_extracted); Trofeo Varadero Valencia 2026  (likely_no_event_extracted) |
| sevilla_kids | talleres infantiles y actividades para n | 4 | 1 | 0 | Black and White (magia infanti (likely_no_event_extracted); El Ratoncito Perez (mision: di (likely_no_event_extracted); Visita-taller familiar: Filmad (likely_no_event_extracted) |
| paris_art | expositions d'art a Paris ce mois-ci | 4 | 0 | 0 | Mary Cassatt: Being Independen (likely_no_event_extracted); Stan Douglas: Parallax (likely_no_event_extracted); Gustave Fayet, Collector and C (likely_no_event_extracted); Ibrahim Mahama: Harvest season (likely_no_event_extracted) |
| tokyo_jazz | 東京 ジャズ 11月 | 3 | 0 | 0 | AZIZA featuring Dave Holland,  (likely_no_event_extracted); Kenny Barron Trio (likely_no_event_extracted); Benny Green Trio (likely_no_event_extracted) |
| vienna_classical | classical concerts in Vienna, 1-15 Nov 2 | 4 | 1 | 0 | Otello (Verdi) - Kaufmann, Sal (likely_no_event_extracted); La Fille du regiment (Donizett (likely_no_event_extracted); Madama Butterfly (Puccini) - J (likely_no_event_extracted) |
| amsterdam_tech | tech meetups in Amsterdam this month | 3 | 0 | 0 | AI Tinkerers Amsterdam: Octobe (likely_no_event_extracted); FastAPI Conf 2026 (likely_no_event_extracted); SREday Amsterdam 2026 Q4 (likely_no_event_extracted) |
| running_global | running | 4 | 0 | 0 | TCS New York City Marathon 202 (likely_no_event_extracted); 48th Istanbul Marathon 2026 (likely_no_event_extracted); 43rd Athens Authentic Marathon (likely_no_event_extracted); Fukuoka Marathon 2026 (likely_no_event_extracted) |

recall@run: **7/38 (18.4%)**  
accepted-recall: **2/38 (5.3%)**

Page classification 29/38 = 76% on current main (deepseek-v4.1-flash),
target 90%, red until issue 124 lands.

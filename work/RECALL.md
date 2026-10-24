# Recall measurements

Superseded by `work/RUN-LOG.md` (unified runner phase 4, issue #135).

## Before 2026-10-25

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

Page classification 33/40 = 82.5% on current main (deepseek-v4.1-flash),
target 90%, red until issue 124 lands.

lisbon_fado 0/4 diagnostic (2026-10-24): 14 events extracted, but GT titles
are in English while extraction returns Portuguese; dates shift by 1-2 days
across recurring shows. The events exist in the results but the title/date
matching is too strict for cross-language GT entries. This is a matching
limitation, not an extraction failure.

## 2026-10-24 19:52 UTC -- recall measurement -- http://localhost:8032 -- ab21641

| triple | criteria | gt | found | accepted | misses |
|--------|----------|----|-------|----------|--------|
| valencia_regatta | regatas de vela en Valencia en noviembre | 3 | 0 | 0 | J80 Winter Series RCNV 2026-20 (possibly_filtered_past); Trofeo Levante 2026 (ILCA 4/6/ (possibly_filtered_past); Trofeo Varadero Valencia 2026  (possibly_filtered_past) |

recall@run: **0/3 (0.0%)**  
accepted-recall: **0/3 (0.0%)**

## 2026-10-24 19:55 UTC -- recall measurement -- http://localhost:8032 -- ab21641

| triple | criteria | gt | found | accepted | misses |
|--------|----------|----|-------|----------|--------|
| sevilla_kids | talleres infantiles y actividades para n | 4 | 1 | 0 | Black and White (magia infanti (possibly_filtered_past); El Ratoncito Perez (mision: di (possibly_filtered_past); Visita-taller familiar: Filmad (possibly_filtered_past) |

recall@run: **1/4 (25.0%)**  
accepted-recall: **0/4 (0.0%)**

## 2026-10-24 19:57 UTC -- recall measurement -- http://localhost:8032 -- ab21641

| triple | criteria | gt | found | accepted | misses |
|--------|----------|----|-------|----------|--------|
| paris_art | expositions d'art a Paris ce mois-ci | 4 | 0 | 0 | Mary Cassatt: Being Independen (likely_no_event_extracted); Stan Douglas: Parallax (likely_no_event_extracted); Gustave Fayet, Collector and C (likely_no_event_extracted); Ibrahim Mahama: Harvest season (likely_no_event_extracted) |

recall@run: **0/4 (0.0%)**  
accepted-recall: **0/4 (0.0%)**

## 2026-10-24 20:00 UTC -- recall measurement -- http://localhost:8031 -- ab21641

| triple | criteria | gt | found | accepted | misses |
|--------|----------|----|-------|----------|--------|
| berlin_jazz | jazz in Berlin (Germany) next week | 5 | 0 | 0 | Emil Wahlgren "Autumn in Berli (possibly_filtered_past); Jazzfest Berlin - Elin Forkeli (possibly_filtered_past); STREAMLINE ORCHESTRA (possibly_filtered_past); ZIG ZAG HALL: Kurt Elling & Th (possibly_filtered_past); Jazzfest Berlin - Wendy Eisenb (possibly_filtered_past) |
| london_ai | AI meetups and tech events in London nex | 4 | 4 | 0 | -- |
| lisbon_fado | fado ao vivo em Lisboa este fim de seman | 4 | 1 | 0 | Fado in the Garden of the Hous (possibly_filtered_past); Fado Performance at Pateo in B (possibly_filtered_past); Ha Fado no Cais - Trio SUL (possibly_filtered_past) |
| valencia_regatta | regatas de vela en Valencia en noviembre | 3 | 0 | 0 | J80 Winter Series RCNV 2026-20 (possibly_filtered_past); Trofeo Levante 2026 (ILCA 4/6/ (possibly_filtered_past); Trofeo Varadero Valencia 2026  (possibly_filtered_past) |
| sevilla_kids | talleres infantiles y actividades para n | 4 | 2 | 0 | Black and White (magia infanti (possibly_filtered_past); El Ratoncito Perez (mision: di (possibly_filtered_past) |
| paris_art | expositions d'art a Paris ce mois-ci | 4 | 2 | 2 | Mary Cassatt: Being Independen (possibly_filtered_past); Stan Douglas: Parallax (possibly_filtered_past) |
| tokyo_jazz | 東京 ジャズ 11月 | 3 | 0 | 0 | AZIZA featuring Dave Holland,  (possibly_filtered_past); Kenny Barron Trio (possibly_filtered_past); Benny Green Trio (possibly_filtered_past) |
| vienna_classical | classical concerts in Vienna, 1-15 Nov 2 | 4 | 1 | 1 | Otello (Verdi) - Kaufmann, Sal (possibly_filtered_past); La Fille du regiment (Donizett (possibly_filtered_past); Madama Butterfly (Puccini) - J (possibly_filtered_past) |
| amsterdam_tech | tech meetups in Amsterdam this month | 3 | 0 | 0 | AI Tinkerers Amsterdam: Octobe (possibly_filtered_past); FastAPI Conf 2026 (possibly_filtered_past); SREday Amsterdam 2026 Q4 (possibly_filtered_past) |
| running_global | running | 4 | 2 | 2 | 43rd Athens Authentic Marathon (likely_no_event_extracted); Fukuoka Marathon 2026 (likely_no_event_extracted) |

recall@run: **12/38 (31.6%)**  
accepted-recall: **5/38 (13.2%)**

## 2026-10-24 20:01 UTC -- recall measurement -- http://localhost:8032 -- ab21641

| triple | criteria | gt | found | accepted | misses |
|--------|----------|----|-------|----------|--------|
| tokyo_jazz | 東京 ジャズ 11月 | 3 | 0 | 0 | AZIZA featuring Dave Holland,  (possibly_filtered_past); Kenny Barron Trio (possibly_filtered_past); Benny Green Trio (possibly_filtered_past) |

recall@run: **0/3 (0.0%)**  
accepted-recall: **0/3 (0.0%)**

## 2026-10-24 20:03 UTC -- recall measurement -- http://localhost:8032 -- ab21641

| triple | criteria | gt | found | accepted | misses |
|--------|----------|----|-------|----------|--------|
| vienna_classical | classical concerts in Vienna, 1-15 Nov 2 | 4 | 0 | 0 | Otello (Verdi) - Kaufmann, Sal (possibly_filtered_past); La Fille du regiment (Donizett (possibly_filtered_past); Lise Davidsen and James Bailli (possibly_filtered_past); Madama Butterfly (Puccini) - J (possibly_filtered_past) |

recall@run: **0/4 (0.0%)**  
accepted-recall: **0/4 (0.0%)**

## 2026-10-24 20:04 UTC -- recall measurement -- http://localhost:8032 -- ab21641

| triple | criteria | gt | found | accepted | misses |
|--------|----------|----|-------|----------|--------|
| berlin_jazz | jazz in Berlin (Germany) next week | 5 | 0 | 0 | Emil Wahlgren "Autumn in Berli (not_in_search_results); Jazzfest Berlin - Elin Forkeli (not_in_search_results); STREAMLINE ORCHESTRA (not_in_search_results); ZIG ZAG HALL: Kurt Elling & Th (not_in_search_results); Jazzfest Berlin - Wendy Eisenb (not_in_search_results) |
| london_ai | AI meetups and tech events in London nex | 4 | 1 | 0 | The London AI Conference 2026 (possibly_filtered_past); The London Startup Party 2026 (possibly_filtered_past); Trustworthy AI: From Principle (possibly_filtered_past) |
| lisbon_fado | fado ao vivo em Lisboa este fim de seman | 4 | 1 | 0 | Fado in the Garden of the Hous (likely_no_event_extracted); Fado Performance at Pateo in B (likely_no_event_extracted); Ha Fado no Cais - Trio SUL (likely_no_event_extracted) |
| valencia_regatta | regatas de vela en Valencia en noviembre | 3 | 0 | 0 | J80 Winter Series RCNV 2026-20 (possibly_filtered_past); Trofeo Levante 2026 (ILCA 4/6/ (possibly_filtered_past); Trofeo Varadero Valencia 2026  (possibly_filtered_past) |
| sevilla_kids | talleres infantiles y actividades para n | 4 | 1 | 0 | Black and White (magia infanti (possibly_filtered_past); El Ratoncito Perez (mision: di (possibly_filtered_past); Visita-taller familiar: Filmad (possibly_filtered_past) |
| paris_art | expositions d'art a Paris ce mois-ci | 4 | 0 | 0 | Mary Cassatt: Being Independen (likely_no_event_extracted); Stan Douglas: Parallax (likely_no_event_extracted); Gustave Fayet, Collector and C (likely_no_event_extracted); Ibrahim Mahama: Harvest season (likely_no_event_extracted) |
| tokyo_jazz | 東京 ジャズ 11月 | 3 | 0 | 0 | AZIZA featuring Dave Holland,  (possibly_filtered_past); Kenny Barron Trio (possibly_filtered_past); Benny Green Trio (possibly_filtered_past) |
| vienna_classical | classical concerts in Vienna, 1-15 Nov 2 | 4 | 0 | 0 | Otello (Verdi) - Kaufmann, Sal (not_in_search_results); La Fille du regiment (Donizett (not_in_search_results); Lise Davidsen and James Bailli (not_in_search_results); Madama Butterfly (Puccini) - J (not_in_search_results) |
| amsterdam_tech | tech meetups in Amsterdam this month | 3 | 0 | 0 | AI Tinkerers Amsterdam: Octobe (possibly_filtered_past); FastAPI Conf 2026 (possibly_filtered_past); SREday Amsterdam 2026 Q4 (possibly_filtered_past) |
| running_global | running | 4 | 0 | 0 | TCS New York City Marathon 202 (likely_no_event_extracted); 48th Istanbul Marathon 2026 (likely_no_event_extracted); 43rd Athens Authentic Marathon (likely_no_event_extracted); Fukuoka Marathon 2026 (likely_no_event_extracted) |

recall@run: **3/38 (7.9%)**  
accepted-recall: **0/38 (0.0%)**

## 2026-10-24 20:06 UTC -- recall measurement -- http://localhost:8032 -- ab21641

| triple | criteria | gt | found | accepted | misses |
|--------|----------|----|-------|----------|--------|
| amsterdam_tech | tech meetups in Amsterdam this month | 3 | 0 | 0 | AI Tinkerers Amsterdam: Octobe (possibly_filtered_past); FastAPI Conf 2026 (possibly_filtered_past); SREday Amsterdam 2026 Q4 (possibly_filtered_past) |

recall@run: **0/3 (0.0%)**  
accepted-recall: **0/3 (0.0%)**

## 2026-10-24 20:07 UTC -- recall measurement -- http://localhost:8032 -- ab21641

| triple | criteria | gt | found | accepted | misses |
|--------|----------|----|-------|----------|--------|
| running_global | running | 4 | 0 | 0 | TCS New York City Marathon 202 (likely_no_event_extracted); 48th Istanbul Marathon 2026 (likely_no_event_extracted); 43rd Athens Authentic Marathon (likely_no_event_extracted); Fukuoka Marathon 2026 (likely_no_event_extracted) |

recall@run: **0/4 (0.0%)**  
accepted-recall: **0/4 (0.0%)**

## 2026-10-24 20:09 UTC -- recall measurement -- http://localhost:8031 -- ab21641

| triple | criteria | gt | found | accepted | misses |
|--------|----------|----|-------|----------|--------|
| berlin_jazz | jazz in Berlin (Germany) next week | 5 | 0 | 0 | Emil Wahlgren "Autumn in Berli (possibly_filtered_past); Jazzfest Berlin - Elin Forkeli (possibly_filtered_past); STREAMLINE ORCHESTRA (possibly_filtered_past); ZIG ZAG HALL: Kurt Elling & Th (possibly_filtered_past); Jazzfest Berlin - Wendy Eisenb (possibly_filtered_past) |

recall@run: **0/5 (0.0%)**  
accepted-recall: **0/5 (0.0%)**

## 2026-10-24 20:12 UTC -- recall measurement -- http://localhost:8031 -- ab21641

| triple | criteria | gt | found | accepted | misses |
|--------|----------|----|-------|----------|--------|
| london_ai | AI meetups and tech events in London nex | 4 | 2 | 0 | The London Startup Party 2026 (possibly_filtered_past); Trustworthy AI: From Principle (possibly_filtered_past) |

recall@run: **2/4 (50.0%)**  
accepted-recall: **0/4 (0.0%)**

## 2026-10-24 20:13 UTC -- recall measurement -- http://localhost:8031 -- ab21641

| triple | criteria | gt | found | accepted | misses |
|--------|----------|----|-------|----------|--------|
| lisbon_fado | fado ao vivo em Lisboa este fim de seman | 4 | 1 | 0 | Fado in the Garden of the Hous (likely_no_event_extracted); Fado Performance at Pateo in B (likely_no_event_extracted); Ha Fado no Cais - Trio SUL (likely_no_event_extracted) |

recall@run: **1/4 (25.0%)**  
accepted-recall: **0/4 (0.0%)**

## 2026-10-24 20:15 UTC -- recall measurement -- http://localhost:8031 -- ab21641

| triple | criteria | gt | found | accepted | misses |
|--------|----------|----|-------|----------|--------|
| valencia_regatta | regatas de vela en Valencia en noviembre | 3 | 1 | 0 | Trofeo Levante 2026 (ILCA 4/6/ (possibly_filtered_past); Trofeo Varadero Valencia 2026  (possibly_filtered_past) |

recall@run: **1/3 (33.3%)**  
accepted-recall: **0/3 (0.0%)**

## 2026-10-24 20:17 UTC -- recall measurement -- http://localhost:8031 -- ab21641

| triple | criteria | gt | found | accepted | misses |
|--------|----------|----|-------|----------|--------|
| sevilla_kids | talleres infantiles y actividades para n | 4 | 4 | 0 | -- |

recall@run: **4/4 (100.0%)**  
accepted-recall: **0/4 (0.0%)**

## 2026-10-24 20:19 UTC -- recall measurement -- http://localhost:8031 -- ab21641

| triple | criteria | gt | found | accepted | misses |
|--------|----------|----|-------|----------|--------|
| paris_art | expositions d'art a Paris ce mois-ci | 4 | 2 | 1 | Mary Cassatt: Being Independen (possibly_filtered_past); Stan Douglas: Parallax (possibly_filtered_past) |

recall@run: **2/4 (50.0%)**  
accepted-recall: **1/4 (25.0%)**

## 2026-10-24 20:22 UTC -- recall measurement -- http://localhost:8031 -- ab21641

| triple | criteria | gt | found | accepted | misses |
|--------|----------|----|-------|----------|--------|
| tokyo_jazz | 東京 ジャズ 11月 | 3 | 0 | 0 | AZIZA featuring Dave Holland,  (possibly_filtered_past); Kenny Barron Trio (possibly_filtered_past); Benny Green Trio (possibly_filtered_past) |

recall@run: **0/3 (0.0%)**  
accepted-recall: **0/3 (0.0%)**

## 2026-10-24 20:24 UTC -- recall measurement -- http://localhost:8031 -- ab21641

| triple | criteria | gt | found | accepted | misses |
|--------|----------|----|-------|----------|--------|
| vienna_classical | classical concerts in Vienna, 1-15 Nov 2 | 4 | 1 | 1 | Otello (Verdi) - Kaufmann, Sal (possibly_filtered_past); La Fille du regiment (Donizett (possibly_filtered_past); Madama Butterfly (Puccini) - J (possibly_filtered_past) |

recall@run: **1/4 (25.0%)**  
accepted-recall: **1/4 (25.0%)**

## 2026-10-24 20:25 UTC -- recall measurement -- http://localhost:8031 -- ab21641

| triple | criteria | gt | found | accepted | misses |
|--------|----------|----|-------|----------|--------|
| amsterdam_tech | tech meetups in Amsterdam this month | 3 | 0 | 0 | AI Tinkerers Amsterdam: Octobe (possibly_filtered_past); FastAPI Conf 2026 (possibly_filtered_past); SREday Amsterdam 2026 Q4 (possibly_filtered_past) |

recall@run: **0/3 (0.0%)**  
accepted-recall: **0/3 (0.0%)**

## 2026-10-24 20:26 UTC -- recall measurement -- http://localhost:8031 -- ab21641

| triple | criteria | gt | found | accepted | misses |
|--------|----------|----|-------|----------|--------|
| running_global | running | 4 | 2 | 2 | 43rd Athens Authentic Marathon (likely_no_event_extracted); Fukuoka Marathon 2026 (likely_no_event_extracted) |

recall@run: **2/4 (50.0%)**  
accepted-recall: **2/4 (50.0%)**

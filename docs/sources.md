# Источники данных

В проекте два независимых пайплайна сбора данных.

## Модуль 1. Live-поиск (backend/src/sources/multi_search.py)

Используется в POST /api/search. Функция принимает два готовых запроса: query_ru и query_en.

| # | Источник | trust_level | Язык |
|---|---|---|---|
| 1 | DuckDuckGo | 5 | ru/en |
| 2 | Startpage | 5 | ru/en |
| 3 | Mojeek | 5 | ru/en |
| 4 | Marginalia | 4 | en |
| 5 | Habr | 6 | ru |
| 6 | arXiv | 9 | en |
| 7 | OpenAlex | 9 | en |
| 8 | Crossref | 9 | en |
| 9 | PubMed | 10 | en |
| 10 | Europe PMC | 9 | en |
| 11 | DOAJ | 9 | en |
| 12 | Semantic Scholar | 8 | en |
| 13 | Zenodo | 8 | en |
| 14 | HAL | 8 | fr |
| 15 | bioRxiv | 8 | en |
| 16 | Hacker News | 5 | en |
| 17 | GitHub | 6 | en |
| 18 | Stack Exchange | 6 | en |
| 19 | Reddit | 4 | en |
| 20 | Dev.to | 5 | en |
| 21 | Spaceflight News | 6 | en |

Итого: 21 источник.

## Модуль 2. RSS/Atom-реестр (config/sources_registry.json)

Используется отдельным пайплайном для наполнения таблицы documents.

Итого в реестре: 160 записей, из них 117 активны.

| Категория | Всего | Активно |
|---|---|---|
| media | 78 | 56 |
| science | 23 | 21 |
| gov | 20 | 10 |
| funding | 18 | 10 |
| patent | 11 | 11 |
| social | 8 | 7 |
| code | 1 | 1 |
| aggregator | 1 | 1 |

## Правила trust_level (модуль 1, шкала 1–10)

| Уровень | Категория |
|---|---|
| 10 | Рецензируемые научные издания |
| 8–9 | Препринты |
| 6–7 | Медиа и техплощадки |
| 4–5 | Общие веб-источники |
| 2–3 | Блоги |
| 1 | Анонимные источники |

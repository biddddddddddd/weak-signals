# Пайплайн данных

## ETL-пайплайн

1. Сбор из 21 источника — параллельные запросы.
2. Дедупликация по doc_id.
3. Фильтр по длине — < 30 символов отбрасывается.
4. Классификатор weak / negative / junk.
5. Retrieval по weak_signals.
6. GigaChat-скоринг.
7. Группировка по технологии.

## Источники

Два независимых потока:

1. Live-поиск (multi_search.py): 21 источник в момент запроса.
2. RSS/Atom-реестр (config/sources_registry.json): 160 записей (117 активных).

## Итоговый датасет

- weak: 1288
- negative: 1584
- junk: 1004
- Всего: 3876

Разбиение: train 2712, validation 582, test 582.

## Скрипты (backend/src/scripts/)

Запуск через docker compose exec backend python -m src.scripts.<script_name>.

Сбор сырых данных:
- collect_raw_weak.py — arXiv / OpenAlex / Crossref
- collect_raw_weak_github.py — GitHub
- collect_raw_weak_producthunt.py — Product Hunt
- collect_raw_negative.py — negative-примеры
- collect_dataset.py — общий сбор
- generate_raw_junk.py — генерация junk

Расширение датасета:
- add_negative_batch.py
- add_junk_batch.py
- add_short_weak.py
- add_short_negative_junk.py
- add_irrelevant_negative.py
- add_targeted_fixes.py
- augment_all.py

Подготовка данных и обучение:
- load_seeds.py
- build_embeddings.py
- build_raw_embeddings.py
- deduplicate_raw.py
- report_raw_stats.py
- build_final_dataset.py
- train_classifier.py

Отладка:
- debug_llm.py, debug_retrieval.py, debug_search.py, debug_search2.py
- big_test.py, demo_test.py, demo_test_v2.py

## Таблицы БД

См. docs/architecture.md.
